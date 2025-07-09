"""
OpenAI client for content analysis and generation
"""

from openai import AsyncOpenAI
from typing import List, Dict, Any
import json

from config import settings
from models import Article, AnalyzedArticle, NewsletterConfig


class OpenAIClient:
    """Client for OpenAI API"""

    def __init__(self):
        self.client = None

    async def initialize(self):
        """Initialize the OpenAI client"""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def analyze_article(
        self, article: Article, user_preferences, available_sections: List[str]
    ) -> Dict[str, Any]:
        """Analyze an article for relevance, sentiment, and section assignment"""
        try:
            prompt = f"""
            Analyze this article for relevance to responsible AI, AI ethics, and AI governance:
            
            Title: {article.title}
            Summary: {article.summary}
            Source: {article.source}
            
            Available sections: {', '.join(available_sections)}
            
            Return ONLY a JSON object with this exact format:
            {{
                "relevance_score": 0.8,
                "sentiment": "positive",
                "impact_score": 7,
                "urgency_score": 6,
                "best_section": "Compliance & Risk Watch",
                "explanation": "Brief explanation"
            }}
            
            - relevance_score: 0.0-1.0 (how relevant to responsible AI/governance)
            - sentiment: "positive", "negative", or "neutral"
            - impact_score: 1-10 (potential business/industry impact)
            - urgency_score: 1-10 (how urgent/time-sensitive)
            - best_section: choose the most appropriate section from the list
            """

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI analyst. Return only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            print(f"Error analyzing article: {e}")
            # Return default values
            return {
                "relevance_score": 0.5,
                "sentiment": "neutral",
                "impact_score": 5,
                "urgency_score": 5,
                "best_section": (
                    available_sections[0] if available_sections else "General"
                ),
                "explanation": "Analysis failed",
            }

    async def generate_section_content(
        self,
        section_name: str,
        articles: List[AnalyzedArticle],
        config: NewsletterConfig,
    ) -> str:
        """Generate content for a newsletter section"""
        try:
            articles_text = "\n\n".join(
                [
                    f"Title: {article.article.title}\n"
                    f"Source: {article.article.source}\n"
                    f"URL: {article.article.url}\n"
                    f"Summary: {article.article.summary}\n"
                    f"Relevance: {article.relevance_score:.2f}\n"
                    f"Impact: {article.impact_score}/10"
                    for article in articles[:5]  # Limit to top 5
                ]
            )

            prompt = f"""
            Generate content for the "{section_name}" section of an AI newsletter.
            
            Articles:
            {articles_text}
            
            Format: {config.template}
            Include links: {config.include_links}
            
            Create a well-structured section with:
            - Brief section introduction
            - 2-4 key highlights with proper formatting
            - Include clickable links where mentioned
            - Keep it professional and concise
            
            Return only the formatted section content (no JSON, just the text).
            """

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional newsletter writer.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error generating section content: {e}")
            return f"**{section_name}**\n\nContent generation failed for this section."
