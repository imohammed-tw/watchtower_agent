# File: app/agents/content_agent.py - FIXED VERSION

"""
Content Agent - Handles data collection and validation - FIXED
"""

from typing import List, Any
from datetime import datetime, timedelta
import asyncio

from agents.base_agent import BaseAgent
from models import WorkflowState, Article, NewsletterFormat
from tools.perplexity_client import PerplexityClient
from tools.content_processor import ContentProcessor


class ContentAgent(BaseAgent):
    """Content collection and validation agent - FIXED"""

    def __init__(self):
        super().__init__("ContentAgent")
        self.perplexity_client = None
        self.content_processor = None

    async def initialize(self):
        """Initialize content agent resources"""
        await super().initialize()
        self.perplexity_client = PerplexityClient()
        self.content_processor = ContentProcessor()

        await asyncio.gather(
            self.perplexity_client.initialize(), self.content_processor.initialize()
        )

    async def execute(
        self, input_data: Any, workflow_state: WorkflowState
    ) -> List[Article]:
        """Execute content collection workflow"""
        self.last_execution = datetime.utcnow()

        try:
            self.logger.info(
                f"Starting content collection for user {workflow_state.user_id}"
            )

            # 🔧 FIX: Ensure proper date range is set
            config = workflow_state.newsletter_config
            if not config.date_range:
                config.date_range = self._calculate_date_range(config.format)
                print(
                    f"🔧 Setting date range for {config.format.value}: {config.date_range}"
                )

            # 1. Generate personalized topics
            topics = await self._generate_topics(workflow_state)
            self.logger.info(f"Generated {len(topics)} search topics")

            # 2. Collect articles from sources
            all_articles = []
            for topic in topics:
                try:
                    articles = await self.perplexity_client.search_articles(
                        topic,
                        workflow_state.newsletter_config,
                        workflow_state.user_preferences,
                    )
                    all_articles.extend(articles)
                except Exception as e:
                    self.logger.error(f"Error collecting for topic '{topic}': {e}")

            # 3. 🔧 FIX: Filter articles by date range STRICTLY
            date_filtered_articles = self._filter_by_date_range(all_articles, config)
            print(
                f"🔧 Date filtering: {len(all_articles)} -> {len(date_filtered_articles)} articles"
            )

            # 4. Remove duplicates and validate
            unique_articles = await self.content_processor.remove_duplicates(
                date_filtered_articles
            )
            validated_articles = await self.content_processor.validate_articles(
                unique_articles, workflow_state.user_preferences
            )

            self.logger.info(
                f"Content collection complete: {len(validated_articles)} articles"
            )
            return validated_articles

        except Exception as e:
            self.logger.error(f"Content collection failed: {e}")
            raise

    def _calculate_date_range(self, format_type: NewsletterFormat) -> dict:
        """Calculate proper date range based on format"""
        end_date = datetime.utcnow()

        if format_type == NewsletterFormat.DAILY:
            start_date = end_date - timedelta(days=1)
            print(f"📅 Daily: Looking for articles from last 24 hours")
        elif format_type == NewsletterFormat.WEEKLY:
            start_date = end_date - timedelta(days=7)
            print(f"📅 Weekly: Looking for articles from last 7 days")
        elif format_type == NewsletterFormat.MONTHLY:
            start_date = end_date - timedelta(days=30)
            print(f"📅 Monthly: Looking for articles from last 30 days")
        else:
            start_date = end_date - timedelta(days=7)  # Default

        return {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
        }

    def _filter_by_date_range(self, articles: List[Article], config) -> List[Article]:
        """Filter articles by date range"""
        if not config.date_range:
            return articles

        try:
            start_date = datetime.strptime(config.date_range["start"], "%Y-%m-%d")
            end_date = datetime.strptime(config.date_range["end"], "%Y-%m-%d")

            filtered_articles = []
            for article in articles:
                if article.published_at:
                    if start_date <= article.published_at <= end_date:
                        filtered_articles.append(article)
                else:
                    # If no published date, assume it's recent
                    filtered_articles.append(article)

            return filtered_articles
        except Exception as e:
            print(f"⚠️ Date filtering error: {e}, returning all articles")
            return articles

    async def _generate_topics(self, workflow_state: WorkflowState) -> List[str]:
        """Generate personalized search topics - ENHANCED"""
        preferences = workflow_state.user_preferences
        config = workflow_state.newsletter_config

        topics = []

        # 🔧 FIX: Use user keywords as primary topics
        if preferences.keywords:
            print(f"🎯 Using user keywords: {preferences.keywords}")
            for keyword in preferences.keywords:
                topics.extend(
                    [
                        f"{keyword} AI",
                        f"{keyword} regulations",
                        f"{keyword} developments",
                        f"{keyword} news",
                    ]
                )
        else:
            # Default AI governance topics
            base_topics = [
                "AI governance regulations",
                "responsible AI developments",
                "AI compliance updates",
                "AI ethics guidelines",
                "AI policy updates",
            ]
            topics.extend(base_topics)

        # Add industry-specific topics
        for industry in preferences.industry_focus:
            topics.extend(
                [
                    f"AI applications in {industry}",
                    f"{industry} AI compliance",
                    f"{industry} AI developments",
                ]
            )

        # 🔧 FIX: Add proper date context for recency
        date_context = self._get_date_context(config.format)
        topics = [f"{topic} {date_context}" for topic in topics]

        # Remove duplicates and limit
        unique_topics = list(set(topics))[:10]  # Limit to 10 topics
        print(f"🔍 Generated topics: {unique_topics}")

        return unique_topics

    def _get_date_context(self, format_type: NewsletterFormat) -> str:
        """Get appropriate date context for search"""
        if format_type == NewsletterFormat.DAILY:
            return "today latest"
        elif format_type == NewsletterFormat.WEEKLY:
            return "this week latest"
        elif format_type == NewsletterFormat.MONTHLY:
            return "this month latest"
        else:
            return "recent latest"
