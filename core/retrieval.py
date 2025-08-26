"""
RAG (Retrieval-Augmented Generation) module for LinkedIn AI agent.
Handles retrieval of similar past posts to ground new content generation.
"""

import json
import os
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from datetime import datetime
import re


class PostRetriever:
    """
    Retrieves and ranks past posts for content grounding using semantic similarity.
    
    Uses sentence transformers to find similar content from historical posts
    to inform new draft generation and avoid repetition.
    """
    
    def __init__(self, posts_dir: str = "data/posts", model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the post retriever with embedding model.
        
        Args:
            posts_dir: Directory containing historical posts
            model_name: Sentence transformer model for embeddings
        """
        self.posts_dir = posts_dir
        self.model = SentenceTransformer(model_name)
        self.posts = self._load_posts()
        self.embeddings = self._compute_embeddings()
    
    def _load_posts(self) -> List[Dict[str, Any]]:
        """Load all historical posts from the posts directory."""
        all_posts = []
        
        if not os.path.exists(self.posts_dir):
            return all_posts
        
        for filename in os.listdir(self.posts_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(self.posts_dir, filename), 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            all_posts.extend(data)
                        else:
                            all_posts.append(data)
                except (json.JSONDecodeError, FileNotFoundError):
                    continue
        
        return all_posts
    
    def _compute_embeddings(self) -> np.ndarray:
        """Compute embeddings for all posts."""
        if not self.posts:
            return np.array([])
        
        # Combine title and body for embedding
        texts = []
        for post in self.posts:
            title = post.get('title', '')
            body = post.get('body', '')
            combined_text = f"{title} {body}"
            texts.append(combined_text)
        
        return self.model.encode(texts)
    
    def retrieve_similar(self, query: str, top_k: int = 3, min_similarity: float = 0.3) -> List[Dict[str, Any]]:
        """
        Retrieve similar posts based on semantic similarity to query.
        
        Args:
            query: Search query or topic description
            top_k: Number of similar posts to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar posts with similarity scores and reasons
        """
        if not self.posts or len(self.embeddings) == 0:
            return []
        
        # Encode the query
        query_embedding = self.model.encode([query])
        
        # Calculate similarities
        similarities = np.dot(self.embeddings, query_embedding.T).flatten()
        similarities = similarities / (np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding))
        
        # Get top-k similar posts above threshold
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] >= min_similarity:
                post = self.posts[idx].copy()
                post['similarity_score'] = float(similarities[idx])
                post['reason'] = self._generate_similarity_reason(query, post, similarities[idx])
                results.append(post)
        
        return results
    
    def _generate_similarity_reason(self, query: str, post: Dict[str, Any], score: float) -> str:
        """Generate a human-readable reason for why a post is similar."""
        if score > 0.7:
            return f"Very similar topic and content approach (score: {score:.2f})"
        elif score > 0.5:
            return f"Related topic with overlapping themes (score: {score:.2f})"
        elif score > 0.3:
            return f"Similar context or audience interest (score: {score:.2f})"
        else:
            return f"Weak similarity (score: {score:.2f})"
    
    def get_top_performing_posts(self, metrics_dir: str = "data/metrics", top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Get top-performing posts based on engagement metrics.
        
        Args:
            metrics_dir: Directory containing metrics data
            top_k: Number of top posts to return
            
        Returns:
            List of top-performing posts with engagement data
        """
        # Load metrics
        all_metrics = []
        if os.path.exists(metrics_dir):
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
        
        # Calculate engagement rates and match with posts
        post_performance = {}
        for metric in all_metrics:
            post_id = metric.get('post_id')
            if post_id:
                total_interactions = (
                    metric.get('reactions', 0) + 
                    metric.get('comments', 0) + 
                    metric.get('shares', 0)
                )
                impressions = metric.get('impressions', 1)
                engagement_rate = total_interactions / impressions if impressions > 0 else 0
                post_performance[post_id] = {
                    'engagement_rate': engagement_rate,
                    'total_interactions': total_interactions,
                    'impressions': impressions
                }
        
        # Match posts with performance data
        posts_with_metrics = []
        for post in self.posts:
            post_id = post.get('id')
            if post_id in post_performance:
                enhanced_post = post.copy()
                enhanced_post.update(post_performance[post_id])
                posts_with_metrics.append(enhanced_post)
        
        # Sort by engagement rate
        posts_with_metrics.sort(key=lambda p: p.get('engagement_rate', 0), reverse=True)
        
        return posts_with_metrics[:top_k]
    
    def find_by_tags(self, tags: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find posts that contain any of the specified tags.
        
        Args:
            tags: List of tags to search for
            limit: Maximum number of posts to return
            
        Returns:
            List of posts matching the tags
        """
        matching_posts = []
        
        for post in self.posts:
            post_tags = post.get('tags', [])
            if any(tag.lower() in [pt.lower() for pt in post_tags] for tag in tags):
                matching_posts.append(post)
        
        return matching_posts[:limit]
    
    def extract_key_phrases(self, text: str) -> List[str]:
        """
        Extract key phrases from text for topic analysis.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of key phrases
        """
        # Simple keyword extraction (in a full implementation, use more sophisticated NLP)
        # Remove common words and extract meaningful phrases
        text = text.lower()
        
        # Remove punctuation and split
        words = re.findall(r'\b\w+\b', text)
        
        # Filter out common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Return most frequent non-stop words
        from collections import Counter
        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(10)]
    
    def get_content_insights(self, topic: str) -> Dict[str, Any]:
        """
        Get insights about past content related to a topic.
        
        Args:
            topic: Topic to analyze
            
        Returns:
            Dictionary with content insights and recommendations
        """
        similar_posts = self.retrieve_similar(topic, top_k=10, min_similarity=0.2)
        
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
        
        from collections import Counter
        common_tags = [tag for tag, count in Counter(all_tags).most_common(5)]
        
        # Calculate average similarity
        avg_similarity = sum(post['similarity_score'] for post in similar_posts) / len(similar_posts)
        
        # Generate recommendations
        recommendations = []
        if avg_similarity > 0.6:
            recommendations.append("You've covered similar ground before - consider a fresh angle")
        elif avg_similarity > 0.4:
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
                    'similarity': post['similarity_score']
                }
                for post in similar_posts[:3]
            ]
        }