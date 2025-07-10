"""
Perplexity API client for content collection
"""

import httpx
from typing import List, Dict, Any
from datetime import datetime, timedelta
import json
import os
from config import settings
from models import (
    Article,
    NewsletterConfig,
    UserPreferences,
    NewsletterFormat,
)  # Add NewsletterFormat


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

    # File: app/tools/perplexity_client.py - ENHANCED VERSION

    def _build_search_prompt(
        self, topic: str, config: NewsletterConfig, preferences: UserPreferences
    ) -> str:
        """Build search prompt for Perplexity - ENHANCED"""

        # 🔧 FIX: Build precise date range for search
        date_range = ""
        if config.date_range:
            start_date = config.date_range.get("start")
            end_date = config.date_range.get("end")
            date_range = f" published between {start_date} and {end_date}"

        # 🔧 FIX: Add time-specific context
        time_context = ""
        if config.format == NewsletterFormat.DAILY:
            time_context = " from today or yesterday"
        elif config.format == NewsletterFormat.WEEKLY:
            time_context = " from the past 7 days"
        elif config.format == NewsletterFormat.MONTHLY:
            time_context = " from the past 30 days"

        preferred_sources = ""
        if preferences.preferred_sources:
            preferred_sources = (
                f"Prioritize sources: {', '.join(preferences.preferred_sources[:5])}"
            )

        # 🔧 FIX: Enhanced prompt with strict date requirements
        prompt = f"""
        Find 10 recent news articles about: {topic}{date_range}{time_context}
        
        REQUIREMENTS:
        - Articles must be from the specified date range
        - Focus on: AI governance, responsible AI, AI ethics, AI regulations, compliance
        - Only include articles with publication dates
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
        
        IMPORTANT: Only include articles that are genuinely recent and match the date requirements.
        """

        return prompt

    async def _mock_search_articles(
        self, topic: str, config: NewsletterConfig, preferences: UserPreferences
    ) -> List[Article]:
        """Return mock articles for testing - ENHANCED with proper dates"""
        print(f"🔧 Using mock data for topic: '{topic}'")

        # 🔧 FIX: Generate mock articles with proper recent dates
        from datetime import datetime, timedelta
        import random

        # Calculate date range based on format
        end_date = datetime.utcnow()
        if config.format == NewsletterFormat.DAILY:
            start_date = end_date - timedelta(days=1)
        elif config.format == NewsletterFormat.WEEKLY:
            start_date = end_date - timedelta(days=7)
        else:
            start_date = end_date - timedelta(days=30)

        mock_articles = []
        for i in range(3):
            # Random date within the range
            random_days = random.randint(0, (end_date - start_date).days)
            article_date = start_date + timedelta(days=random_days)

            mock_articles.append(
                Article(
                    title=f"Latest {topic[:40]} Development - {article_date.strftime('%B %d')}",
                    url=f"https://techcrunch.com/mock-article-{i+1}",
                    source="TechCrunch",
                    summary=f"Breaking news on {topic} published {article_date.strftime('%B %d, %Y')}. This article covers recent developments and industry impact.",
                    topic=topic,
                    published_at=article_date,  # 🔧 FIX: Proper date
                    quality_score=0.8,
                )
            )

        return mock_articles

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
