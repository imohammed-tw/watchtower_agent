"""
Content Agent - Handles data collection and validation
"""

from typing import List, Any
from datetime import datetime, timedelta
import asyncio

from agents.base_agent import BaseAgent
from models import WorkflowState, Article, NewsletterFormat
from tools.perplexity_client import PerplexityClient
from tools.content_processor import ContentProcessor


class ContentAgent(BaseAgent):
    """Content collection and validation agent"""

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

            # 3. Remove duplicates and validate
            unique_articles = await self.content_processor.remove_duplicates(
                all_articles
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

    async def _generate_topics(self, workflow_state: WorkflowState) -> List[str]:
        """Generate personalized search topics"""
        preferences = workflow_state.user_preferences
        config = workflow_state.newsletter_config

        topics = []

        # Base topics for AI governance and responsible AI
        base_topics = [
            "AI governance regulations",
            "responsible AI developments",
            "AI compliance updates",
            "AI ethics guidelines",
            "AI policy updates",
        ]

        # Add user keyword-based topics
        for keyword in preferences.keywords:
            topics.extend(
                [
                    f"{keyword} AI regulations",
                    f"{keyword} responsible AI",
                    f"{keyword} AI governance",
                ]
            )

        # Add industry-specific topics
        for industry in preferences.industry_focus:
            topics.extend(
                [f"AI applications in {industry}", f"{industry} AI compliance"]
            )

        #  Add date range context for search - FIX: Use .value for enum
        if config.date_range:
            date_context = f" {config.format.value} updates"  # ✅ Fixed: use .value
        else:
            date_context = f" recent {config.format.value} news"  # ✅ Fixed: use .value

        # Append date context to topics
        topics = [topic + date_context for topic in (topics + base_topics)]

        return list(set(topics))  # Remove duplicates
