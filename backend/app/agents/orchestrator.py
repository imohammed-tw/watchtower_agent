# File: app/agents/orchestrator.py
"""
Main orchestrator with enhanced debugging
"""
import asyncio
from datetime import datetime
from typing import Optional
import logging

from agents.base_agent import BaseAgent
from agents.content_agent import ContentAgent
from agents.analysis_agent import AnalysisAgent
from agents.newsletter_agent import NewsletterAgent
from models import WorkflowState, Newsletter, UserPreferences, NewsletterConfig


class Orchestrator:
    """Main orchestrator for agent coordination with debugging"""

    def __init__(self):
        self.logger = logging.getLogger("Orchestrator")

        # Initialize agents
        self.content_agent = ContentAgent()
        self.analysis_agent = AnalysisAgent()
        self.newsletter_agent = NewsletterAgent()

        self.active_workflows = {}

    async def initialize(self):
        """Initialize all agents"""
        print("🔧 Initializing orchestrator and agents...")

        try:
            await asyncio.gather(
                self.content_agent.initialize(),
                self.analysis_agent.initialize(),
                self.newsletter_agent.initialize(),
            )
            print("✅ All agents initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing agents: {e}")
            raise

    async def generate_newsletter(
        self, user_preferences: UserPreferences, newsletter_config: NewsletterConfig
    ) -> Newsletter:
        """Generate newsletter using multi-agent workflow with debugging"""

        workflow_id = (
            f"workflow_{user_preferences.user_id}_{datetime.utcnow().isoformat()}"
        )

        # Create workflow state
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            user_id=user_preferences.user_id,
            user_preferences=user_preferences,
            newsletter_config=newsletter_config,
        )

        self.active_workflows[workflow_id] = workflow_state

        try:
            print(f"🚀 Starting newsletter generation workflow: {workflow_id}")

            # Phase 1: Content Collection
            workflow_state.status = "collecting"
            print("📰 Phase 1: Content Collection")
            articles = await self.content_agent.execute(None, workflow_state)
            workflow_state.collected_articles = articles
            print(f"📊 Content collection result: {len(articles)} articles collected")

            if not articles:
                print("⚠️ No articles collected, generating empty newsletter")
                # Continue with empty articles to test the rest of the pipeline

            # Phase 2: Content Analysis
            workflow_state.status = "analyzing"
            print("🧠 Phase 2: Content Analysis")
            print(f"📝 Analyzing {len(articles)} articles...")

            analyzed_articles = await self.analysis_agent.execute(
                articles, workflow_state
            )
            workflow_state.analyzed_articles = analyzed_articles
            print(
                f"📊 Analysis result: {len(analyzed_articles)} articles passed analysis"
            )

            # Debug: Print analysis details
            if analyzed_articles:
                print("📋 Analysis breakdown:")
                for i, article in enumerate(analyzed_articles[:3]):  # Show first 3
                    print(f"   {i+1}. {article.article.title[:50]}...")
                    print(f"      Relevance: {article.relevance_score:.2f}")
                    print(f"      Section: {article.assigned_section}")
                    print(f"      Sentiment: {article.sentiment}")
            else:
                print("❌ No articles passed analysis threshold!")
                # Check raw analysis results
                print("🔍 Checking if articles are being analyzed at all...")

            # Phase 3: Newsletter Generation
            workflow_state.status = "generating"
            print("📄 Phase 3: Newsletter Generation")
            print(
                f"📝 Generating newsletter from {len(analyzed_articles)} analyzed articles..."
            )

            newsletter = await self.newsletter_agent.execute(
                analyzed_articles, workflow_state
            )

            # Debug newsletter generation
            print(f"📊 Newsletter generation result:")
            print(f"   Total articles: {newsletter.total_articles}")
            print(f"   Sections: {len(newsletter.sections)}")
            print(f"   Section names: {list(newsletter.sections.keys())}")
            print(f"   Content length: {len(newsletter.content)} characters")

            # Show section content lengths
            for section_name, content in newsletter.sections.items():
                print(f"   {section_name}: {len(content)} characters")

            workflow_state.status = "completed"
            print(f"✅ Newsletter generation completed: {workflow_id}")

            return newsletter

        except Exception as e:
            workflow_state.status = "failed"
            workflow_state.error = str(e)
            print(f"❌ Workflow {workflow_id} failed: {e}")
            print(f"   Error type: {type(e)}")
            import traceback

            print(f"   Traceback: {traceback.format_exc()}")
            raise

        finally:
            # Cleanup
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]

    def get_workflow_status(self, workflow_id: str) -> Optional[dict]:
        """Get workflow status"""
        if workflow_id in self.active_workflows:
            state = self.active_workflows[workflow_id]
            return {
                "workflow_id": workflow_id,
                "status": state.status,
                "created_at": state.created_at.isoformat(),
                "error": state.error,
            }
        return None

    def get_agents_status(self) -> dict:
        """Get status of all agents"""
        return {
            "content_agent": self.content_agent.get_status(),
            "analysis_agent": self.analysis_agent.get_status(),
            "newsletter_agent": self.newsletter_agent.get_status(),
        }


# Global orchestrator instance
orchestrator = Orchestrator()
