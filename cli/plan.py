"""
CLI command handler for weekly content planning.
Generates Now-Next-Later posting schedules with optimal time windows.
"""

import click
import json
import os
from datetime import datetime
from typing import Optional
import jsonschema

from core.scheduler import Scheduler
from core.schemas import PLAN_SCHEMA


@click.command()
@click.option('--accept', is_flag=True, help='Auto-accept the generated plan without review')
@click.option('--suggest', is_flag=True, help='Generate suggestions based on past performance')
@click.option('--week-start', type=str, help='Start date for the week (YYYY-MM-DD format)')
@click.option('--output', '-o', type=str, help='Output file path (defaults to data/schedules/plan_YYYY-MM-DD.json)')
@click.pass_context
def plan(ctx, accept: bool, suggest: bool, week_start: Optional[str], output: Optional[str]):
    """
    Generate a Now-Next-Later weekly content plan with optimal posting windows.
    
    Creates a structured weekly plan that balances immediate content needs (Now),
    upcoming posts (Next), and experimental content (Later) based on engagement
    best practices and historical performance data.
    
    Examples:
        li plan --accept                    # Generate and auto-save plan
        li plan --suggest                   # Include performance-based suggestions
        li plan --week-start 2025-08-25     # Plan for specific week
    """
    try:
        # Initialize scheduler
        scheduler = Scheduler()
        
        # Parse week start date if provided
        week_start_date = None
        if week_start:
            try:
                week_start_date = datetime.strptime(week_start, '%Y-%m-%d')
            except ValueError:
                click.echo(f"❌ Invalid date format: {week_start}. Use YYYY-MM-DD format.")
                ctx.exit(1)
        
        # Generate the weekly plan
        click.echo("🔄 Generating weekly content plan...")
        plan_data = scheduler.generate_weekly_plan(week_start_date)
        
        # Add suggestions if requested
        if suggest:
            click.echo("📊 Analyzing past performance for suggestions...")
            suggestions = _generate_suggestions(scheduler)
            plan_data['suggestions'] = suggestions
        
        # Validate against schema
        try:
            jsonschema.validate(plan_data, PLAN_SCHEMA)
        except jsonschema.ValidationError as e:
            click.echo(f"❌ Generated plan failed validation: {e.message}")
            ctx.exit(1)
        
        # Determine output path
        if not output:
            output = f"data/schedules/plan_{plan_data['week_of']}.json"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output), exist_ok=True)
        
        # Display plan summary
        _display_plan_summary(plan_data, suggest)
        
        # Save or prompt for confirmation
        if accept or click.confirm("💾 Save this plan?"):
            with open(output, 'w') as f:
                json.dump(plan_data, f, indent=2)
            
            click.echo(f"✅ Plan saved to {output}")
            
            # Display next steps
            _display_next_steps(plan_data)
        else:
            click.echo("❌ Plan not saved. Use --accept to auto-save future plans.")
    
    except Exception as e:
        click.echo(f"❌ Error generating plan: {str(e)}")
        ctx.exit(1)


def _generate_suggestions(scheduler: Scheduler) -> dict:
    """
    Generate performance-based suggestions for the content plan.
    
    Args:
        scheduler: Scheduler instance with access to metrics
        
    Returns:
        Dictionary containing suggestions based on past performance
    """
    suggestions = {
        "timing": [],
        "topics": [],
        "experiments": []
    }
    
    # Analyze optimal windows
    top_windows = scheduler.optimal_windows[:3]
    if top_windows:
        best_window = top_windows[0]
        suggestions["timing"].append(
            f"Your best performing time is {best_window.day} at {best_window.hour}:00 "
            f"(avg engagement: {best_window.engagement_score:.2%})"
        )
        
        if len(top_windows) > 1:
            suggestions["timing"].append(
                f"Alternative high-performing slots: {top_windows[1].day} {top_windows[1].hour}:00, "
                f"{top_windows[2].day} {top_windows[2].hour}:00"
            )
    
    # Suggest experiments
    experiment_spread = scheduler.config.get('experiment_spread_hours', 2)
    suggestions["experiments"].append(
        f"Test posting ±{experiment_spread} hours from your optimal windows to discover new high-engagement slots"
    )
    
    suggestions["experiments"].append(
        "Try weekend posting experiments to test audience availability outside work hours"
    )
    
    # Topic suggestions based on config
    topics = scheduler.config.get('topics', [])
    if topics:
        suggestions["topics"].append(
            f"Focus on your top topics: {', '.join(topics[:3])} for higher engagement"
        )
    
    return suggestions


def _display_plan_summary(plan_data: dict, include_suggestions: bool = False):
    """
    Display a formatted summary of the generated plan.
    
    Args:
        plan_data: The generated plan data
        include_suggestions: Whether to show performance suggestions
    """
    click.echo(f"\n📅 Weekly Plan for week of {plan_data['week_of']}")
    click.echo("=" * 50)
    
    # Display NOW items
    click.echo("\n🔥 NOW (High Priority)")
    for item in plan_data.get('now', []):
        window = item.get('target_window', {})
        click.echo(f"  • {item['topic']}")
        click.echo(f"    📍 Target: {window.get('day', 'TBD')} at {window.get('hour', 'TBD')}:00")
    
    # Display NEXT items
    click.echo("\n⏭️  NEXT (Medium Priority)")
    for item in plan_data.get('next', []):
        window = item.get('target_window', {})
        click.echo(f"  • {item['topic']}")
        click.echo(f"    📍 Target: {window.get('day', 'TBD')} at {window.get('hour', 'TBD')}:00")
    
    # Display LATER items
    click.echo("\n🔮 LATER (Experimental)")
    for item in plan_data.get('later', []):
        click.echo(f"  • {item['topic']}")
        if 'experiment' in item:
            click.echo(f"    🧪 {item['experiment']}")
    
    # Display recommended windows
    if 'recommended_windows' in plan_data:
        click.echo("\n⭐ Top Performing Windows")
        for i, window in enumerate(plan_data['recommended_windows'][:3], 1):
            score = window.get('engagement_score', 0)
            count = window.get('post_count', 0)
            click.echo(f"  {i}. {window['day']} {window['hour']}:00 "
                      f"(score: {score:.2%}, posts: {count})")
    
    # Display suggestions if available
    if include_suggestions and 'suggestions' in plan_data:
        suggestions = plan_data['suggestions']
        
        if suggestions.get('timing'):
            click.echo("\n💡 Timing Suggestions")
            for suggestion in suggestions['timing']:
                click.echo(f"  • {suggestion}")
        
        if suggestions.get('experiments'):
            click.echo("\n🧪 Experiment Ideas")
            for suggestion in suggestions['experiments'][:2]:
                click.echo(f"  • {suggestion}")


def _display_next_steps(plan_data: dict):
    """
    Display recommended next steps after saving the plan.
    
    Args:
        plan_data: The saved plan data
    """
    click.echo("\n🚀 Next Steps:")
    click.echo("  1. Start drafting your NOW posts:")
    
    for i, item in enumerate(plan_data.get('now', [])[:2], 1):
        topic = item['topic']
        click.echo(f"     li draft \"{topic}\" --format story")
    
    click.echo("\n  2. Queue your drafts:")
    click.echo("     li queue draft.json")
    
    click.echo("\n  3. Track performance:")
    click.echo("     li metrics --since 7d --import metrics.csv")
    
    click.echo("\n  4. Update plan next week:")
    click.echo("     li plan --suggest --accept")


if __name__ == '__main__':
    plan()