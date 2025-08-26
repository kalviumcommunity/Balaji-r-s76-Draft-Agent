"""
CLI command handler for metrics ingestion and analytics.
Imports post performance data and updates recommendations.
"""

import click
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import jsonschema

from core.schemas import METRICS_SCHEMA


@click.command()
@click.option('--since', type=str, help='Time period to analyze (e.g., "7d", "30d", "2025-08-01")')
@click.option('--import', 'import_file', type=click.Path(exists=True), help='CSV file to import metrics from')
@click.option('--export', type=str, help='Export metrics to file')
@click.option('--summary', is_flag=True, help='Show performance summary')
@click.pass_context
def metrics(ctx, since: Optional[str], import_file: Optional[str], export: Optional[str], summary: bool):
    """
    Ingest and analyze post performance metrics.
    
    Imports metrics from CSV files, analyzes performance trends,
    and updates recommendations for future content.
    
    Examples:
        li metrics --since 7d --summary           # Show last 7 days summary
        li metrics --import metrics.csv           # Import from CSV
        li metrics --export metrics_report.json  # Export analysis
    """
    try:
        click.echo("📊 Processing metrics...")
        
        # Import metrics if file provided
        if import_file:
            imported_count = _import_metrics_from_csv(import_file)
            click.echo(f"✅ Imported {imported_count} metrics records")
        
        # Load and analyze metrics
        metrics_data = _load_metrics_data()
        
        if not metrics_data:
            click.echo("⚠️  No metrics data found. Import some data first with --import")
            return
        
        # Filter by time period if specified
        if since:
            metrics_data = _filter_metrics_by_time(metrics_data, since)
            click.echo(f"📅 Filtered to {len(metrics_data)} records from {since}")
        
        # Generate analysis
        analysis = _analyze_metrics(metrics_data)
        
        # Display summary if requested
        if summary:
            _display_metrics_summary(analysis, metrics_data)
        
        # Export if requested
        if export:
            _export_analysis(analysis, export)
            click.echo(f"📄 Analysis exported to {export}")
        
        # Update recommendations
        _update_recommendations(analysis)
        click.echo("🔄 Updated posting recommendations based on performance data")
    
    except Exception as e:
        click.echo(f"❌ Error processing metrics: {str(e)}")
        ctx.exit(1)


def _import_metrics_from_csv(csv_file: str) -> int:
    """Import metrics from CSV file and save as JSON."""
    try:
        df = pd.read_csv(csv_file)
        
        # Expected CSV columns: post_id, impressions, reactions, comments, shares, clicks, published_at
        required_columns = ['post_id', 'impressions', 'reactions', 'comments', 'shares', 'published_at']
        
        # Check for required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Convert to metrics format
        metrics_list = []
        for _, row in df.iterrows():
            # Calculate engagement rate
            total_interactions = row['reactions'] + row['comments'] + row.get('shares', 0)
            impressions = row['impressions'] if row['impressions'] > 0 else 1
            engagement_rate = total_interactions / impressions
            
            metric = {
                "post_id": str(row['post_id']),
                "impressions": int(row['impressions']),
                "reactions": int(row['reactions']),
                "comments": int(row['comments']),
                "shares": int(row.get('shares', 0)),
                "clicks": int(row.get('clicks', 0)),
                "published_at": str(row['published_at']),
                "engagement_rate": float(engagement_rate),
                "imported_at": datetime.now().isoformat()
            }
            
            # Validate against schema
            jsonschema.validate(metric, METRICS_SCHEMA)
            metrics_list.append(metric)
        
        # Save to metrics directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"data/metrics/imported_metrics_{timestamp}.json"
        
        os.makedirs("data/metrics", exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(metrics_list, f, indent=2)
        
        return len(metrics_list)
    
    except Exception as e:
        raise Exception(f"Failed to import CSV: {str(e)}")


def _load_metrics_data() -> list:
    """Load all metrics data from the metrics directory."""
    all_metrics = []
    metrics_dir = "data/metrics"
    
    if not os.path.exists(metrics_dir):
        return all_metrics
    
    for filename in os.listdir(metrics_dir):
        if filename.endswith('.json'):
            try:
                with open(os.path.join(metrics_dir, filename), 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_metrics.extend(data)
                    else:
                        all_metrics.append(data)
            except (json.JSONDecodeError, FileNotFoundError):
                continue
    
    return all_metrics


def _filter_metrics_by_time(metrics_data: list, since: str) -> list:
    """Filter metrics by time period."""
    if since.endswith('d'):
        # Days ago
        days = int(since[:-1])
        cutoff_date = datetime.now() - timedelta(days=days)
    else:
        # Specific date
        try:
            cutoff_date = datetime.strptime(since, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"Invalid date format: {since}. Use YYYY-MM-DD or Xd format")
    
    filtered_metrics = []
    for metric in metrics_data:
        try:
            pub_date = datetime.fromisoformat(metric['published_at'].replace('Z', '+00:00'))
            if pub_date >= cutoff_date:
                filtered_metrics.append(metric)
        except (ValueError, KeyError):
            continue
    
    return filtered_metrics


def _analyze_metrics(metrics_data: list) -> dict:
    """Analyze metrics data and generate insights."""
    if not metrics_data:
        return {}
    
    # Basic statistics
    total_posts = len(metrics_data)
    total_impressions = sum(m.get('impressions', 0) for m in metrics_data)
    total_reactions = sum(m.get('reactions', 0) for m in metrics_data)
    total_comments = sum(m.get('comments', 0) for m in metrics_data)
    total_shares = sum(m.get('shares', 0) for m in metrics_data)
    
    avg_impressions = total_impressions / total_posts if total_posts > 0 else 0
    avg_engagement_rate = sum(m.get('engagement_rate', 0) for m in metrics_data) / total_posts if total_posts > 0 else 0
    
    # Time analysis
    time_performance = {}
    for metric in metrics_data:
        try:
            pub_date = datetime.fromisoformat(metric['published_at'].replace('Z', '+00:00'))
            day = pub_date.strftime('%a')
            hour = pub_date.hour
            
            key = f"{day}-{hour:02d}"
            if key not in time_performance:
                time_performance[key] = {'posts': 0, 'total_engagement': 0}
            
            time_performance[key]['posts'] += 1
            time_performance[key]['total_engagement'] += metric.get('engagement_rate', 0)
        except (ValueError, KeyError):
            continue
    
    # Calculate average engagement by time
    for key in time_performance:
        posts = time_performance[key]['posts']
        if posts > 0:
            time_performance[key]['avg_engagement'] = time_performance[key]['total_engagement'] / posts
    
    # Top performing times
    top_times = sorted(
        [(k, v['avg_engagement']) for k, v in time_performance.items() if v['posts'] >= 2],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    # Best performing posts
    best_posts = sorted(
        metrics_data,
        key=lambda m: m.get('engagement_rate', 0),
        reverse=True
    )[:5]
    
    return {
        'summary': {
            'total_posts': total_posts,
            'total_impressions': total_impressions,
            'total_reactions': total_reactions,
            'total_comments': total_comments,
            'total_shares': total_shares,
            'avg_impressions': avg_impressions,
            'avg_engagement_rate': avg_engagement_rate
        },
        'time_performance': time_performance,
        'top_times': top_times,
        'best_posts': best_posts,
        'analysis_date': datetime.now().isoformat()
    }


def _display_metrics_summary(analysis: dict, metrics_data: list):
    """Display a formatted metrics summary."""
    summary = analysis.get('summary', {})
    
    click.echo(f"\n📊 Metrics Summary")
    click.echo("=" * 40)
    
    click.echo(f"Total Posts: {summary.get('total_posts', 0)}")
    click.echo(f"Total Impressions: {summary.get('total_impressions', 0):,}")
    click.echo(f"Total Engagement: {summary.get('total_reactions', 0) + summary.get('total_comments', 0) + summary.get('total_shares', 0):,}")
    click.echo(f"Avg Impressions: {summary.get('avg_impressions', 0):.0f}")
    click.echo(f"Avg Engagement Rate: {summary.get('avg_engagement_rate', 0):.2%}")
    
    # Top performing times
    top_times = analysis.get('top_times', [])
    if top_times:
        click.echo(f"\n⭐ Best Performing Times:")
        for time_key, engagement in top_times[:3]:
            day, hour = time_key.split('-')
            click.echo(f"  {day} {hour}:00 - {engagement:.2%} avg engagement")
    
    # Best posts
    best_posts = analysis.get('best_posts', [])
    if best_posts:
        click.echo(f"\n🏆 Top Performing Posts:")
        for post in best_posts[:3]:
            post_id = post.get('post_id', 'Unknown')[:12]
            engagement = post.get('engagement_rate', 0)
            impressions = post.get('impressions', 0)
            click.echo(f"  {post_id} - {engagement:.2%} ({impressions:,} impressions)")


def _export_analysis(analysis: dict, output_file: str):
    """Export analysis to JSON file."""
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)


def _update_recommendations(analysis: dict):
    """Update posting recommendations based on analysis."""
    # This would update the scheduler's optimal windows
    # For now, we'll save the analysis for the scheduler to use
    recommendations_file = "data/recommendations.json"
    
    recommendations = {
        'optimal_times': analysis.get('top_times', []),
        'avg_engagement_rate': analysis.get('summary', {}).get('avg_engagement_rate', 0),
        'last_updated': datetime.now().isoformat()
    }
    
    with open(recommendations_file, 'w') as f:
        json.dump(recommendations, f, indent=2)


if __name__ == '__main__':
    metrics()