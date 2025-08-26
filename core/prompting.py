"""
Core prompting and content generation module for LinkedIn AI agent.
Handles structured post generation with hooks, value, and CTAs.
Enhanced with Gemini AI integration for superior content quality.
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from core.retrieval import PostRetriever
from core.scheduler import Scheduler

# Try to import Gemini generator, fall back gracefully
try:
    from core.gemini_generator import GeminiContentGenerator
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  Gemini AI not available. Using template-based generation.")


class ContentGenerator:
    """
    Generates LinkedIn posts using prompting techniques and RAG.
    
    Creates structured posts with engaging hooks, valuable content,
    and clear calls-to-action, grounded in past performance data.
    Enhanced with Gemini AI for superior content quality when available.
    """
    
    POST_FORMATS = {
        'short': {
            'max_length': 300,
            'structure': 'Hook + Key insight + CTA',
            'template': '{hook}\n\n{insight}\n\n{cta}'
        },
        'story': {
            'max_length': 1200,
            'structure': 'Hook + Story + Lesson + CTA',
            'template': '{hook}\n\n{story}\n\n{lesson}\n\n{cta}'
        },
        'carousel': {
            'max_length': 2000,
            'structure': 'Hook + Multiple points + Summary + CTA',
            'template': '{hook}\n\n{points}\n\n{summary}\n\n{cta}'
        }
    }
    
    def __init__(self, config_path: str = "config.json", use_gemini: bool = True):
        """
        Initialize content generator with configuration.
        
        Args:
            config_path: Path to configuration file
            use_gemini: Whether to use Gemini AI for content generation
        """
        self.config = self._load_config(config_path)
        self.retriever = PostRetriever()
        self.scheduler = Scheduler()
        
        # Initialize Gemini if available and requested
        self.use_gemini = use_gemini and GEMINI_AVAILABLE
        if self.use_gemini:
            try:
                self.gemini_generator = GeminiContentGenerator()
                print("✅ Gemini AI content generator initialized")
            except Exception as e:
                print(f"⚠️  Failed to initialize Gemini: {str(e)}")
                print("🔄 Falling back to template-based generation")
                self.use_gemini = False
        else:
            self.gemini_generator = None
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "tone": "practical, concise, conversational",
                "topics": ["product", "engineering", "founder"]
            }
    
    def generate_post(self, topic: str, format_type: str = "story", enhance_with_ai: bool = True) -> Dict[str, Any]:
        """
        Generate a LinkedIn post on the given topic using RAG and prompting.
        
        Args:
            topic: Topic or prompt for the post
            format_type: Type of post format (short, story, carousel)
            enhance_with_ai: Whether to use Gemini AI for enhanced generation
            
        Returns:
            Dictionary containing the generated post with metadata
        """
        if format_type not in self.POST_FORMATS:
            raise ValueError(f"Unsupported format: {format_type}. Use: {list(self.POST_FORMATS.keys())}")
        
        # Retrieve similar posts for context
        similar_posts = self.retriever.retrieve_similar(topic, top_k=3)
        content_insights = self.retriever.get_content_insights(topic)
        
        # Generate content - use Gemini if available and requested
        if self.use_gemini and enhance_with_ai:
            content = self._generate_with_gemini(topic, format_type, similar_posts, content_insights)
        else:
            content = self._generate_with_templates(topic, format_type, similar_posts)
        
        # Get optimal posting window
        optimal_window = self.scheduler.suggest_posting_time()
        
        # Extract or suggest tags
        suggested_tags = self._extract_tags(topic, content_insights)
        
        # Create post structure
        post = {
            "id": f"post_{uuid.uuid4().hex[:8]}",
            "title": self._generate_title(topic, format_type),
            "body": content,
            "tags": suggested_tags,
            "assets": [],
            "cta": self._extract_cta(content),
            "target_window": {
                "day": optimal_window.day,
                "hour": optimal_window.hour
            },
            "source_snippets": [
                {
                    "post_id": post.get('id', 'unknown'),
                    "reason": post.get('reason', 'semantic similarity')
                }
                for post in similar_posts
            ],
            "format": format_type,
            "generated_at": datetime.now().isoformat(),
            "insights": content_insights,
            "generation_method": "gemini" if (self.use_gemini and enhance_with_ai) else "template"
        }
        
        return post
    
    def _generate_with_gemini(self, topic: str, format_type: str, similar_posts: List[Dict], insights: Dict) -> str:
        """Generate content using Gemini AI."""
        try:
            # Prepare performance insights for Gemini
            performance_insights = {}
            if hasattr(self.scheduler, 'get_performance_insights'):
                performance_insights = self.scheduler.get_performance_insights()
            
            content = self.gemini_generator.generate_linkedin_post(
                topic=topic,
                format_type=format_type,
                similar_posts=similar_posts,
                performance_insights=performance_insights,
                config=self.config
            )
            
            print("🤖 Content generated using Gemini AI")
            return content
            
        except Exception as e:
            print(f"⚠️  Gemini generation failed: {str(e)}")
            print("🔄 Falling back to template generation")
            return self._generate_with_templates(topic, format_type, similar_posts)
    
    def _generate_with_templates(self, topic: str, format_type: str, similar_posts: List[Dict]) -> str:
        """Generate content using template-based approach."""
        if format_type == "short":
            content = self._generate_short_post(topic, similar_posts)
        elif format_type == "story":
            content = self._generate_story_post(topic, similar_posts)
        elif format_type == "carousel":
            content = self._generate_carousel_post(topic, similar_posts)
        
        print("📝 Content generated using templates")
        return content
    
    def generate_hook_variations(self, topic: str, count: int = 3) -> List[str]:
        """Generate multiple hook variations for A/B testing."""
        if self.use_gemini:
            try:
                return self.gemini_generator.generate_hook_variations(topic, count)
            except:
                pass
        
        # Fallback to template-based hooks
        hooks = [
            f"Here's what most people get wrong about {topic}:",
            f"After 6 months of working with {topic}, I finally understand this:",
            f"The {topic} mistake that cost me weeks of work:",
            f"Why {topic} is harder than it looks:",
            f"3 {topic} insights that changed everything:"
        ]
        
        import random
        return random.sample(hooks, min(count, len(hooks)))
    
    def optimize_content_for_engagement(self, content: str, target_metrics: Dict = None) -> str:
        """Optimize existing content for better engagement."""
        if self.use_gemini:
            try:
                return self.gemini_generator.optimize_for_engagement(content, target_metrics)
            except:
                pass
        
        # Simple template-based optimization
        print("💡 For better engagement, consider:")
        print("   - Adding more specific examples")
        print("   - Including numbers or statistics")
        print("   - Strengthening the call-to-action")
        print("   - Adding relevant emojis")
        
        return content
    
    def generate_cta_variations(self, topic: str, content: str) -> List[str]:
        """Generate multiple CTA variations."""
        if self.use_gemini:
            try:
                return self.gemini_generator.generate_cta_variations(topic, content)
            except:
                pass
        
        # Fallback CTAs
        return [
            f"What's your biggest {topic} challenge?",
            f"Share your {topic} success story below.",
            f"Which {topic} strategy works best for you?",
            f"Tag someone who needs to see this {topic} advice.",
            f"What would you add to this {topic} list?"
        ]
    
    # ...existing template-based methods...
    def _generate_short_post(self, topic: str, similar_posts: List[Dict]) -> str:
        """Generate a short-form LinkedIn post."""
        tone = self.config.get('tone', 'conversational')
        
        # Analyze successful patterns from similar posts
        hook_patterns = self._analyze_hooks(similar_posts)
        
        # Generate hook
        hook = self._generate_hook(topic, hook_patterns)
        
        # Generate key insight
        insight = self._generate_insight(topic, similar_posts, format="concise")
        
        # Generate CTA
        cta = self._generate_cta(topic, "question")
        
        return f"{hook}\n\n{insight}\n\n{cta}"
    
    def _generate_story_post(self, topic: str, similar_posts: List[Dict]) -> str:
        """Generate a story-format LinkedIn post."""
        tone = self.config.get('tone', 'conversational')
        
        # Generate components
        hook = self._generate_hook(topic, style="story")
        story = self._generate_story_content(topic, similar_posts)
        lesson = self._generate_lesson(topic, similar_posts)
        cta = self._generate_cta(topic, "engagement")
        
        return f"{hook}\n\n{story}\n\n{lesson}\n\n{cta}"
    
    def _generate_carousel_post(self, topic: str, similar_posts: List[Dict]) -> str:
        """Generate a carousel/list-format LinkedIn post."""
        hook = self._generate_hook(topic, style="list")
        points = self._generate_key_points(topic, similar_posts)
        summary = self._generate_summary(topic, points)
        cta = self._generate_cta(topic, "share")
        
        return f"{hook}\n\n{points}\n\n{summary}\n\n{cta}"
    
    def _generate_hook(self, topic: str, patterns: Optional[List] = None, style: str = "default") -> str:
        """Generate an engaging hook for the post."""
        hooks = {
            "default": [
                f"Here's what I learned about {topic}:",
                f"3 insights from working with {topic}:",
                f"The {topic} lesson I wish I knew earlier:",
                f"Why {topic} matters more than you think:"
            ],
            "story": [
                f"Last week, I had a revelation about {topic}.",
                f"A conversation about {topic} changed my perspective.",
                f"After months of working on {topic}, here's what surprised me:",
                f"I used to think {topic} was simple. I was wrong."
            ],
            "list": [
                f"5 {topic} lessons I wish I knew earlier:",
                f"The essential {topic} guide:",
                f"Every {topic} expert knows these principles:",
                f"Here's how to master {topic}:"
            ]
        }
        
        import random
        return random.choice(hooks.get(style, hooks["default"]))
    
    def _generate_insight(self, topic: str, similar_posts: List[Dict], format: str = "detailed") -> str:
        """Generate the main insight or content."""
        if format == "concise":
            return f"The key to successful {topic} is focusing on value over complexity.\n\nMost people overcomplicate it, but the best results come from simple, consistent execution."
        else:
            return f"Through working on {topic}, I've discovered that the fundamentals matter most.\n\nWhile it's tempting to chase the latest trends and complex strategies, the highest impact comes from mastering the basics and executing them consistently."
    
    def _generate_story_content(self, topic: str, similar_posts: List[Dict]) -> str:
        """Generate story content for narrative posts."""
        return f"We were struggling with {topic} on our latest project. Despite having all the right tools and processes, something wasn't clicking.\n\nThen our team lead suggested a different approach. Instead of focusing on the technical details, we stepped back and asked: 'What outcome are we really trying to achieve?'\n\nThat simple shift in perspective changed everything."
    
    def _generate_lesson(self, topic: str, similar_posts: List[Dict]) -> str:
        """Generate the lesson or takeaway."""
        return f"The lesson: {topic} isn't just about execution—it's about clarity of purpose.\n\nWhen you're clear on the 'why,' the 'how' becomes much easier to figure out."
    
    def _generate_key_points(self, topic: str, similar_posts: List[Dict]) -> str:
        """Generate key points for list/carousel format."""
        points = [
            f"1. Start with the fundamentals of {topic}",
            f"2. Focus on consistent execution over perfection",
            f"3. Measure what matters most",
            f"4. Learn from others who've succeeded",
            f"5. Adapt based on real feedback"
        ]
        return "\n\n".join(points)
    
    def _generate_summary(self, topic: str, points: str) -> str:
        """Generate summary for carousel posts."""
        return f"Master these {topic} principles, and you'll be ahead of 90% of people in your field."
    
    def _generate_cta(self, topic: str, cta_type: str = "question") -> str:
        """Generate call-to-action."""
        ctas = {
            "question": [
                f"What's your biggest {topic} challenge?",
                f"Which of these {topic} insights resonates most?",
                f"What would you add to this {topic} list?"
            ],
            "engagement": [
                f"Share your {topic} experience in the comments.",
                f"Tag someone who needs to see this {topic} advice.",
                f"What's your {topic} success story?"
            ],
            "share": [
                f"Save this {topic} guide for later.",
                f"Share if this {topic} framework helps.",
                f"Which {topic} tip will you try first?"
            ]
        }
        
        import random
        return random.choice(ctas.get(cta_type, ctas["question"]))
    
    def _analyze_hooks(self, similar_posts: List[Dict]) -> List[str]:
        """Analyze hooks from similar posts."""
        hooks = []
        for post in similar_posts:
            body = post.get('body', '')
            # Extract first line as potential hook
            first_line = body.split('\n')[0].strip()
            if first_line and len(first_line) < 100:
                hooks.append(first_line)
        return hooks
    
    def _extract_cta(self, content: str) -> str:
        """Extract or identify the CTA from content."""
        lines = content.split('\n')
        # Look for question marks or common CTA patterns in the last few lines
        for line in reversed(lines[-3:]):
            if '?' in line and len(line.strip()) > 10:
                return line.strip()
        
        # Default CTA if none found
        return "What are your thoughts?"
    
    def _extract_tags(self, topic: str, insights: Dict[str, Any]) -> List[str]:
        """Extract or suggest relevant tags."""
        # Start with topic-derived tags
        topic_words = topic.lower().split()
        base_tags = [word for word in topic_words if len(word) > 3]
        
        # Add common tags from insights
        common_tags = insights.get('common_tags', [])
        
        # Combine and deduplicate
        all_tags = list(set(base_tags + common_tags))
        
        # Add some default professional tags
        default_tags = ['linkedin', 'professional', 'insights']
        for tag in default_tags:
            if tag not in all_tags:
                all_tags.append(tag)
        
        return all_tags[:5]  # Limit to 5 tags
    
    def _generate_title(self, topic: str, format_type: str) -> str:
        """Generate a title for the post."""
        format_prefixes = {
            'short': 'Quick insight:',
            'story': 'Story:',
            'carousel': 'Guide:'
        }
        
        prefix = format_prefixes.get(format_type, '')
        
        # Capitalize topic properly
        topic_title = ' '.join(word.capitalize() for word in topic.split())
        
        return f"{prefix} {topic_title}".strip()


class ZeroShotPrompting:
    """
    Utility class for zero-shot prompting to generate LinkedIn posts.
    """

    def __init__(self, model):
        """
        Initialize with a pre-trained language model.

        Args:
            model: Pre-trained language model (e.g., OpenAI GPT, Hugging Face model).
        """
        self.model = model

    def generate_post(self, topic: str, format_type: str) -> str:
        """
        Generate a LinkedIn post using zero-shot prompting.

        Args:
            topic: The topic for the post.
            format_type: The format type (e.g., short, story, carousel).

        Returns:
            Generated post as a string.
        """
        prompt = (
            f"You are an expert LinkedIn content creator. Generate a {format_type} post about '{topic}'.\n"
            "Ensure the post is engaging, professional, and follows LinkedIn best practices."
        )

        # Simulate model response (replace with actual model call in production)
        response = self.model.generate(prompt)
        return response


class OneShotPrompting:
    """
    Utility class for one-shot prompting to generate LinkedIn posts.
    """

    def __init__(self, model):
        """
        Initialize with a pre-trained language model.

        Args:
            model: Pre-trained language model (e.g., OpenAI GPT, Hugging Face model).
        """
        self.model = model

    def generate_post(self, topic: str, format_type: str, example: str) -> str:
        """
        Generate a LinkedIn post using one-shot prompting.

        Args:
            topic: The topic for the post.
            format_type: The format type (e.g., short, story, carousel).
            example: An example post to guide the model.

        Returns:
            Generated post as a string.
        """
        prompt = (
            f"You are an expert LinkedIn content creator. Here is an example of a {format_type} post:\n"
            f"Example: {example}\n\n"
            f"Now, generate a similar {format_type} post about '{topic}'.\n"
            "Ensure the post is engaging, professional, and follows LinkedIn best practices."
        )

        # Simulate model response (replace with actual model call in production)
        response = self.model.generate(prompt)
        return response


class MultiShotPrompting:
    """
    Utility class for multi-shot prompting to generate LinkedIn posts.
    """

    def __init__(self, model):
        """
        Initialize with a pre-trained language model.

        Args:
            model: Pre-trained language model (e.g., OpenAI GPT, Hugging Face model).
        """
        self.model = model

    def generate_post(self, topic: str, format_type: str, examples: List[str]) -> str:
        """
        Generate a LinkedIn post using multi-shot prompting.

        Args:
            topic: The topic for the post.
            format_type: The format type (e.g., short, story, carousel).
            examples: A list of example posts to guide the model.

        Returns:
            Generated post as a string.
        """
        examples_text = "\n\n".join([f"Example {i+1}: {example}" for i, example in enumerate(examples)])
        prompt = (
            f"You are an expert LinkedIn content creator. Here are some examples of {format_type} posts:\n"
            f"{examples_text}\n\n"
            f"Now, generate a similar {format_type} post about '{topic}'.\n"
            "Ensure the post is engaging, professional, and follows LinkedIn best practices."
        )

        # Simulate model response (replace with actual model call in production)
        response = self.model.generate(prompt)
        return response

# Example usage (replace 'model' with an actual pre-trained model instance)
# multi_shot = MultiShotPrompting(model)
# example_posts = [
#     "AI is transforming marketing by enabling personalized campaigns.",
#     "Data-driven insights are the key to successful marketing strategies."
# ]
# post = multi_shot.generate_post("AI in Marketing", "story", example_posts)
# print(post)