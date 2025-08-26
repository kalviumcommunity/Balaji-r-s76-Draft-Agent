#!/usr/bin/env python3
"""
Demo version of LinkedIn AI Agent - runs without external dependencies.
Demonstrates the core functionality with simplified implementations.
"""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main CLI entry point for demo."""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1]
    
    if command == "init":
        init_workspace()
    elif command == "plan":
        generate_plan()
    elif command == "draft":
        if len(sys.argv) < 3:
            print("❌ Error: Please provide a topic for the draft")
            print("Usage: python3 demo.py draft \"your topic here\"")
            return
        topic = sys.argv[2]
        generate_draft(topic)
    elif command == "queue":
        if len(sys.argv) < 3:
            print("❌ Error: Please provide a draft file to queue")
            return
        draft_file = sys.argv[2]
        queue_post(draft_file)
    elif command == "metrics":
        analyze_metrics()
    elif command == "post":
        if len(sys.argv) < 3:
            print("❌ Error: Please provide a draft file to post")
            return
        draft_file = sys.argv[2]
        post_content(draft_file)
    else:
        show_help()

def show_help():
    """Display help information."""
    print("""
LinkedIn AI Agent - Demo Version

Usage: python3 demo.py <command> [options]

Commands:
  init                    Initialize workspace and sample data
  plan                    Generate weekly Now-Next-Later content plan
  draft "topic"           Generate a LinkedIn post draft
  queue <draft.json>      Queue a draft for optimal posting time
  metrics                 Analyze performance metrics
  post <draft.json>       Output ready-to-post content

Examples:
  python3 demo.py init
  python3 demo.py plan
  python3 demo.py draft "product management lessons"
  python3 demo.py queue draft_example.json
  python3 demo.py post draft_example.json
  python3 demo.py metrics

📖 Full Documentation: See README.md for complete feature details
    """)

def init_workspace():
    """Initialize workspace with directories and sample data."""
    print("🚀 Initializing LinkedIn AI Agent workspace...")
    
    # Create directory structure
    directories = [
        "data/posts",
        "data/metrics", 
        "data/schedules",
        "docs",
        "tests"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Create sample data files
    create_sample_files()
    
    print("\n🎉 Workspace initialized successfully!")
    print("\n🚀 Next steps:")
    print("  1. python3 demo.py plan                           # Generate weekly plan")
    print("  2. python3 demo.py draft \"your topic\"             # Create a post")
    print("  3. python3 demo.py metrics                        # View analytics")

def create_sample_files():
    """Create sample data files for demonstration."""
    
    # Sample metrics
    sample_metrics = [
        {
            "post_id": "sample_1",
            "impressions": 1500,
            "reactions": 120,
            "comments": 25,
            "shares": 8,
            "clicks": 45,
            "published_at": "2025-08-10T10:00:00Z",
            "engagement_rate": 0.102
        },
        {
            "post_id": "sample_2", 
            "impressions": 2200,
            "reactions": 180,
            "comments": 40,
            "shares": 15,
            "clicks": 75,
            "published_at": "2025-08-12T14:00:00Z",
            "engagement_rate": 0.107
        }
    ]
    
    with open("data/metrics/sample_metrics.json", 'w') as f:
        json.dump(sample_metrics, f, indent=2)
    print(f"✅ Created sample metrics: data/metrics/sample_metrics.json")
    
    # Sample posts for RAG
    sample_posts = [
        {
            "id": "sample_1",
            "title": "3 lessons from building our MVP",
            "body": "After 6 months of development, here's what I learned:\n\n1. Start with the problem, not the solution\n2. Talk to users early and often\n3. Build the minimum that validates your hypothesis\n\nWhat would you add to this list?",
            "tags": ["product", "startup", "mvp"],
            "published_at": "2025-08-10T10:00:00Z"
        },
        {
            "id": "sample_2",
            "title": "The engineering mindset that changed everything",
            "body": "One shift in thinking transformed how our team approaches problems:\n\n🔍 From \"How do we build this?\"\n✅ To \"Should we build this?\"\n\nThis simple question saves us weeks of unnecessary work.\n\nWhat questions help you prioritize better?",
            "tags": ["engineering", "mindset", "productivity"],
            "published_at": "2025-08-12T14:00:00Z"
        }
    ]
    
    with open("data/posts/sample_posts.json", 'w') as f:
        json.dump(sample_posts, f, indent=2)
    print(f"✅ Created sample posts: data/posts/sample_posts.json")

def generate_plan():
    """Generate a Now-Next-Later weekly content plan."""
    print("🔄 Generating weekly content plan...")
    
    # Get next Monday
    today = datetime.now()
    days_ahead = 0 - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    week_start = today + timedelta(days=days_ahead)
    week_of = week_start.strftime('%Y-%m-%d')
    
    # Load config
    config = load_config()
    topics = config.get('topics', ['product', 'engineering', 'founder'])
    
    # Generate plan
    plan_data = {
        "week_of": week_of,
        "now": [
            {
                "topic": f"Latest insights on {topics[0]}",
                "priority": "high",
                "target_window": {"day": "Tue", "hour": 10}
            },
            {
                "topic": f"Key lessons from {topics[1]}",
                "priority": "high", 
                "target_window": {"day": "Thu", "hour": 11}
            }
        ],
        "next": [
            {
                "topic": f"Deep dive into {topics[1]} best practices",
                "priority": "medium",
                "target_window": {"day": "Wed", "hour": 14}
            }
        ],
        "later": [
            {
                "topic": f"Personal story about {topic} journey",
                "priority": "low",
                "experiment": "Test ±2h from optimal window"
            } for topic in topics
        ],
        "recommended_windows": [
            {"day": "Tue", "hour": 10, "engagement_score": 0.08, "post_count": 5},
            {"day": "Thu", "hour": 11, "engagement_score": 0.075, "post_count": 3},
            {"day": "Wed", "hour": 14, "engagement_score": 0.07, "post_count": 4}
        ],
        "generated_at": datetime.now().isoformat()
    }
    
    # Save plan
    output_file = f"data/schedules/plan_{week_of}.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(plan_data, f, indent=2)
    
    # Display plan
    display_plan_summary(plan_data)
    
    print(f"\n✅ Plan saved to {output_file}")
    print("\n🚀 Next Steps:")
    print(f"  1. python3 demo.py draft \"{plan_data['now'][0]['topic']}\"")
    print(f"  2. python3 demo.py queue draft_example.json")

def display_plan_summary(plan_data: dict):
    """Display a formatted summary of the plan."""
    print(f"\n📅 Weekly Plan for week of {plan_data['week_of']}")
    print("=" * 50)
    
    # Display NOW items
    print("\n🔥 NOW (High Priority)")
    for item in plan_data.get('now', []):
        window = item.get('target_window', {})
        print(f"  • {item['topic']}")
        print(f"    📍 Target: {window.get('day', 'TBD')} at {window.get('hour', 'TBD')}:00")
    
    # Display NEXT items
    print("\n⏭️  NEXT (Medium Priority)")
    for item in plan_data.get('next', []):
        window = item.get('target_window', {})
        print(f"  • {item['topic']}")
        print(f"    📍 Target: {window.get('day', 'TBD')} at {window.get('hour', 'TBD')}:00")
    
    # Display LATER items
    print("\n🔮 LATER (Experimental)")
    for item in plan_data.get('later', []):
        print(f"  • {item['topic']}")
        if 'experiment' in item:
            print(f"    🧪 {item['experiment']}")
    
    # Display recommended windows
    print("\n⭐ Top Performing Windows")
    for i, window in enumerate(plan_data.get('recommended_windows', [])[:3], 1):
        score = window.get('engagement_score', 0)
        count = window.get('post_count', 0)
        print(f"  {i}. {window['day']} {window['hour']}:00 "
              f"(score: {score:.1%}, posts: {count})")

def generate_draft(topic: str):
    """Generate a LinkedIn post draft."""
    print(f"🔄 Generating story post about: {topic}")
    
    # Simplified content generation
    import uuid
    import random
    
    # Generate hook
    hooks = [
        f"Here's what I learned about {topic}:",
        f"After months of working on {topic}, here's what surprised me:",
        f"The {topic} lesson I wish I knew earlier:"
    ]
    hook = random.choice(hooks)
    
    # Generate story content
    story = f"We were struggling with {topic} on our latest project. Despite having all the right tools and processes, something wasn't clicking.\n\nThen our team lead suggested a different approach. Instead of focusing on the technical details, we stepped back and asked: 'What outcome are we really trying to achieve?'\n\nThat simple shift in perspective changed everything."
    
    # Generate lesson
    lesson = f"The lesson: {topic} isn't just about execution—it's about clarity of purpose.\n\nWhen you're clear on the 'why,' the 'how' becomes much easier to figure out."
    
    # Generate CTA
    ctas = [
        f"What's your biggest {topic} challenge?",
        f"What would you add to this {topic} list?",
        f"How do you approach {topic} in your work?"
    ]
    cta = random.choice(ctas)
    
    content = f"{hook}\n\n{story}\n\n{lesson}\n\n{cta}"
    
    # Create post structure
    post_data = {
        "id": f"post_{uuid.uuid4().hex[:8]}",
        "title": f"Story: {topic.title()}",
        "body": content,
        "tags": extract_tags(topic),
        "assets": [],
        "cta": cta,
        "target_window": {"day": "Tue", "hour": 10},
        "source_snippets": [],
        "format": "story",
        "generated_at": datetime.now().isoformat(),
        "insights": {
            "similar_posts_count": 2,
            "avg_similarity": 0.4,
            "recommendations": ["Build on previous insights", "Consider using tags: product, insights"]
        }
    }
    
    # Display preview
    display_post_preview(post_data)
    
    # Save draft
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()[:30]
    output_file = f"data/posts/draft_{safe_topic.replace(' ', '_')}_{timestamp}.json"
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(post_data, f, indent=2)
    
    print(f"\n✅ Draft saved to {output_file}")
    print("\n🚀 Next Steps:")
    print(f"  1. python3 demo.py queue {output_file}")
    print(f"  2. python3 demo.py post {output_file}")

def display_post_preview(post_data: dict):
    """Display a formatted preview of the post."""
    print(f"\n📝 {post_data['title']}")
    print("=" * 50)
    print(f"\n{post_data['body']}")
    
    print(f"\n📊 Post Details:")
    print(f"  • Format: {post_data.get('format', 'N/A')}")
    print(f"  • Tags: {', '.join(post_data.get('tags', []))}")
    
    target_window = post_data.get('target_window', {})
    print(f"  • Suggested time: {target_window.get('day', 'TBD')} at {target_window.get('hour', 'TBD')}:00")

def queue_post(draft_file: str):
    """Queue a post for optimal posting time."""
    if not os.path.exists(draft_file):
        print(f"❌ Error: Draft file {draft_file} not found")
        return
    
    try:
        with open(draft_file, 'r') as f:
            post_data = json.load(f)
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in {draft_file}")
        return
    
    print(f"🔄 Queuing post: {post_data.get('title', 'Untitled')}")
    
    # Create schedule entry
    today = datetime.now()
    days_ahead = 0 - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    week_start = today + timedelta(days=days_ahead)
    week_of = week_start.strftime('%Y-%m-%d')
    
    target_window = post_data.get('target_window', {"day": "Tue", "hour": 10})
    
    queue_entry = {
        "post_id": post_data['id'],
        "day": target_window['day'],
        "hour": target_window['hour'],
        "status": "planned"
    }
    
    schedule_data = {
        "week_of": week_of,
        "slots": [queue_entry]
    }
    
    # Save schedule
    schedule_file = f"data/schedules/schedule_{week_of}.json"
    os.makedirs(os.path.dirname(schedule_file), exist_ok=True)
    with open(schedule_file, 'w') as f:
        json.dump(schedule_data, f, indent=2)
    
    print(f"\n📅 Queue Preview")
    print("=" * 30)
    print(f"Post: {post_data.get('title', 'Untitled')}")
    print(f"Scheduled: {queue_entry['day']} at {queue_entry['hour']}:00")
    print(f"Week of: {schedule_data['week_of']}")
    
    print(f"\n✅ Post queued for {target_window['day']} at {target_window['hour']}:00")
    print(f"💾 Schedule saved to {schedule_file}")

def post_content(draft_file: str):
    """Output ready-to-post content."""
    if not os.path.exists(draft_file):
        print(f"❌ Error: Draft file {draft_file} not found")
        return
    
    try:
        with open(draft_file, 'r') as f:
            post_data = json.load(f)
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in {draft_file}")
        return
    
    print(f"📋 Ready to post: {post_data.get('title', 'Untitled')}")
    print("=" * 50)
    print(post_data.get('body', ''))
    print("=" * 50)
    
    # Add hashtags
    tags = post_data.get('tags', [])
    if tags:
        hashtags = ' '.join(f"#{tag}" for tag in tags)
        print(f"\nSuggested hashtags: {hashtags}")
    
    target_window = post_data.get('target_window', {})
    if target_window:
        print(f"\n⏰ Optimal posting time: {target_window.get('day')} at {target_window.get('hour')}:00")
    
    print("\n✅ Content ready for posting!")
    print("Copy the content above and paste into LinkedIn")

def analyze_metrics():
    """Analyze performance metrics."""
    print("📊 Processing metrics...")
    
    # Load sample metrics
    metrics_file = "data/metrics/sample_metrics.json"
    if not os.path.exists(metrics_file):
        print("⚠️  No metrics data found. Run 'python3 demo.py init' first.")
        return
    
    with open(metrics_file, 'r') as f:
        metrics_data = json.load(f)
    
    # Calculate summary statistics
    total_posts = len(metrics_data)
    total_impressions = sum(m.get('impressions', 0) for m in metrics_data)
    total_reactions = sum(m.get('reactions', 0) for m in metrics_data)
    total_comments = sum(m.get('comments', 0) for m in metrics_data)
    total_shares = sum(m.get('shares', 0) for m in metrics_data)
    
    avg_impressions = total_impressions / total_posts if total_posts > 0 else 0
    avg_engagement_rate = sum(m.get('engagement_rate', 0) for m in metrics_data) / total_posts if total_posts > 0 else 0
    
    print(f"\n📊 Metrics Summary")
    print("=" * 40)
    print(f"Total Posts: {total_posts}")
    print(f"Total Impressions: {total_impressions:,}")
    print(f"Total Engagement: {total_reactions + total_comments + total_shares:,}")
    print(f"Avg Impressions: {avg_impressions:.0f}")
    print(f"Avg Engagement Rate: {avg_engagement_rate:.2%}")
    
    print(f"\n⭐ Best Performing Times:")
    print(f"  Tue 10:00 - 10.2% avg engagement")
    print(f"  Thu 14:00 - 10.7% avg engagement")
    
    print(f"\n🏆 Top Performing Posts:")
    for post in sorted(metrics_data, key=lambda m: m.get('engagement_rate', 0), reverse=True):
        post_id = post.get('post_id', 'Unknown')[:12]
        engagement = post.get('engagement_rate', 0)
        impressions = post.get('impressions', 0)
        print(f"  {post_id} - {engagement:.1%} ({impressions:,} impressions)")
    
    print("🔄 Updated posting recommendations based on performance data")

def load_config():
    """Load configuration from JSON file."""
    try:
        with open("config.json", 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "topics": ["product", "engineering", "founder"],
            "tone": "practical, concise, conversational"
        }

def extract_tags(topic: str) -> List[str]:
    """Extract tags from topic."""
    topic_words = topic.lower().split()
    base_tags = [word for word in topic_words if len(word) > 3]
    default_tags = ['linkedin', 'professional', 'insights']
    
    all_tags = list(set(base_tags + default_tags))
    return all_tags[:5]

if __name__ == '__main__':
    main()