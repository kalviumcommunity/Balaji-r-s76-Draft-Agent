"""
Core scheduler module for LinkedIn AI agent.
Handles optimal posting time windows, scheduling logic, and engagement-based recommendations.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random
from dataclasses import dataclass

@dataclass
class TimeWindow:
    """Represents a posting time window with engagement metrics."""
    day: str
    hour: int
    engagement_score: float = 0.0
    post_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "day": self.day,
            "hour": self.hour,
            "engagement_score": self.engagement_score,
            "post_count": self.post_count
        }

class Scheduler:
    """
    Manages posting schedules and optimal time window recommendations.
    
    Combines best-practice heuristics with historical performance data
    to suggest optimal posting times and generate weekly schedules.
    """
    
    # Best practice posting windows (weekday work hours bias)
    DEFAULT_WINDOWS = [
        TimeWindow("Tue", 10, 0.8),  # Tuesday mid-morning
        TimeWindow("Thu", 11, 0.75), # Thursday late morning
        TimeWindow("Wed", 14, 0.7),  # Wednesday lunch
        TimeWindow("Tue", 15, 0.65), # Tuesday afternoon
        TimeWindow("Fri", 12, 0.6),  # Friday lunch
        TimeWindow("Mon", 16, 0.55), # Monday late afternoon
        TimeWindow("Wed", 9, 0.5),   # Wednesday early morning
    ]
    
    def __init__(self, config_path: str = "config.json", data_dir: str = "data"):
        """
        Initialize scheduler with configuration and data directory.
        
        Args:
            config_path: Path to configuration file
            data_dir: Directory containing metrics and schedule data
        """
        self.config_path = config_path
        self.data_dir = data_dir
        self.metrics_dir = os.path.join(data_dir, "metrics")
        self.schedules_dir = os.path.join(data_dir, "schedules")
        
        # Ensure directories exist
        os.makedirs(self.metrics_dir, exist_ok=True)
        os.makedirs(self.schedules_dir, exist_ok=True)
        
        self.config = self._load_config()
        self.optimal_windows = self._calculate_optimal_windows()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "windows": [{"day": "Tue", "hour": 10}, {"day": "Thu", "hour": 11}],
                "experiment_spread_hours": 2,
                "topics": ["product", "engineering"]
            }
    
    def _calculate_optimal_windows(self) -> List[TimeWindow]:
        """
        Calculate optimal posting windows based on historical metrics.
        
        Combines default best practices with actual performance data
        from past posts to recommend the best times to post.
        
        Returns:
            List of TimeWindow objects ranked by engagement potential
        """
        # Start with default windows
        windows = self.DEFAULT_WINDOWS.copy()
        
        # Load historical metrics to refine windows
        metrics_data = self._load_historical_metrics()
        
        if metrics_data:
            # Calculate engagement rates by time window
            window_performance = {}
            for metric in metrics_data:
                if 'published_at' in metric:
                    dt = datetime.fromisoformat(metric['published_at'].replace('Z', '+00:00'))
                    day = dt.strftime('%a')
                    hour = dt.hour
                    
                    # Calculate engagement rate
                    total_interactions = (
                        metric.get('reactions', 0) + 
                        metric.get('comments', 0) + 
                        metric.get('shares', 0)
                    )
                    impressions = metric.get('impressions', 1)
                    engagement_rate = total_interactions / impressions if impressions > 0 else 0
                    
                    key = f"{day}-{hour}"
                    if key not in window_performance:
                        window_performance[key] = {"rates": [], "count": 0}
                    
                    window_performance[key]["rates"].append(engagement_rate)
                    window_performance[key]["count"] += 1
            
            # Update windows with actual performance data
            for window in windows:
                key = f"{window.day}-{window.hour}"
                if key in window_performance:
                    rates = window_performance[key]["rates"]
                    window.engagement_score = sum(rates) / len(rates)
                    window.post_count = window_performance[key]["count"]
            
            # Sort by engagement score
            windows.sort(key=lambda w: w.engagement_score, reverse=True)
        
        return windows[:7]  # Return top 7 windows
    
    def _load_historical_metrics(self) -> List[Dict[str, Any]]:
        """Load all historical metrics from the metrics directory."""
        all_metrics = []
        
        if not os.path.exists(self.metrics_dir):
            return all_metrics
        
        for filename in os.listdir(self.metrics_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(self.metrics_dir, filename), 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            all_metrics.extend(data)
                        else:
                            all_metrics.append(data)
                except (json.JSONDecodeError, FileNotFoundError):
                    continue
        
        return all_metrics
    
    def generate_weekly_plan(self, week_start: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Generate a Now-Next-Later weekly content plan with optimal time windows.
        
        Args:
            week_start: Start date for the week (defaults to next Monday)
            
        Returns:
            Dictionary containing the weekly plan with Now/Next/Later structure
        """
        if not week_start:
            today = datetime.now()
            days_ahead = 0 - today.weekday()  # Monday is 0
            if days_ahead <= 0:  # Target next Monday
                days_ahead += 7
            week_start = today + timedelta(days=days_ahead)
        
        week_of = week_start.strftime('%Y-%m-%d')
        topics = self.config.get('topics', ['product', 'engineering', 'founder'])
        
        # Generate Now (immediate priority) items
        now_items = []
        for i, topic in enumerate(topics[:2]):  # Top 2 topics for immediate posting
            window = self.optimal_windows[i % len(self.optimal_windows)]
            now_items.append({
                "topic": f"Latest insights on {topic}",
                "priority": "high",
                "target_window": {
                    "day": window.day,
                    "hour": window.hour
                }
            })
        
        # Generate Next (upcoming) items
        next_items = []
        for i, topic in enumerate(topics[2:4] if len(topics) > 2 else topics[:2]):
            window = self.optimal_windows[(i + 2) % len(self.optimal_windows)]
            next_items.append({
                "topic": f"Deep dive into {topic} best practices",
                "priority": "medium",
                "target_window": {
                    "day": window.day,
                    "hour": window.hour
                }
            })
        
        # Generate Later (experimental/future) items
        later_items = []
        for topic in topics:
            experiment_spread = self.config.get('experiment_spread_hours', 2)
            later_items.append({
                "topic": f"Personal story about {topic} journey",
                "priority": "low",
                "experiment": f"Test ±{experiment_spread}h from optimal window"
            })
        
        return {
            "week_of": week_of,
            "now": now_items,
            "next": next_items,
            "later": later_items,
            "recommended_windows": [w.to_dict() for w in self.optimal_windows[:5]],
            "generated_at": datetime.now().isoformat()
        }
    
    def suggest_posting_time(self, preferred_day: Optional[str] = None) -> TimeWindow:
        """
        Suggest the best posting time based on optimal windows.
        
        Args:
            preferred_day: Preferred day of week (e.g., 'Tue')
            
        Returns:
            TimeWindow object with recommended posting time
        """
        if preferred_day:
            day_windows = [w for w in self.optimal_windows if w.day == preferred_day]
            if day_windows:
                return day_windows[0]
        
        # Return the top-ranked window
        return self.optimal_windows[0] if self.optimal_windows else TimeWindow("Tue", 10)
    
    def create_experimental_window(self, base_window: TimeWindow, spread_hours: int = 2) -> TimeWindow:
        """
        Create an experimental posting window based on a base window.
        
        Args:
            base_window: The base time window to experiment around
            spread_hours: Hours to vary from base (±spread_hours)
            
        Returns:
            New TimeWindow with experimental timing
        """
        hour_offset = random.randint(-spread_hours, spread_hours)
        new_hour = max(6, min(22, base_window.hour + hour_offset))  # Keep within 6 AM - 10 PM
        
        return TimeWindow(
            day=base_window.day,
            hour=new_hour,
            engagement_score=0.0  # Unknown performance for experimental window
        )
    
    def get_next_available_slot(self, exclude_scheduled: bool = True) -> TimeWindow:
        """
        Get the next available posting slot from optimal windows.
        
        Args:
            exclude_scheduled: Whether to exclude already scheduled slots
            
        Returns:
            Next available TimeWindow
        """
        # For now, return the best available window
        # In a full implementation, this would check against existing schedules
        return self.optimal_windows[0] if self.optimal_windows else TimeWindow("Tue", 10)
    
    def validate_schedule(self, schedule_data: Dict[str, Any]) -> bool:
        """
        Validate a schedule against business rules and constraints.
        
        Args:
            schedule_data: Schedule data to validate
            
        Returns:
            True if schedule is valid, False otherwise
        """
        if not isinstance(schedule_data, dict):
            return False
        
        required_fields = ['week_of', 'slots']
        if not all(field in schedule_data for field in required_fields):
            return False
        
        slots = schedule_data.get('slots', [])
        if not isinstance(slots, list):
            return False
        
        # Check for conflicts (same day/hour)
        seen_times = set()
        for slot in slots:
            if not isinstance(slot, dict):
                return False
            
            day = slot.get('day')
            hour = slot.get('hour')
            
            if not day or not isinstance(hour, int):
                return False
            
            time_key = f"{day}-{hour}"
            if time_key in seen_times:
                return False  # Time conflict
            
            seen_times.add(time_key)
        
        return True