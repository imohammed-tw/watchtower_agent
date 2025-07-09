# File: app/agents/analysis_agent.py
"""
Analysis Agent with enhanced debugging
"""
from typing import List, Any
from datetime import datetime
import asyncio

from agents.base_agent import BaseAgent
from models import WorkflowState, Article, AnalyzedArticle
from tools.openai_client import OpenAIClient


class AnalysisAgent(BaseAgent):
    """Content analysis and intelligence agent with debugging"""

    def __init__(self):
        super().__init__("AnalysisAgent")
        self.openai_client = None

    async def initialize(self):
        """Initialize analysis agent resources"""
        await super().initialize()
        self.openai_client = OpenAIClient()
        await self.openai_client.initialize()
        print("✅ Analysis agent initialized")

    async def execute(
        self, input_data: List[Article], workflow_state: WorkflowState
    ) -> List[AnalyzedArticle]:
        """Execute content analysis workflow with debugging"""
        self.last_execution = datetime.utcnow()

        try:
            articles = input_data
            print(f"🧠 Analysis Agent: Starting analysis of {len(articles)} articles")

            if not articles:
                print("⚠️ No articles to analyze")
                return []

            analyzed_articles = []
            failed_analyses = 0

            # Process articles in batches
            batch_size = 5
            for i in range(0, len(articles), batch_size):
                batch = articles[i : i + batch_size]
                print(
                    f"📝 Processing batch {i//batch_size + 1}/{(len(articles) + batch_size - 1)//batch_size} ({len(batch)} articles)"
                )

                batch_results = await self._process_batch(batch, workflow_state)

                # Count successful vs failed
                successful = len(batch_results)
                failed = len(batch) - successful
                failed_analyses += failed

                analyzed_articles.extend(batch_results)
                print(f"✅ Batch complete: {successful} successful, {failed} failed")

            print(f"📊 Analysis summary:")
            print(f"   Total articles processed: {len(articles)}")
            print(f"   Successful analyses: {len(analyzed_articles)}")
            print(f"   Failed analyses: {failed_analyses}")

            # Filter by relevance threshold
            threshold = workflow_state.user_preferences.relevance_threshold
            print(f"🎯 Applying relevance threshold: {threshold}")

            relevant_articles = []
            for article in analyzed_articles:
                print(
                    f"   '{article.article.title[:40]}...': {article.relevance_score:.2f} {'✅' if article.relevance_score >= threshold else '❌'}"
                )
                if article.relevance_score >= threshold:
                    relevant_articles.append(article)

            print(
                f"📊 Relevance filtering result: {len(relevant_articles)}/{len(analyzed_articles)} articles passed threshold"
            )

            if not relevant_articles:
                print("⚠️ No articles passed relevance threshold!")
                print(
                    f"   Consider lowering threshold from {threshold} to 0.5 or lower"
                )

                # Return top articles anyway for testing
                if analyzed_articles:
                    print("🔧 Returning top 3 articles for testing...")
                    top_articles = sorted(
                        analyzed_articles, key=lambda x: x.relevance_score, reverse=True
                    )[:3]
                    return top_articles

            return relevant_articles

        except Exception as e:
            print(f"❌ Analysis Agent failed: {e}")
            import traceback

            print(f"   Traceback: {traceback.format_exc()}")
            raise

    async def _process_batch(
        self, articles: List[Article], workflow_state: WorkflowState
    ) -> List[AnalyzedArticle]:
        """Process a batch of articles with debugging"""
        analyzed_articles = []

        for i, article in enumerate(articles, 1):
            try:
                print(f"   Analyzing {i}/{len(articles)}: {article.title[:50]}...")

                # Analyze article using OpenAI
                analysis_result = await self.openai_client.analyze_article(
                    article,
                    workflow_state.user_preferences,
                    workflow_state.newsletter_config.sections,
                )

                print(
                    f"   ✅ Analysis complete: relevance={analysis_result.get('relevance_score', 0):.2f}, section={analysis_result.get('best_section', 'Unknown')}"
                )

                # Calculate personalization score
                personal_score = await self._calculate_personalization_score(
                    article, workflow_state.user_preferences
                )

                analyzed_article = AnalyzedArticle(
                    article=article,
                    relevance_score=analysis_result["relevance_score"],
                    sentiment=analysis_result["sentiment"],
                    impact_score=analysis_result["impact_score"],
                    urgency_score=analysis_result["urgency_score"],
                    assigned_section=analysis_result["best_section"],
                    personalization_score=personal_score,
                )

                analyzed_articles.append(analyzed_article)

            except Exception as e:
                print(f"   ❌ Failed to analyze article '{article.title[:30]}...': {e}")
                continue

        return analyzed_articles

    async def _calculate_personalization_score(
        self, article: Article, preferences
    ) -> float:
        """Calculate personalization score based on user preferences"""
        score = 0.0

        # Keyword matching
        title_summary = (article.title + " " + article.summary).lower()
        keyword_matches = sum(
            1 for keyword in preferences.keywords if keyword.lower() in title_summary
        )
        keyword_score = (
            min(keyword_matches / max(len(preferences.keywords), 1), 1.0)
            if preferences.keywords
            else 0.5
        )

        # Source preference
        source_score = 1.0 if article.source in preferences.preferred_sources else 0.5
        if article.source in preferences.excluded_sources:
            source_score = 0.0

        # Industry relevance
        industry_matches = sum(
            1
            for industry in preferences.industry_focus
            if industry.lower() in title_summary
        )
        industry_score = (
            min(industry_matches / max(len(preferences.industry_focus), 1), 1.0)
            if preferences.industry_focus
            else 0.5
        )

        # Combine scores
        score = keyword_score * 0.4 + source_score * 0.3 + industry_score * 0.3

        return min(score, 1.0)
