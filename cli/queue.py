"""
CLI command handler for queueing posts and managing schedules.
Assigns posts to optimal time windows and manages posting queue.
"""

import click
import json
import os
from datetime import datetime
from typing import Optional
import jsonschema

from core.scheduler import Scheduler
from core.schemas import SCHEDULE_SCHEMA


@click.command()
@click.argument('draft_file', type=click.Path(exists=True))
@click.option('--schedule', type=str, help='Specific schedule file to add to (defaults to current week)')
@click.option('--time', type=str, help='Override posting time (format: "Day HH", e.g., "Tue 10")')
@click.option('--preview', is_flag=True, help='Preview the scheduling without saving')
@click.pass_context
def queue(ctx, draft_file: str, schedule: Optional[str], time: Optional[str], preview: bool):
    """
    Queue a draft post for publishing at an optimal time.
    
    Assigns the post to the next available optimal time window
    and adds it to the weekly schedule.
    
    Examples:
        li queue draft.json                    # Queue for next optimal slot
        li queue draft.json --time "Thu 14"    # Queue for specific time
        li queue draft.json --preview          # Preview scheduling
    """
    try:
        # Load the draft post
        with open(draft_file, 'r') as f:
            post_data = json.load(f)
        
        click.echo(f"🔄 Queuing post: {post_data.get('title', 'Untitled')}")
        
        # Initialize scheduler
        scheduler = Scheduler()
        
        # Determine posting time
        if time:
            posting_window = _parse_time_override(time)
            if not posting_window:
                click.echo(f"❌ Invalid time format: {time}. Use format 'Day HH' (e.g., 'Tue 10')")
                ctx.exit(1)
        else:
            # Use the post's suggested window or get next available
            suggested_window = post_data.get('target_window')
            if suggested_window:
                posting_window = suggested_window
            else:
                optimal_window = scheduler.get_next_available_slot()
                posting_window = {
                    "day": optimal_window.day,
                    "hour": optimal_window.hour
                }
        
        # Load or create schedule
        schedule_data = _load_or_create_schedule(schedule, scheduler)
        
        # Create queue entry
        queue_entry = {
            "post_id": post_data['id'],
            "day": posting_window['day'],
            "hour": posting_window['hour'],
            "status": "planned"
        }
        
        # Check for conflicts
        if _has_time_conflict(schedule_data, queue_entry):
            click.echo(f"⚠️  Time slot {posting_window['day']} {posting_window['hour']}:00 is already taken")
            if not click.confirm("Continue anyway?"):
                ctx.exit(0)
        
        # Add to schedule
        schedule_data['slots'].append(queue_entry)
        
        # Validate schedule
        try:
            jsonschema.validate(schedule_data, SCHEDULE_SCHEMA)
        except jsonschema.ValidationError as e:
            click.echo(f"❌ Schedule validation failed: {e.message}")
            ctx.exit(1)
        
        # Display preview
        _display_queue_preview(post_data, queue_entry, schedule_data)
        
        if preview:
            click.echo("\n👀 Preview mode - schedule not updated")
            return
        
        # Save schedule
        schedule_file = _get_schedule_file_path(schedule_data['week_of'])
        
        if click.confirm(f"💾 Add to schedule ({schedule_file})?"):
            os.makedirs(os.path.dirname(schedule_file), exist_ok=True)
            with open(schedule_file, 'w') as f:
                json.dump(schedule_data, f, indent=2)
            
            click.echo(f"✅ Post queued for {posting_window['day']} at {posting_window['hour']}:00")
            
            # Display next steps
            _display_queue_next_steps(schedule_file, schedule_data)
        else:
            click.echo("❌ Post not queued.")
    
    except Exception as e:
        click.echo(f"❌ Error queuing post: {str(e)}")
        ctx.exit(1)


def _parse_time_override(time_str: str) -> Optional[dict]:
    """Parse time override string into day/hour format."""
    try:
        parts = time_str.strip().split()
        if len(parts) != 2:
            return None
        
        day, hour_str = parts
        hour = int(hour_str)
        
        # Validate day
        valid_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        if day not in valid_days:
            return None
        
        # Validate hour
        if not 0 <= hour <= 23:
            return None
        
        return {"day": day, "hour": hour}
    
    except (ValueError, IndexError):
        return None


def _load_or_create_schedule(schedule_file: Optional[str], scheduler: Scheduler) -> dict:
    """Load existing schedule or create new one for current week."""
    if schedule_file and os.path.exists(schedule_file):
        with open(schedule_file, 'r') as f:
            return json.load(f)
    
    # Create new schedule for current week
    today = datetime.now()
    days_ahead = 0 - today.weekday()  # Monday is 0
    if days_ahead <= 0:
        days_ahead += 7
    week_start = today + days_ahead * datetime.timedelta(days=1)
    
    return {
        "week_of": week_start.strftime('%Y-%m-%d'),
        "slots": []
    }


def _has_time_conflict(schedule_data: dict, new_entry: dict) -> bool:
    """Check if the new entry conflicts with existing slots."""
    for slot in schedule_data.get('slots', []):
        if (slot.get('day') == new_entry['day'] and 
            slot.get('hour') == new_entry['hour']):
            return True
    return False


def _display_queue_preview(post_data: dict, queue_entry: dict, schedule_data: dict):
    """Display preview of the queueing operation."""
    click.echo(f"\n📅 Queue Preview")
    click.echo("=" * 30)
    
    click.echo(f"Post: {post_data.get('title', 'Untitled')}")
    click.echo(f"Scheduled: {queue_entry['day']} at {queue_entry['hour']}:00")
    click.echo(f"Week of: {schedule_data['week_of']}")
    
    # Show other posts in the schedule
    other_slots = [s for s in schedule_data.get('slots', []) if s != queue_entry]
    if other_slots:
        click.echo(f"\nOther posts this week:")
        for slot in sorted(other_slots, key=lambda s: (s.get('day', ''), s.get('hour', 0))):
            click.echo(f"  • {slot.get('day')} {slot.get('hour')}:00 - {slot.get('post_id', 'Unknown')}")


def _get_schedule_file_path(week_of: str) -> str:
    """Get the file path for a schedule."""
    return f"data/schedules/schedule_{week_of}.json"


def _display_queue_next_steps(schedule_file: str, schedule_data: dict):
    """Display next steps after queuing."""
    click.echo("\n🚀 Next Steps:")
    click.echo(f"  1. View full schedule:")
    click.echo(f"     cat {schedule_file}")
    
    click.echo(f"\n  2. Post when ready:")
    click.echo(f"     li post --schedule {schedule_file}")
    
    # Count posts in schedule
    total_posts = len(schedule_data.get('slots', []))
    click.echo(f"\n  📊 Weekly schedule: {total_posts} posts planned")


if __name__ == '__main__':
    queue()