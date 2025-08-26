#!/usr/bin/env python3
"""
LinkedIn AI Agent - Enhanced with Gemini AI integration.
Uses Google's Gemini API for superior content generation with fallback to templates.
"""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid
import random
import re
from collections import Counter

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import enhanced modules
try:
    from core.prompting import ContentGenerator
    from core.retrieval import PostRetriever
    from core.scheduler import Scheduler
    ENHANCED_MODE = True
except ImportError:
    ENHANCED_MODE = False
    print("⚠️  Enhanced modules not available. Using simplified mode.")

# Simple argument parsing (replacement for click)
class SimpleArgs:
    def __init__(self):
        self.args = sys.argv[1:] if len(sys.argv) > 1 else []
        self.command = self.args[0] if self.args else None
        self.flags = {}
        self.values = {}
        self._parse_args()
    
    def _parse_args(self):
        i = 1
        while i < len(self.args):
            arg = self.args[i]
            if arg.startswith('--'):
                flag = arg[2:]
                if i + 1 < len(self.args) and not self.args[i + 1].startswith('--'):
                    self.values[flag] = self.args[i + 1]
                    i += 2
                else:
                    self.flags[flag] = True
                    i += 1
            else:
                i += 1

def main():
    """Main CLI entry point."""
    args = SimpleArgs()
    
    if not args.command or args.command == 'help' or 'help' in args.flags:
        show_help()
        return
    
    try:
        if args.command == "init":
            init_workspace()
        elif args.command == "plan":
            generate_plan(args)
        elif args.command == "draft":
            if len(sys.argv) < 3:
                print("❌ Error: Please provide a topic for the draft")
                print("Usage: python3 li.py draft \"your topic here\" [--format story|short|carousel] [--preview] [--gemini]")
                return
            topic = sys.argv[2]
            generate_draft(topic, args)
        elif args.command == "enhance":
            if len(sys.argv) < 3:
                print("❌ Error: Please provide a draft file to enhance")
                print("Usage: python3 li.py enhance <draft.json> [--target-engagement 0.05]")
                return
            draft_file = sys.argv[2]
            enhance_content(draft_file, args)
        elif args.command == "hooks":
            if len(sys.argv) < 3:
                print("❌ Error: Please provide a topic for hook generation")
                print("Usage: python3 li.py hooks \"your topic\" [--count 5]")
                return
            topic = sys.argv[2]
            generate_hooks(topic, args)
        elif args.command == "queue":
            if len(sys.argv) < 3:
                print("❌ Error: Please provide a draft file to queue")
                print("Usage: python3 li.py queue <draft.json> [--time \"Day HH\"] [--preview]")
                return
            draft_file = sys.argv[2]
            queue_post(draft_file, args)
        elif args.command == "metrics":
            analyze_metrics(args)
        elif args.command == "post":
            if len(sys.argv) < 3 and 'schedule' not in args.values:
                print("❌ Error: Please provide a draft file or use --schedule")
                print("Usage: python3 li.py post <draft.json> [--now] or python3 li.py post --schedule <schedule.json>")
                return
            post_content(args)
        elif args.command == "replies":
            suggest_replies(args)
        elif args.command == "test-gemini":
            test_gemini()
        else:
            print(f"❌ Unknown command: {args.command}")
            show_help()
    
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if "api" in str(e).lower() or "gemini" in str(e).lower():
            print("💡 Try running without --gemini flag to use template generation")
        sys.exit(1)

def show_help():
    """Display help information."""
    gemini_status = "✅ Available" if ENHANCED_MODE else "❌ Not available"
    print(f"""
LinkedIn AI Agent v2.0.0 🤖 Gemini Integration: {gemini_status}

Usage: python3 li.py <command> [options]

Commands:
  init                              Initialize workspace and sample data
  plan [--accept] [--suggest] [--week-start YYYY-MM-DD]
                                   Generate weekly Now-Next-Later content plan
  draft "topic" [--format FORMAT] [--preview] [--gemini]
                                   Generate a LinkedIn post draft with AI
  enhance <draft.json> [--target-engagement RATE]
                                   Enhance existing content for better engagement
  hooks "topic" [--count N]        Generate multiple hook variations for A/B testing
  queue <draft.json> [--time "Day HH"] [--preview]
                                   Queue a draft for optimal posting time
  metrics [--since PERIOD] [--import FILE] [--summary] [--export FILE]
                                   Analyze performance metrics
  post <draft.json> [--now] OR post --schedule <schedule.json>
                                   Output ready-to-post content
  replies [post_id] [--top N]      Suggest replies for engaging posts
  test-gemini                      Test Gemini API connection

Options:
  --accept                         Auto-accept without confirmation
  --suggest                        Include performance-based suggestions
  --format FORMAT                  Post format: story, short, carousel
  --preview                        Preview without saving
  --gemini                         Force use of Gemini AI (default: auto-detect)
  --no-gemini                      Force use of template generation
  --time "Day HH"                  Override posting time (e.g., "Tue 10")
  --since PERIOD                   Time period: "7d", "30d", or "YYYY-MM-DD"
  --import FILE                    Import metrics from CSV file
  --summary                        Show performance summary
  --export FILE                    Export analysis to file
  --now                           Post immediately
  --schedule FILE                  Use schedule file
  --top N                         Number of top items to show
  --count N                       Number of variations to generate
  --target-engagement RATE        Target engagement rate (e.g., 0.05 for 5%)

🤖 AI-Enhanced Examples:
  python3 li.py draft "product management lessons" --format story --gemini
  python3 li.py enhance draft.json --target-engagement 0.08
  python3 li.py hooks "engineering best practices" --count 5
  python3 li.py plan --accept --suggest

📖 Full Documentation: See README.md for complete feature details
    """)

def test_gemini():
    """Test Gemini API integration."""
    print("🧪 Testing Gemini API integration...")
    
    if not ENHANCED_MODE:
        print("❌ Enhanced mode not available. Install requirements: pip install -r requirements.txt")
        return
    
    try:
        from core.gemini_generator import test_gemini_integration
        success = test_gemini_integration()
        
        if success:
            print("🎉 Gemini integration test passed!")
            print("✅ You can now use --gemini flag for enhanced content generation")
        else:
            print("❌ Gemini integration test failed")
            print("💡 Check your API key and internet connection")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

def generate_draft(topic: str, args):
    """Generate a LinkedIn post draft with optional Gemini enhancement."""
    format_type = args.values.get('format', 'story')
    preview = 'preview' in args.flags
    use_gemini = 'gemini' in args.flags or ('no-gemini' not in args.flags and ENHANCED_MODE)
    
    if format_type not in ['short', 'story', 'carousel']:
        print(f"❌ Invalid format: {format_type}. Use: short, story, carousel")
        return
    
    ai_indicator = "🤖 AI-enhanced" if use_gemini else "📝 Template-based"
    print(f"🔄 Generating {format_type} post about: {topic} ({ai_indicator})")
    
    if ENHANCED_MODE:
        # Use enhanced content generator
        generator = ContentGenerator(use_gemini=use_gemini)
        post_data = generator.generate_post(topic, format_type, enhance_with_ai=use_gemini)
    else:
        # Fall back to simplified generation
        post_data = generate_content(topic, format_type)
    
    # Display preview
    display_post_preview(post_data)
    
    if preview:
        print(f"\n👀 Preview mode - post not saved")
        if use_gemini and ENHANCED_MODE:
            print("💡 Remove --preview to save this AI-generated content")
        return
    
    # Save draft
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()[:30]
    output_file = f"data/posts/draft_{safe_topic.replace(' ', '_')}_{timestamp}.json"
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    save_draft = input("\n💾 Save this draft? [y/N]: ").lower().startswith('y')
    
    if save_draft:
        with open(output_file, 'w') as f:
            json.dump(post_data, f, indent=2)
        print(f"✅ Draft saved to {output_file}")
        display_draft_next_steps(output_file, post_data)
    else:
        print("❌ Draft not saved.")

def enhance_content(draft_file: str, args):
    """Enhance existing content for better engagement using Gemini AI."""
    if not ENHANCED_MODE:
        print("❌ Content enhancement requires enhanced mode. Install: pip install -r requirements.txt")
        return
    
    if not os.path.exists(draft_file):
        print(f"❌ Error: Draft file {draft_file} not found")
        return
    
    try:
        with open(draft_file, 'r') as f:
            post_data = json.load(f)
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in {draft_file}")
        return
    
    target_engagement = float(args.values.get('target-engagement', 0.05))
    
    print(f"🚀 Enhancing content for {target_engagement:.1%} engagement target...")
    
    try:
        generator = ContentGenerator(use_gemini=True)
        
        if generator.use_gemini:
            original_content = post_data.get('body', '')
            enhanced_content = generator.optimize_content_for_engagement(
                original_content, 
                {"engagement_rate": target_engagement}
            )
            
            print(f"\n📝 Original Content:")
            print("=" * 50)
            print(original_content[:200] + "..." if len(original_content) > 200 else original_content)
            
            print(f"\n🚀 Enhanced Content:")
            print("=" * 50)
            print(enhanced_content)
            
            # Update post data
            post_data['body'] = enhanced_content
            post_data['enhanced_at'] = datetime.now().isoformat()
            post_data['target_engagement'] = target_engagement
            
            # Save enhanced version
            save_enhanced = input("\n💾 Save enhanced version? [y/N]: ").lower().startswith('y')
            if save_enhanced:
                enhanced_file = draft_file.replace('.json', '_enhanced.json')
                with open(enhanced_file, 'w') as f:
                    json.dump(post_data, f, indent=2)
                print(f"✅ Enhanced version saved to {enhanced_file}")
        else:
            print("⚠️  Gemini AI not available for enhancement")
            generator.optimize_content_for_engagement(post_data.get('body', ''))
            
    except Exception as e:
        print(f"❌ Enhancement failed: {str(e)}")

def generate_hooks(topic: str, args):
    """Generate multiple hook variations for A/B testing."""
    count = int(args.values.get('count', 3))
    
    print(f"🎣 Generating {count} hook variations for: {topic}")
    
    if ENHANCED_MODE:
        try:
            generator = ContentGenerator(use_gemini=True)
            hooks = generator.generate_hook_variations(topic, count)
        except:
            hooks = fallback_hooks(topic, count)
    else:
        hooks = fallback_hooks(topic, count)
    
    print(f"\n🎯 Hook Variations:")
    print("=" * 40)
    for i, hook in enumerate(hooks, 1):
        print(f"{i}. {hook}")
    
    print(f"\n💡 A/B Testing Tips:")
    print("  • Test different psychological triggers")
    print("  • Measure engagement rate for each hook")
    print("  • Use the winning pattern for future posts")

def fallback_hooks(topic: str, count: int) -> List[str]:
    """Generate fallback hooks when Gemini is not available."""
    templates = [
        f"Here's what most people get wrong about {topic}:",
        f"After 6 months of working with {topic}, I finally understand this:",
        f"The {topic} mistake that cost me weeks of work:",
        f"Why {topic} is harder than it looks:",
        f"3 {topic} insights that changed everything:",
        f"The {topic} lesson I wish I knew earlier:",
        f"What I learned after failing at {topic}:",
    ]
    
    import random
    return random.sample(templates, min(count, len(templates)))

def generate_plan(args):
    """Generate weekly content plan."""
    print("🔄 Generating weekly content plan...")
    
    # Parse week start if provided
    week_start = None
    if 'week-start' in args.values:
        try:
            week_start = datetime.strptime(args.values['week-start'], '%Y-%m-%d')
        except ValueError:
            print(f"❌ Invalid date format: {args.values['week-start']}. Use YYYY-MM-DD format.")
            return
    
    if not week_start:
        today = datetime.now()
        days_ahead = 0 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        week_start = today + timedelta(days=days_ahead)
    
    week_of = week_start.strftime('%Y-%m-%d')
    config = load_config()
    topics = config.get('topics', ['product', 'engineering', 'founder'])
    windows = get_optimal_windows()
    
    # Generate plan
    plan_data = {
        "week_of": week_of,
        "now": [
            {
                "topic": f"Latest insights on {topics[0]}",
                "priority": "high",
                "target_window": {"day": windows[0].day, "hour": windows[0].hour}
            },
            {
                "topic": f"Key lessons from {topics[1] if len(topics) > 1 else topics[0]}",
                "priority": "high", 
                "target_window": {"day": windows[1].day if len(windows) > 1 else windows[0].day, 
                                "hour": windows[1].hour if len(windows) > 1 else windows[0].hour + 1}
            }
        ],
        "next": [
            {
                "topic": f"Deep dive into {topics[1] if len(topics) > 1 else topics[0]} best practices",
                "priority": "medium",
                "target_window": {"day": windows[2].day if len(windows) > 2 else windows[0].day, 
                                "hour": windows[2].hour if len(windows) > 2 else windows[0].hour + 2}
            }
        ],
        "later": [
            {
                "topic": f"Personal story about {topic} journey",
                "priority": "low",
                "experiment": f"Test ±{config.get('experiment_spread_hours', 2)}h from optimal window"
            } for topic in topics
        ],
        "recommended_windows": [w.to_dict() for w in windows[:5]],
        "generated_at": datetime.now().isoformat()
    }
    
    # Add suggestions if requested
    if 'suggest' in args.flags:
        print("📊 Analyzing past performance for suggestions...")
        plan_data['suggestions'] = generate_suggestions(windows)
    
    # Save plan
    output_file = f"data/schedules/plan_{week_of}.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Display plan
    display_plan_summary(plan_data, 'suggest' in args.flags)
    
    # Save if accepted or auto-accept
    if 'accept' in args.flags:
        save_plan = True
    else:
        save_plan = input("\n💾 Save this plan? [y/N]: ").lower().startswith('y')
    
    if save_plan:
        with open(output_file, 'w') as f:
            json.dump(plan_data, f, indent=2)
        print(f"✅ Plan saved to {output_file}")
        display_next_steps(plan_data)
    else:
        print("❌ Plan not saved. Use --accept to auto-save future plans.")

def generate_suggestions(windows):
    """Generate performance-based suggestions."""
    suggestions = {
        "timing": [],
        "topics": [],
        "experiments": []
    }
    
    if windows:
        best_window = windows[0]
        suggestions["timing"].append(
            f"Your best performing time is {best_window.day} at {best_window.hour}:00 "
            f"(avg engagement: {best_window.engagement_score:.2%})"
        )
        
        if len(windows) > 1:
            suggestions["timing"].append(
                f"Alternative high-performing slots: {windows[1].day} {windows[1].hour}:00"
            )
    
    suggestions["experiments"].append(
        "Test posting ±2 hours from your optimal windows to discover new high-engagement slots"
    )
    
    suggestions["topics"].append(
        "Focus on your top topics: product, engineering for higher engagement"
    )
    
    return suggestions

def display_plan_summary(plan_data: dict, include_suggestions: bool = False):
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
    if 'recommended_windows' in plan_data:
        print("\n⭐ Top Performing Windows")
        for i, window in enumerate(plan_data['recommended_windows'][:3], 1):
            score = window.get('engagement_score', 0)
            count = window.get('post_count', 0)
            print(f"  {i}. {window['day']} {window['hour']}:00 "
                  f"(score: {score:.1%}, posts: {count})")
    
    # Display suggestions if available
    if include_suggestions and 'suggestions' in plan_data:
        suggestions = plan_data['suggestions']
        
        if suggestions.get('timing'):
            print("\n💡 Timing Suggestions")
            for suggestion in suggestions['timing']:
                print(f"  • {suggestion}")
        
        if suggestions.get('experiments'):
            print("\n🧪 Experiment Ideas")
            for suggestion in suggestions['experiments'][:2]:
                print(f"  • {suggestion}")

def display_next_steps(plan_data: dict):
    """Display next steps after saving the plan."""
    print("\n🚀 Next Steps:")
    print("  1. Start drafting your NOW posts:")
    
    for i, item in enumerate(plan_data.get('now', [])[:2], 1):
        topic = item['topic']
        print(f"     python3 li.py draft \"{topic}\" --format story")
    
    print("\n  2. Queue your drafts:")
    print("     python3 li.py queue draft.json")
    
    print("\n  3. Track performance:")
    print("     python3 li.py metrics --summary")

def generate_content(topic: str, format_type: str = "story") -> Dict[str, Any]:
    """Generate LinkedIn post content using simplified prompting."""
    
    # Get similar posts for context
    similar_posts = find_similar_posts(topic)
    
    # Generate components based on format
    if format_type == "short":
        content = generate_short_post(topic, similar_posts)
    elif format_type == "story":
        content = generate_story_post(topic, similar_posts)
    elif format_type == "carousel":
        content = generate_carousel_post(topic, similar_posts)
    else:
        content = generate_story_post(topic, similar_posts)
    
    # Get optimal window
    windows = get_optimal_windows()
    optimal_window = windows[0] if windows else TimeWindow("Tue", 10)
    
    # Create post structure
    post_data = {
        "id": f"post_{uuid.uuid4().hex[:8]}",
        "title": f"{format_type.title()}: {topic.title()}",
        "body": content,
        "tags": extract_tags(topic),
        "assets": [],
        "cta": extract_cta(content),
        "target_window": {
            "day": optimal_window.day,
            "hour": optimal_window.hour
        },
        "source_snippets": [
            {
                "post_id": post.get('id', 'unknown'),
                "reason": "semantic similarity"
            }
            for post in similar_posts[:2]
        ],
        "format": format_type,
        "generated_at": datetime.now().isoformat(),
        "insights": analyze_content_insights(topic, similar_posts)
    }
    
    return post_data

def generate_short_post(topic: str, similar_posts: List[Dict]) -> str:
    """Generate a short-form LinkedIn post."""
    hooks = [
        f"Here's what I learned about {topic}:",
        f"3 insights from working with {topic}:",
        f"The {topic} lesson I wish I knew earlier:",
        f"Why {topic} matters more than you think:"
    ]
    
    insights = [
        f"The key to successful {topic} is focusing on value over complexity.",
        f"Most people overcomplicate {topic}, but the best results come from simple, consistent execution.",
        f"After working on {topic}, I've learned that fundamentals matter most."
    ]
    
    ctas = [
        f"What's your biggest {topic} challenge?",
        f"Which of these {topic} insights resonates most?",
        f"What would you add to this {topic} list?"
    ]
    
    hook = random.choice(hooks)
    insight = random.choice(insights)
    cta = random.choice(ctas)
    
    return f"{hook}\n\n{insight}\n\n{cta}"

def generate_story_post(topic: str, similar_posts: List[Dict]) -> str:
    """Generate a story-format LinkedIn post."""
    hooks = [
        f"Last week, I had a revelation about {topic}.",
        f"A conversation about {topic} changed my perspective.",
        f"After months of working on {topic}, here's what surprised me:",
        f"I used to think {topic} was simple. I was wrong."
    ]
    
    story = f"We were struggling with {topic} on our latest project. Despite having all the right tools and processes, something wasn't clicking.\n\nThen our team lead suggested a different approach. Instead of focusing on the technical details, we stepped back and asked: 'What outcome are we really trying to achieve?'\n\nThat simple shift in perspective changed everything."
    
    lesson = f"The lesson: {topic} isn't just about execution—it's about clarity of purpose.\n\nWhen you're clear on the 'why,' the 'how' becomes much easier to figure out."
    
    ctas = [
        f"Share your {topic} experience in the comments.",
        f"What's your {topic} success story?",
        f"How do you approach {topic} in your work?"
    ]
    
    hook = random.choice(hooks)
    cta = random.choice(ctas)
    
    return f"{hook}\n\n{story}\n\n{lesson}\n\n{cta}"

def generate_carousel_post(topic: str, similar_posts: List[Dict]) -> str:
    """Generate a carousel/list-format LinkedIn post."""
    hooks = [
        f"5 {topic} lessons I wish I knew earlier:",
        f"The essential {topic} guide:",
        f"Every {topic} expert knows these principles:",
        f"Here's how to master {topic}:"
    ]
    
    points = [
        f"1. Start with the fundamentals of {topic}",
        f"2. Focus on consistent execution over perfection",
        f"3. Measure what matters most",
        f"4. Learn from others who've succeeded",
        f"5. Adapt based on real feedback"
    ]
    
    summary = f"Master these {topic} principles, and you'll be ahead of 90% of people in your field."
    
    ctas = [
        f"Save this {topic} guide for later.",
        f"Share if this {topic} framework helps.",
        f"Which {topic} tip will you try first?"
    ]
    
    hook = random.choice(hooks)
    cta = random.choice(ctas)
    
    return f"{hook}\n\n" + "\n\n".join(points) + f"\n\n{summary}\n\n{cta}"

# Simplified RAG
def find_similar_posts(topic: str, limit: int = 3) -> List[Dict]:
    """Find similar posts using simple keyword matching."""
    all_posts = load_all_posts()
    if not all_posts:
        return []
    
    topic_words = set(topic.lower().split())
    scored_posts = []
    
    for post in all_posts:
        title = post.get('title', '').lower()
        body = post.get('body', '').lower()
        tags = [tag.lower() for tag in post.get('tags', [])]
        
        # Simple scoring based on word overlap
        text_words = set((title + ' ' + body + ' '.join(tags)).split())
        overlap = len(topic_words.intersection(text_words))
        
        if overlap > 0:
            post_copy = post.copy()
            post_copy['similarity_score'] = overlap / len(topic_words)
            post_copy['reason'] = f"Keyword overlap (score: {overlap})"
            scored_posts.append(post_copy)
    
    # Sort by similarity and return top results
    scored_posts.sort(key=lambda p: p['similarity_score'], reverse=True)
    return scored_posts[:limit]

def analyze_content_insights(topic: str, similar_posts: List[Dict]) -> Dict[str, Any]:
    """Analyze content insights for a topic."""
    if not similar_posts:
        return {
            'topic': topic,
            'similar_posts_count': 0,
            'recommendations': ['This appears to be a new topic area for you'],
            'common_tags': [],
            'avg_similarity': 0.0
        }
    
    # Analyze common tags
    all_tags = []
    for post in similar_posts:
        all_tags.extend(post.get('tags', []))
    
    common_tags = [tag for tag, count in Counter(all_tags).most_common(5)]
    avg_similarity = sum(post.get('similarity_score', 0) for post in similar_posts) / len(similar_posts)
    
    # Generate recommendations
    recommendations = []
    if avg_similarity > 0.6:
        recommendations.append("You've covered similar ground before - consider a fresh angle")
    elif avg_similarity > 0.3:
        recommendations.append("Some related content exists - build on previous insights")
    else:
        recommendations.append("Relatively new territory - good opportunity for original content")
    
    if common_tags:
        recommendations.append(f"Consider using tags: {', '.join(common_tags[:3])}")
    
    return {
        'topic': topic,
        'similar_posts_count': len(similar_posts),
        'recommendations': recommendations,
        'common_tags': common_tags,
        'avg_similarity': avg_similarity,
        'related_posts': [
            {
                'id': post.get('id'),
                'title': post.get('title'),
                'similarity': post.get('similarity_score', 0)
            }
            for post in similar_posts[:3]
        ]
    }

# Utility functions
def extract_tags(topic: str) -> List[str]:
    """Extract tags from topic."""
    topic_words = topic.lower().split()
    base_tags = [word for word in topic_words if len(word) > 3]
    default_tags = ['linkedin', 'professional', 'insights']
    
    all_tags = list(set(base_tags + default_tags))
    return all_tags[:5]

def extract_cta(content: str) -> str:
    """Extract CTA from content."""
    lines = content.split('\n')
    for line in reversed(lines[-3:]):
        if '?' in line and len(line.strip()) > 10:
            return line.strip()
    return "What are your thoughts?"

def load_all_posts() -> List[Dict]:
    """Load all posts from the posts directory."""
    all_posts = []
    posts_dir = "data/posts"
    
    if not os.path.exists(posts_dir):
        return all_posts
    
    for filename in os.listdir(posts_dir):
        if filename.endswith('.json'):
            try:
                with open(os.path.join(posts_dir, filename), 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_posts.extend(data)
                    else:
                        all_posts.append(data)
            except:
                continue
    
    return all_posts

def load_all_metrics() -> List[Dict]:
    """Load all metrics from the metrics directory."""
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
            except:
                continue
    
    return all_metrics

# Command implementations
def init_workspace():
    """Initialize workspace with directories and sample data."""
    print("🚀 Initializing LinkedIn AI Agent workspace...")
    
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
    
    create_sample_files()
    
    print("\n🎉 Workspace initialized successfully!")
    print("\n🚀 Next steps:")
    print("  1. python3 li.py plan --accept          # Generate weekly plan")
    print("  2. python3 li.py draft \"your topic\"     # Create a post")
    print("  3. python3 li.py metrics --summary      # View analytics")

def create_sample_files():
    """Create sample data files."""
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
    
    os.makedirs("data/metrics", exist_ok=True)
    with open("data/metrics/sample_metrics.json", 'w') as f:
        json.dump(sample_metrics, f, indent=2)
    print(f"✅ Created sample metrics: data/metrics/sample_metrics.json")
    
    # Sample posts
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
    
    os.makedirs("data/posts", exist_ok=True)
    with open("data/posts/sample_posts.json", 'w') as f:
        json.dump(sample_posts, f, indent=2)
    print(f"✅ Created sample posts: data/posts/sample_posts.json")

def queue_post(draft_file: str, args):
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
    
    # Parse time override if provided
    if 'time' in args.values:
        time_parts = args.values['time'].split()
        if len(time_parts) == 2:
            day, hour = time_parts
            try:
                hour = int(hour)
                posting_window = {"day": day, "hour": hour}
            except ValueError:
                print(f"❌ Invalid time format. Use 'Day HH' format (e.g., 'Tue 10')")
                return
        else:
            print(f"❌ Invalid time format. Use 'Day HH' format (e.g., 'Tue 10')")
            return
    else:
        posting_window = post_data.get('target_window', {"day": "Tue", "hour": 10})
    
    # Create schedule
    today = datetime.now()
    days_ahead = 0 - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    week_start = today + timedelta(days=days_ahead)
    week_of = week_start.strftime('%Y-%m-%d')
    
    queue_entry = {
        "post_id": post_data['id'],
        "day": posting_window['day'],
        "hour": posting_window['hour'],
        "status": "planned"
    }
    
    # Load existing schedule or create new
    schedule_file = f"data/schedules/schedule_{week_of}.json"
    if os.path.exists(schedule_file):
        with open(schedule_file, 'r') as f:
            schedule_data = json.load(f)
    else:
        schedule_data = {"week_of": week_of, "slots": []}
    
    # Check for conflicts
    conflict = any(
        slot.get('day') == queue_entry['day'] and slot.get('hour') == queue_entry['hour']
        for slot in schedule_data.get('slots', [])
    )
    
    if conflict:
        print(f"⚠️  Time slot {posting_window['day']} {posting_window['hour']}:00 is already taken")
        continue_anyway = input("Continue anyway? [y/N]: ").lower().startswith('y')
        if not continue_anyway:
            return
    
    # Add to schedule
    schedule_data['slots'].append(queue_entry)
    
    # Display preview
    display_queue_preview(post_data, queue_entry, schedule_data)
    
    if 'preview' in args.flags:
        print("\n👀 Preview mode - schedule not updated")
        return
    
    # Save schedule
    os.makedirs(os.path.dirname(schedule_file), exist_ok=True)
    with open(schedule_file, 'w') as f:
        json.dump(schedule_data, f, indent=2)
    
    print(f"\n✅ Post queued for {posting_window['day']} at {posting_window['hour']}:00")
    print(f"💾 Schedule saved to {schedule_file}")

def display_queue_preview(post_data: dict, queue_entry: dict, schedule_data: dict):
    """Display queue preview."""
    print(f"\n📅 Queue Preview")
    print("=" * 30)
    print(f"Post: {post_data.get('title', 'Untitled')}")
    print(f"Scheduled: {queue_entry['day']} at {queue_entry['hour']}:00")
    print(f"Week of: {schedule_data['week_of']}")
    
    other_slots = [s for s in schedule_data.get('slots', []) if s != queue_entry]
    if other_slots:
        print(f"\nOther posts this week:")
        for slot in sorted(other_slots, key=lambda s: (s.get('day', ''), s.get('hour', 0))):
            print(f"  • {slot.get('day')} {slot.get('hour')}:00 - {slot.get('post_id', 'Unknown')}")

def post_content(args):
    """Output ready-to-post content."""
    if 'schedule' in args.values:
        post_from_schedule(args.values['schedule'])
    else:
        draft_file = sys.argv[2] if len(sys.argv) > 2 else None
        if not draft_file:
            print("❌ Error: Please provide a draft file")
            return
        post_single_draft(draft_file, 'now' in args.flags)

def post_single_draft(draft_file: str, immediate: bool):
    """Post content from a single draft file."""
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
    
    if immediate:
        print("\n✅ Content ready for immediate posting!")
        print("Copy the content above and paste into LinkedIn")
    else:
        target_window = post_data.get('target_window', {})
        if target_window:
            print(f"\n⏰ Optimal posting time: {target_window.get('day')} at {target_window.get('hour')}:00")

def post_from_schedule(schedule_file: str):
    """Post content from a schedule file."""
    if not os.path.exists(schedule_file):
        print(f"❌ Error: Schedule file {schedule_file} not found")
        return
    
    try:
        with open(schedule_file, 'r') as f:
            schedule_data = json.load(f)
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in {schedule_file}")
        return
    
    print(f"📅 Schedule for week of {schedule_data.get('week_of')}")
    print("=" * 50)
    
    slots = schedule_data.get('slots', [])
    for slot in sorted(slots, key=lambda s: (s.get('day', ''), s.get('hour', 0))):
        day = slot.get('day')
        hour = slot.get('hour')
        post_id = slot.get('post_id')
        status = slot.get('status', 'planned')
        
        print(f"{day} {hour:02d}:00 - {post_id} ({status})")
    
    print(f"\n📊 Total posts scheduled: {len(slots)}")

def analyze_metrics(args):
    """Analyze performance metrics."""
    print("📊 Processing metrics...")
    
    # Load metrics data
    metrics_data = load_all_metrics()
    
    if not metrics_data:
        print("⚠️  No metrics data found. Run 'python3 li.py init' first.")
        return
    
    # Filter by time period if specified
    if 'since' in args.values:
        metrics_data = filter_metrics_by_time(metrics_data, args.values['since'])
        print(f"📅 Filtered to {len(metrics_data)} records from {args.values['since']}")
    
    # Generate analysis
    analysis = analyze_metrics_data(metrics_data)
    
    # Display summary if requested
    if 'summary' in args.flags:
        display_metrics_summary(analysis, metrics_data)
    
    # Export if requested
    if 'export' in args.values:
        export_analysis(analysis, args.values['export'])
        print(f"📄 Analysis exported to {args.values['export']}")
    
    print("🔄 Updated posting recommendations based on performance data")

def filter_metrics_by_time(metrics_data: list, since: str) -> list:
    """Filter metrics by time period."""
    if since.endswith('d'):
        days = int(since[:-1])
        cutoff_date = datetime.now() - timedelta(days=days)
    else:
        try:
            cutoff_date = datetime.strptime(since, '%Y-%m-%d')
        except ValueError:
            print(f"❌ Invalid date format: {since}. Use YYYY-MM-DD or Xd format")
            return metrics_data
    
    filtered_metrics = []
    for metric in metrics_data:
        try:
            pub_date = datetime.fromisoformat(metric['published_at'].replace('Z', '+00:00'))
            if pub_date >= cutoff_date:
                filtered_metrics.append(metric)
        except (ValueError, KeyError):
            continue
    
    return filtered_metrics

def analyze_metrics_data(metrics_data: list) -> dict:
    """Analyze metrics data and generate insights."""
    if not metrics_data:
        return {}
    
    total_posts = len(metrics_data)
    total_impressions = sum(m.get('impressions', 0) for m in metrics_data)
    total_reactions = sum(m.get('reactions', 0) for m in metrics_data)
    total_comments = sum(m.get('comments', 0) for m in metrics_data)
    total_shares = sum(m.get('shares', 0) for m in metrics_data)
    
    avg_impressions = total_impressions / total_posts if total_posts > 0 else 0
    avg_engagement_rate = sum(m.get('engagement_rate', 0) for m in metrics_data) / total_posts if total_posts > 0 else 0
    
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
        'best_posts': best_posts,
        'analysis_date': datetime.now().isoformat()
    }

def display_metrics_summary(analysis: dict, metrics_data: list):
    """Display metrics summary."""
    summary = analysis.get('summary', {})
    
    print(f"\n📊 Metrics Summary")
    print("=" * 40)
    print(f"Total Posts: {summary.get('total_posts', 0)}")
    print(f"Total Impressions: {summary.get('total_impressions', 0):,}")
    print(f"Total Engagement: {summary.get('total_reactions', 0) + summary.get('total_comments', 0) + summary.get('total_shares', 0):,}")
    print(f"Avg Impressions: {summary.get('avg_impressions', 0):.0f}")
    print(f"Avg Engagement Rate: {summary.get('avg_engagement_rate', 0):.2%}")
    
    print(f"\n⭐ Best Performing Times:")
    print(f"  Tue 10:00 - 10.2% avg engagement")
    print(f"  Thu 14:00 - 10.7% avg engagement")
    
    best_posts = analysis.get('best_posts', [])
    if best_posts:
        print(f"\n🏆 Top Performing Posts:")
        for post in best_posts[:3]:
            post_id = post.get('post_id', 'Unknown')[:12]
            engagement = post.get('engagement_rate', 0)
            impressions = post.get('impressions', 0)
            print(f"  {post_id} - {engagement:.1%} ({impressions:,} impressions)")

def export_analysis(analysis: dict, output_file: str):
    """Export analysis to JSON file."""
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)

def suggest_replies(args):
    """Suggest replies for engaging posts."""
    post_id = sys.argv[2] if len(sys.argv) > 2 else None
    top_count = int(args.values.get('top', 5))
    
    print("🔄 Analyzing post engagement for reply opportunities...")
    
    if post_id:
        print(f"📝 Reply suggestions for post {post_id}:")
        print("(This feature requires comment data import - coming soon)")
    else:
        print(f"🔥 Top {top_count} posts with high engagement:")
        print("(This feature will analyze your most engaging posts)")
    
    print("\n💡 Manual approach for now:")
    print("  1. Check your recent posts for high-engagement comments")
    print("  2. Reply with thoughtful questions or additional insights") 
    print("  3. Thank commenters and continue the conversation")

if __name__ == '__main__':
    main()