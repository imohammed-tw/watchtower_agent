"""
Perplexity API client for content collection
"""

import httpx
from typing import List, Dict, Any
from datetime import datetime, timedelta
import json
import os
from config import settings
from models import Article, NewsletterConfig, UserPreferences


class PerplexityClient:
    """Client for Perplexity API"""

    def __init__(self):

        print(
            f"🔍 DEBUG: Perplexity API key from settings: '{settings.perplexity_api_key}'"
        )
        print(
            f"🔍 DEBUG: API key length: {len(settings.perplexity_api_key) if settings.perplexity_api_key else 0}"
        )
        print(f"🔍 DEBUG: API key type: {type(settings.perplexity_api_key)}")

        # Check environment directly
        env_key = os.getenv("PERPLEXITY_API_KEY")
        print(f"🔍 DEBUG: Direct from env: '{env_key}'")
        print(f"🔍 DEBUG: Direct env length: {len(env_key) if env_key else 0}")

        self.api_key = settings.perplexity_api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.client = None

        # Check if API key is valid
        if (
            not self.api_key
            or self.api_key.strip() == ""
            or self.api_key == "your-perplexity-api-key-here"
        ):
            print("❌ WARNING: Perplexity API key is missing or invalid!")
            print(
                "   Please check your .env file and make sure PERPLEXITY_API_KEY is set correctly"
            )
            self.use_mock = True
        else:
            print(f"✅ Perplexity API key loaded: {self.api_key[:10]}...")
            self.use_mock = False

    async def initialize(self):
        """Initialize the client"""
        if self.use_mock:
            print("🔧 Using MOCK mode due to missing/invalid API key")
            return

        try:
            self.client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
            print("✅ Perplexity client initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing Perplexity client: {e}")
            self.use_mock = True

    async def search_articles(
        self, topic: str, config: NewsletterConfig, preferences: UserPreferences
    ) -> List[Article]:
        """Search for articles on a specific topic"""

        # Use mock data if API key is missing/invalid
        if self.use_mock:
            return await self._mock_search_articles(topic, config, preferences)

        try:
            # Build search prompt
            prompt = self._build_search_prompt(topic, config, preferences)

            # Validate API key one more time
            if not self.api_key or len(self.api_key.strip()) == 0:
                print("❌ API key is empty at request time!")
                return await self._mock_search_articles(topic, config, preferences)

            # Make API request
            response = await self.client.post(
                self.base_url,
                json={
                    "model": "sonar-pro",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a research assistant. Return only valid JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                },
            )

            print(f"✅ Perplexity response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()

            # Parse response
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            articles = self._parse_articles_response(content, topic)

            print(f"✅ Successfully parsed {len(articles)} articles from Perplexity")
            return articles

        except httpx.HTTPStatusError as e:
            print(
                f"❌ Perplexity HTTP error for '{topic}': {e.response.status_code} - {e.response.text}"
            )
            return await self._mock_search_articles(topic, config, preferences)
        except Exception as e:
            print(f"❌ Error in Perplexity search for '{topic}': {e}")
            print(f"   Error type: {type(e)}")
            return await self._mock_search_articles(topic, config, preferences)

    async def _mock_search_articles(
        self, topic: str, config: NewsletterConfig, preferences: UserPreferences
    ) -> List[Article]:
        """Return mock articles for testing"""
        print(f"🔧 Using mock data for topic: '{topic}'")

        mock_articles = [
            Article(
                title=f"AI Governance Breakthrough: {topic[:40]}",
                url="https://techcrunch.com/mock-article-1",
                source="TechCrunch",
                summary=f"Recent developments in {topic} demonstrate significant progress in AI governance frameworks and responsible AI implementation across industries.",
                topic=topic,
                quality_score=0.8,
            ),
            Article(
                title=f"New Regulatory Framework for {topic[:30]}",
                url="https://wired.com/mock-article-2",
                source="Wired",
                summary=f"Analysis of emerging regulatory standards addressing {topic}, including compliance requirements and industry impact assessments.",
                topic=topic,
                quality_score=0.7,
            ),
            Article(
                title=f"Industry Response to {topic[:35]}",
                url="https://mit.edu/mock-article-3",
                source="MIT Technology Review",
                summary=f"Leading technology companies adapt their practices in response to {topic}, setting new standards for ethical AI development.",
                topic=topic,
                quality_score=0.9,
            ),
        ]

        return mock_articles

    def _build_search_prompt(
        self, topic: str, config: NewsletterConfig, preferences: UserPreferences
    ) -> str:
        """Build search prompt for Perplexity"""
        date_range = ""
        if config.date_range:
            date_range = f" from {config.date_range.get('start')} to {config.date_range.get('end')}"

        preferred_sources = ""
        if preferences.preferred_sources:
            preferred_sources = (
                f"Prioritize sources: {', '.join(preferences.preferred_sources[:5])}"
            )

        prompt = f"""
        Find 10 recent news articles about: {topic}{date_range}
        
        Focus on: AI governance, responsible AI, AI ethics, AI regulations, compliance
        {preferred_sources}
        
        Return ONLY a JSON list with this exact format:
        [
          {{
            "title": "Article Title",
            "url": "https://example.com/article",
            "source": "Source Name",
            "summary": "Brief summary",
            "published_at": "YYYY-MM-DD"
          }}
        ]
        """

        return prompt

    def _parse_articles_response(self, content: str, topic: str) -> List[Article]:
        """Parse articles from Perplexity response"""
        try:
            # Try to parse JSON directly
            articles_data = json.loads(content)

            if not isinstance(articles_data, list):
                return []

            articles = []
            for item in articles_data:
                try:
                    article = Article(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        source=item.get("source", "Unknown"),
                        summary=item.get("summary", ""),
                        topic=topic,
                        published_at=datetime.fromisoformat(
                            item.get("published_at", datetime.utcnow().isoformat())
                        ),
                    )
                    articles.append(article)
                except Exception as e:
                    print(f"Error parsing article: {e}")
                    continue

            return articles

        except json.JSONDecodeError:
            # Fallback: extract URLs manually if JSON parsing fails
            import re

            urls = re.findall(r'https?://[^\s)"\]]+', content)
            return [
                Article(
                    title=f"Article about {topic}",
                    url=url,
                    source="Unknown",
                    summary="Summary not available",
                    topic=topic,
                )
                for url in urls[:10]  # Limit to 10
            ]
