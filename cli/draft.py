"""
CLI command handler for drafting LinkedIn posts.
Uses RAG and prompting to generate grounded content.
"""

import click
import json
import os
from typing import Optional
import jsonschema

from core.prompting import ContentGenerator
from core.schemas import POST_SCHEMA


@click.command()
@click.argument('topic', type=str)
@click.option('--format', 'format_type', type=click.Choice(['short', 'story', 'carousel']), 
              default='story', help='Post format type')
@click.option('--output', '-o', type=str, help='Output file path (defaults to data/posts/draft_TIMESTAMP.json)')
@click.option('--preview', is_flag=True, help='Preview the post without saving')
@click.pass_context
def draft(ctx, topic: str, format_type: str, output: Optional[str], preview: bool):
    """
    Generate a grounded LinkedIn post draft using RAG and prompting.
    
    Creates structured posts with engaging hooks, valuable content,
    and clear calls-to-action based on past performance data.
    
    Examples:
        li draft "3 lessons from building our MVP" --format story
        li draft "Product management tips" --format carousel --preview
        li draft "Quick engineering insight" --format short
    """
    try:
        # Initialize content generator
        generator = ContentGenerator()
        
        click.echo(f"🔄 Generating {format_type} post about: {topic}")
        
        # Generate the post
        post_data = generator.generate_post(topic, format_type)
        
        # Validate against schema
        try:
            jsonschema.validate(post_data, POST_SCHEMA)
        except jsonschema.ValidationError as e:
            click.echo(f"❌ Generated post failed validation: {e.message}")
            ctx.exit(1)
        
        # Display preview
        _display_post_preview(post_data)
        
        # Save or exit if preview only
        if preview:
            click.echo("\n👀 Preview mode - post not saved")
            return
        
        # Determine output path
        if not output:
            timestamp = post_data['generated_at'].replace(':', '-').split('.')[0]
            safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()[:30]
            output = f"data/posts/draft_{safe_topic.replace(' ', '_')}_{timestamp}.json"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output), exist_ok=True)
        
        # Save the draft
        if click.confirm("💾 Save this draft?"):
            with open(output, 'w') as f:
                json.dump(post_data, f, indent=2)
            
            click.echo(f"✅ Draft saved to {output}")
            
            # Display next steps
            _display_next_steps(output, post_data)
        else:
            click.echo("❌ Draft not saved.")
    
    except Exception as e:
        click.echo(f"❌ Error generating draft: {str(e)}")
        ctx.exit(1)


def _display_post_preview(post_data: dict):
    """Display a formatted preview of the generated post."""
    click.echo(f"\n📝 {post_data['title']}")
    click.echo("=" * 50)
    
    # Display the main content
    click.echo(f"\n{post_data['body']}")
    
    # Display metadata
    click.echo(f"\n📊 Post Details:")
    click.echo(f"  • Format: {post_data.get('format', 'N/A')}")
    click.echo(f"  • Tags: {', '.join(post_data.get('tags', []))}")
    
    target_window = post_data.get('target_window', {})
    click.echo(f"  • Suggested time: {target_window.get('day', 'TBD')} at {target_window.get('hour', 'TBD')}:00")
    
    # Display source insights
    source_snippets = post_data.get('source_snippets', [])
    if source_snippets:
        click.echo(f"  • Based on {len(source_snippets)} similar posts")
    
    insights = post_data.get('insights', {})
    if insights:
        similar_count = insights.get('similar_posts_count', 0)
        avg_similarity = insights.get('avg_similarity', 0)
        click.echo(f"  • Content analysis: {similar_count} related posts (avg similarity: {avg_similarity:.1%})")
        
        recommendations = insights.get('recommendations', [])
        if recommendations:
            click.echo(f"\n💡 Content Insights:")
            for rec in recommendations[:2]:
                click.echo(f"  • {rec}")


def _display_next_steps(output_path: str, post_data: dict):
    """Display recommended next steps after saving the draft."""
    click.echo("\n🚀 Next Steps:")
    click.echo(f"  1. Review and edit the draft:")
    click.echo(f"     cat {output_path}")
    
    click.echo(f"\n  2. Queue for posting:")
    click.echo(f"     li queue {output_path}")
    
    click.echo(f"\n  3. Post immediately (manual mode):")
    click.echo(f"     li post --now {output_path}")
    
    # Show target window info
    target_window = post_data.get('target_window', {})
    if target_window:
        click.echo(f"\n  💡 Optimal time: {target_window.get('day')} at {target_window.get('hour')}:00")


if __name__ == '__main__':
    draft()