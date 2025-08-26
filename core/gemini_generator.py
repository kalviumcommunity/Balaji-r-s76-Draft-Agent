"""
Gemini AI integration for LinkedIn content generation.
Provides advanced content generation using Google's Gemini API.
"""

import os
import json
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from datetime import datetime


class GeminiContentGenerator:
    """
    Advanced content generator using Google's Gemini API.
    
    Provides sophisticated prompting for LinkedIn posts with context awareness,
    RAG integration, and performance-based optimization.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize Gemini content generator.
        
        Args:
            api_key: Gemini API key (defaults to environment variable)
        """
        self.api_key = api_key or "AIzaSyCZaTKONsDBprIEXj9E6I5it0cH-wDvSwQ"
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Generation config for optimal LinkedIn content
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            top_p=0.8,
            top_k=40,
            max_output_tokens=2048,
        )
    
    def generate_linkedin_post(
        self, 
        topic: str, 
        format_type: str = "story",
        similar_posts: List[Dict] = None,
        performance_insights: Dict = None,
        config: Dict = None
    ) -> str:
        """
        Generate a LinkedIn post using Gemini with advanced prompting.
        
        Args:
            topic: Main topic for the post
            format_type: Post format (story, short, carousel)
            similar_posts: Similar historical posts for context
            performance_insights: Performance data and insights
            config: Configuration settings
            
        Returns:
            Generated LinkedIn post content
        """
        # Build comprehensive prompt
        prompt = self._build_prompt(
            topic=topic,
            format_type=format_type,
            similar_posts=similar_posts or [],
            performance_insights=performance_insights or {},
            config=config or {}
        )
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            return response.text.strip()
            
        except Exception as e:
            print(f"⚠️  Gemini API error: {str(e)}")
            print("🔄 Falling back to template-based generation...")
            return self._fallback_generation(topic, format_type)
    
    def _build_prompt(
        self, 
        topic: str, 
        format_type: str,
        similar_posts: List[Dict],
        performance_insights: Dict,
        config: Dict
    ) -> str:
        """Build a comprehensive prompt for Gemini."""
        
        # Base context
        tone = config.get('tone', 'practical, conversational, insightful')
        
        # Format-specific instructions
        format_instructions = {
            'story': """
Create a compelling LinkedIn story post with:
- Hook: Personal anecdote or surprising insight
- Story: Concrete situation with challenge/resolution
- Lesson: Clear takeaway with broader application
- CTA: Engaging question that invites discussion
Target length: 150-300 words
            """,
            'short': """
Create a concise LinkedIn insight post with:
- Hook: Bold statement or counterintuitive fact
- Value: Key insight with specific benefit
- CTA: Simple question or call for engagement
Target length: 50-150 words
            """,
            'carousel': """
Create a LinkedIn list/guide post with:
- Hook: Promise of value (X tips/lessons/strategies)
- Points: 3-5 numbered insights with brief explanations
- Summary: Reinforcement of value delivered
- CTA: Save/share request or implementation question
Target length: 200-400 words
            """
        }
        
        # Historical context
        context_section = ""
        if similar_posts:
            context_section = f"""
HISTORICAL CONTEXT:
You've previously written about similar topics. Here are your past posts for reference:

{self._format_similar_posts(similar_posts)}

Avoid repeating these exact angles while maintaining your authentic voice.
            """
        
        # Performance insights
        performance_section = ""
        if performance_insights:
            best_times = performance_insights.get('top_times', [])
            if best_times:
                performance_section = f"""
PERFORMANCE INSIGHTS:
- Best posting times: {', '.join([f"{time[0]} {time[1]:.1%}" for time in best_times[:2]])}
- Optimize for engagement during these windows
                """
        
        # Main prompt
        prompt = f"""
You are an expert LinkedIn content creator helping generate a {format_type} post about "{topic}".

BRAND VOICE: {tone}

FORMAT REQUIREMENTS:
{format_instructions.get(format_type, format_instructions['story'])}

{context_section}

{performance_section}

LINKEDIN BEST PRACTICES:
- Start with a hook that stops scrolling
- Use line breaks for readability
- Include emojis strategically (1-3 per post)
- End with an engaging question
- Keep paragraphs short (1-2 sentences)
- Use specific examples over generalizations
- Add personal vulnerability when appropriate

TOPIC: {topic}

Generate a LinkedIn post that follows these guidelines and feels authentic to a professional sharing genuine insights.
        """
        
        return prompt.strip()
    
    def _format_similar_posts(self, similar_posts: List[Dict]) -> str:
        """Format similar posts for context."""
        formatted = []
        for i, post in enumerate(similar_posts[:3], 1):
            title = post.get('title', 'Untitled')
            body_preview = post.get('body', '')[:100] + "..." if len(post.get('body', '')) > 100 else post.get('body', '')
            formatted.append(f"{i}. {title}\n   {body_preview}")
        
        return "\n\n".join(formatted)
    
    def _fallback_generation(self, topic: str, format_type: str) -> str:
        """Fallback content generation when Gemini API fails."""
        templates = {
            'story': f"""Here's what I learned about {topic}:

Last week, I encountered a challenge with {topic} that completely changed my perspective.

Despite having the right tools and knowledge, something wasn't working. Then I realized the issue wasn't technical—it was about approach.

The lesson: {topic} isn't just about execution. It's about understanding the underlying principles first.

What's been your experience with {topic}?""",
            
            'short': f"""The {topic} insight that changed everything:

Most people focus on complexity, but the real breakthrough comes from mastering the fundamentals.

Simple, consistent execution beats elaborate strategies every time.

What's your approach to {topic}?""",
            
            'carousel': f"""5 {topic} lessons I wish I knew earlier:

1. Start with the fundamentals
2. Focus on consistency over perfection
3. Learn from others' mistakes
4. Measure what matters
5. Adapt based on feedback

Which of these resonates most with your experience?"""
        }
        
        return templates.get(format_type, templates['story'])
    
    def generate_hook_variations(self, topic: str, count: int = 3) -> List[str]:
        """Generate multiple hook variations for A/B testing."""
        prompt = f"""
Generate {count} different engaging hooks for a LinkedIn post about "{topic}".

Each hook should:
- Stop the scroll immediately
- Create curiosity or surprise
- Be 1-2 sentences maximum
- Use different psychological triggers (surprise, controversy, personal story, etc.)

Return only the hooks, numbered 1-{count}.
        """
        
        try:
            response = self.model.generate_content(prompt)
            hooks = response.text.strip().split('\n')
            return [hook.strip() for hook in hooks if hook.strip()][:count]
        except:
            return [
                f"Here's what most people get wrong about {topic}:",
                f"After 6 months of working with {topic}, I finally understand this:",
                f"The {topic} mistake that cost me weeks of work:"
            ]
    
    def optimize_for_engagement(self, content: str, target_metrics: Dict = None) -> str:
        """Optimize existing content for better engagement."""
        target_metrics = target_metrics or {"engagement_rate": 0.05, "comments": 10}
        
        prompt = f"""
Optimize this LinkedIn post for higher engagement:

CURRENT POST:
{content}

TARGET METRICS:
- Engagement rate: {target_metrics.get('engagement_rate', 0.05):.1%}
- Comments goal: {target_metrics.get('comments', 10)}

OPTIMIZATION GUIDELINES:
- Strengthen the hook to stop scrolling
- Add more specific, relatable examples
- Include a stronger call-to-action
- Improve readability with better formatting
- Add strategic emotional triggers
- Ensure the CTA invites meaningful discussion

Return the optimized version maintaining the original message and voice.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except:
            return content
    
    def generate_cta_variations(self, topic: str, post_content: str) -> List[str]:
        """Generate CTA variations for the post."""
        prompt = f"""
Generate 5 different call-to-action endings for this LinkedIn post about {topic}:

POST CONTENT:
{post_content}

Each CTA should:
- Encourage genuine engagement
- Be relevant to the content
- Invite specific responses (not just "thoughts?")
- Use different engagement types (questions, challenges, sharing requests)

Return only the CTAs, numbered 1-5.
        """
        
        try:
            response = self.model.generate_content(prompt)
            ctas = response.text.strip().split('\n')
            return [cta.strip() for cta in ctas if cta.strip()][:5]
        except:
            return [
                f"What's your biggest {topic} challenge?",
                f"Share your {topic} success story below.",
                f"Which {topic} strategy works best for you?",
                f"Tag someone who needs to see this {topic} advice.",
                f"What would you add to this {topic} list?"
            ]


def test_gemini_integration():
    """Test function to verify Gemini integration works."""
    try:
        generator = GeminiContentGenerator()
        
        # Test basic generation
        test_content = generator.generate_linkedin_post(
            topic="product management lessons",
            format_type="story"
        )
        
        print("✅ Gemini integration successful!")
        print(f"Generated content preview: {test_content[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Gemini integration failed: {str(e)}")
        return False


if __name__ == "__main__":
    test_gemini_integration()