# File: app/agents/orchestrator.py - UPDATED with quality checks and risk assessment

"""
Main orchestrator with enhanced debugging and word limit management
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
from utils.word_limit_manager import WordLimitManager
from utils.content_quality_manager import ContentQualityManager
from utils.risk_assessment import RiskAssessment, AlertManager
from utils.section_manager import SectionManager
from utils.alert_persistence import AlertDatabase, alert_db

class Orchestrator:
    """Main orchestrator for agent coordination with debugging and word limit management"""

    def __init__(self):
        self.logger = logging.getLogger("Orchestrator")

        # Initialize agents
        self.content_agent = ContentAgent()
        self.analysis_agent = AnalysisAgent()
        self.newsletter_agent = NewsletterAgent()

        # Initialize new managers
        self.quality_manager = ContentQualityManager()
        self.risk_assessment = RiskAssessment()
        self.alert_manager = AlertManager()
        self.alert_db = alert_db 

        self.active_workflows = {}

    async def initialize(self):
        """Initialize all agents"""
        print("🔧 Initializing orchestrator and agents...")

        try:
            await self.alert_db.initialize()

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
        """Generate newsletter with enhanced quality checks and risk assessment"""

        workflow_id = f"workflow_{user_preferences.user_id}_{datetime.utcnow().isoformat()}"

        # 🔧 FIX: RESPECT user sections if provided, otherwise use requirements
        if newsletter_config.sections and len(newsletter_config.sections) > 0:
            # User provided sections - validate but don't replace
            from utils.section_manager import SectionManager
            newsletter_config.sections = SectionManager.validate_sections(
                newsletter_config.sections, newsletter_config.format
            )
            print(f"📋 Using USER-PROVIDED sections: {newsletter_config.sections}")
        else:
            # No user sections - use required defaults
            from utils.section_manager import SectionManager
            newsletter_config.sections = SectionManager.get_required_sections(newsletter_config.format)
            print(f"📋 Using DEFAULT sections: {newsletter_config.sections}")
        
        # 🔧 FIX: Set correct date range (25 days for monthly as per requirements)
        if newsletter_config.format.value == "monthly" and not newsletter_config.date_range:
            from datetime import timedelta
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=25)  # 25 days as per requirements
            newsletter_config.date_range = {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d"),
            }
            print(f"📅 Set 25-day range: {newsletter_config.date_range}")

        # Create workflow state
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            user_id=user_preferences.user_id,
            user_preferences=user_preferences,
            newsletter_config=newsletter_config,
        )

        self.active_workflows[workflow_id] = workflow_state

        try:
            print(f"🚀 Starting enhanced newsletter generation: {workflow_id}")
            
            # Display configuration
            word_budget = newsletter_config.get_word_budget_summary()
            print(f"🎯 Configuration:")
            print(f"   Format: {newsletter_config.format.value}")
            print(f"   Sections: {newsletter_config.sections}")
            print(f"   Word Budget: {word_budget['total_budget']} words")
            print(f"   Date Range: {newsletter_config.date_range}")

            # Phase 1: Content Collection
            workflow_state.status = "collecting"
            print("📰 Phase 1: Enhanced Content Collection")
            articles = await self.content_agent.execute(None, workflow_state)
            # Enforce max_articles early to save tokens/time downstream
            try:
                max_articles = int(newsletter_config.max_articles) if newsletter_config.max_articles else None
            except Exception:
                max_articles = None
            if max_articles and len(articles) > max_articles:
                articles = articles[:max_articles]
                print(f"✂️ Trimmed articles to max_articles={max_articles}")
            workflow_state.collected_articles = articles
            print(f"📊 Content collection: {len(articles)} articles found")

            # Basic quality check - ensure we have minimum articles
            if len(articles) < 3:
                error_msg = f"Insufficient content: only {len(articles)} articles found (minimum 3 required)"
                print(f"❌ {error_msg}")
                return self._create_quality_failed_newsletter(workflow_state, error_msg)

            # Phase 2: Content Analysis  
            workflow_state.status = "analyzing"
            print("🧠 Phase 2: Content Analysis")
            analyzed_articles = await self.analysis_agent.execute(articles, workflow_state)
            workflow_state.analyzed_articles = analyzed_articles
            print(f"📊 Analysis result: {len(analyzed_articles)} articles analyzed")

            # 🔧 NEW: Quality Check Phase (moved after analysis)
            print("🔍 Phase 2.5: Content Quality Assessment")
            
            should_proceed, quality_reason = self.quality_manager.should_generate_newsletter(
                analyzed_articles, newsletter_config
            )
            
            if not should_proceed:
                print(f"❌ Quality check failed: {quality_reason}")
                return self._create_quality_failed_newsletter(workflow_state, quality_reason)
            
            print(f"✅ Quality check passed: {quality_reason}")

            # 🔧 NEW: Enhance article distribution to prevent empty sections
            print("🎯 Phase 2.6: Optimizing Content Distribution")
            analyzed_articles = self.quality_manager.enhance_article_assignment(
                analyzed_articles, newsletter_config.sections
            )
            analyzed_articles = self.quality_manager.redistribute_articles_to_sections(
                analyzed_articles, newsletter_config.sections
            )

            # 🔧 NEW: Risk Assessment Phase
            print("⚠️ Phase 2.7: Risk Assessment")
            
            risk_analysis = self.risk_assessment.assess_articles_risk(analyzed_articles)
            
            # Generate alerts and save to database
            for alert in risk_analysis.get("active_alerts", []):
                self.alert_manager.add_alert(alert)
                # NEW: Save alert to database for persistence
                await self.alert_db.save_alert(alert, workflow_state.user_id)
            
            print(f"📊 Risk Analysis Complete:")
            print(f"   Overall Risk Level: {risk_analysis['overall_risk_level']}")
            print(f"   Impact Score: {risk_analysis['impact_score']}/10")
            print(f"   Alerts Generated: {risk_analysis['alerts_generated']}")
            print(f"   Action Items: {len(risk_analysis['action_items'])}")

            # Phase 3: Newsletter Generation
            workflow_state.status = "generating"
            print("📄 Phase 3: Newsletter Generation with Risk Integration")
            
            # Add risk analysis to workflow state for newsletter agent
            workflow_state.risk_analysis = risk_analysis
            workflow_state.alert_metrics = self.alert_manager.get_metrics()
            
            newsletter = await self.newsletter_agent.execute(analyzed_articles, workflow_state)

            # Enhanced newsletter statistics
            word_analysis = newsletter.get_detailed_word_analysis()
            
            print(f"📊 Newsletter Generation Complete:")
            print(f"   Total articles: {newsletter.total_articles}")
            print(f"   Sections: {len(newsletter.sections)}")
            print(f"   Word usage: {word_analysis['total_analysis']['actual_words']}/{word_analysis['total_analysis']['target_words']}")
            print(f"   Within limits: {'✅' if word_analysis['total_analysis']['within_limit'] else '❌'}")
            print(f"   Risk Level: {risk_analysis['overall_risk_level']}")
            print(f"   Active Alerts: {len(self.alert_manager.get_active_alerts())}")

            # NEW: Update dashboard metrics in database
            dashboard_metrics = {
                "total_articles": newsletter.total_articles,
                "sections": len(newsletter.sections),
                "high_risk_items": len([a for a in risk_analysis.get("active_alerts", []) if a.risk_level.value in ["high", "critical"]]),
                "actions_required": len(risk_analysis.get("active_alerts", [])),
                "risk_level": risk_analysis['overall_risk_level'],
                "impact_score": risk_analysis['impact_score'],
                "newsletter_date": newsletter.generated_at.isoformat()
            }
            await self.alert_db.update_dashboard_metrics(workflow_state.user_id, dashboard_metrics)

            workflow_state.status = "completed"
            return newsletter

        except Exception as e:
            workflow_state.status = "failed"
            workflow_state.error = str(e)
            print(f"❌ Workflow {workflow_id} failed: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            raise

        finally:
            # Cleanup
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]

    def _create_quality_failed_newsletter(self, workflow_state: WorkflowState, reason: str) -> Newsletter:
        """Create newsletter explaining why generation failed quality checks"""
        
        config = workflow_state.newsletter_config
        
        content = f"""# AI Watchtower {config.format.value.title()} Brief - Quality Check Failed

**Generation Status:** Failed Quality Threshold

**Reason:** {reason}

## What Happened?

Your AI Watchtower newsletter could not be generated because we didn't find enough high-quality, relevant articles that meet our standards.

## Next Steps:

1. **Widen Your Search Criteria** - Consider adding more keywords or industry focus areas
2. **Extend Date Range** - Try looking at a longer time period for more content
3. **Review Preferences** - Check if your preferences are too restrictive
4. **Try Again Later** - New content may be available in a few hours

## Technical Details:

- **Search Period:** {config.date_range.get('start', 'Not set')} to {config.date_range.get('end', 'Not set')}
- **Target Sections:** {', '.join(config.sections)}
- **Expected Articles:** Minimum threshold not met
- **Found:** {len(workflow_state.collected_articles or [])} articles

---

*Generated: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}*
"""

        return Newsletter(
            user_id=workflow_state.user_id,
            title=f"AI Watchtower {config.format.value.title()} Brief - Quality Check Failed",
            content=content,
            config=config,
            total_articles=0,
            sections={"Quality Notice": "Newsletter generation failed quality thresholds"},
        )

    def get_dashboard_metrics(self, user_id: str) -> dict:
        """Get metrics for dashboard display (NEW - for frontend)"""
        
        # Try to get cached metrics first
        try:
            import asyncio
            cached_metrics = asyncio.create_task(self.alert_db.get_cached_dashboard_metrics(user_id))
            cached = asyncio.get_event_loop().run_until_complete(cached_metrics)
            
            if cached:
                return cached
        except Exception as e:
            print(f"⚠️ Could not get cached metrics: {e}")
        
        # Fallback to alert manager
        alert_metrics = self.alert_manager.get_metrics()
        active_alerts = self.alert_manager.get_active_alerts()
        
        # Get latest risk assessment if available
        latest_risk_level = "low"  # Default
        impact_score = 0
        
        # This would be enhanced to store/retrieve latest assessment
        
        return {
            "total_articles": 0,  # Would be from latest newsletter
            "sections": 5,  # Default sections count
            "high_risk_items": alert_metrics["critical_alerts"],
            "actions_required": alert_metrics["actions_required"],
            "risk_level": latest_risk_level,
            "impact_score": impact_score,
            "active_alerts": len(active_alerts),
            "compliance_deadlines": alert_metrics["compliance_deadlines"],
            "security_threats": alert_metrics["security_threats"]
        }
    
    def get_alerts_and_actions(self, user_id: str) -> dict:
        """Get alerts and actions data for frontend (NEW)"""
        
        # Try to get from database first
        try:
            import asyncio
            db_alerts_task = asyncio.create_task(self.alert_db.get_user_alerts(user_id, limit=50))
            db_alerts = asyncio.get_event_loop().run_until_complete(db_alerts_task)
            
            if db_alerts:
                # Get summary from database
                metrics_task = asyncio.create_task(self.alert_db.get_alert_metrics(user_id))
                metrics = asyncio.get_event_loop().run_until_complete(metrics_task)
                
                return {
                    "alerts": db_alerts,
                    "summary": {
                        "total_alerts": len(db_alerts),
                        "by_risk_level": metrics.get("by_risk_level", {}),
                        "by_type": metrics.get("by_type", {})
                    }
                }
        except Exception as e:
            print(f"⚠️ Could not get alerts from database: {e}")
        
        # Fallback to in-memory alert manager
        active_alerts = self.alert_manager.get_active_alerts()
        
        return {
            "alerts": [
                {
                    "id": alert.id,
                    "title": alert.title,
                    "description": alert.description,
                    "risk_level": alert.risk_level.value,
                    "alert_type": alert.alert_type.value,
                    "deadline": alert.deadline.isoformat() if alert.deadline else None,
                    "action_required": alert.action_required,
                    "created_at": alert.created_at.isoformat()
                }
                for alert in active_alerts
            ],
            "summary": {
                "total_alerts": len(active_alerts),
                "by_risk_level": {
                    "critical": len([a for a in active_alerts if a.risk_level.value == "critical"]),
                    "high": len([a for a in active_alerts if a.risk_level.value == "high"]),
                    "medium": len([a for a in active_alerts if a.risk_level.value == "medium"]),
                    "low": len([a for a in active_alerts if a.risk_level.value == "low"])
                },
                "by_type": {
                    "compliance_deadline": len([a for a in active_alerts if a.alert_type.value == "compliance_deadline"]),
                    "security_threat": len([a for a in active_alerts if a.alert_type.value == "security_threat"]),
                    "regulatory_change": len([a for a in active_alerts if a.alert_type.value == "regulatory_change"]),
                    "market_disruption": len([a for a in active_alerts if a.alert_type.value == "market_disruption"])
                }
            }
        }

    def get_workflow_status(self, workflow_id: str) -> Optional[dict]:
        """Get workflow status with word limit information"""
        if workflow_id in self.active_workflows:
            state = self.active_workflows[workflow_id]
            
            # Include word limit configuration in status
            word_config = None
            if state.newsletter_config:
                word_config = {
                    "max_total_words": state.newsletter_config.max_total_words,
                    "max_section_words": state.newsletter_config.max_section_words,
                    "max_article_summary_words": state.newsletter_config.max_article_summary_words
                }
            
            return {
                "workflow_id": workflow_id,
                "status": state.status,
                "created_at": state.created_at.isoformat(),
                "error": state.error,
                "word_limits": word_config,
                "sections": state.newsletter_config.sections if state.newsletter_config else None,
                "format": state.newsletter_config.format.value if state.newsletter_config else None
            }
        return None

    def get_agents_status(self) -> dict:
        """Get status of all agents"""
        return {
            "content_agent": self.content_agent.get_status(),
            "analysis_agent": self.analysis_agent.get_status(),
            "newsletter_agent": self.newsletter_agent.get_status(),
        }

    async def validate_newsletter_config(self, config: NewsletterConfig) -> dict:
        """Validate newsletter configuration for word limits and sections"""
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        try:
            # Validate word limits
            word_budget = config.get_word_budget_summary()
            
            if config.max_total_words < 500:
                validation_results["warnings"].append(
                    f"Total word limit ({config.max_total_words}) is quite low. Consider at least 500 words for meaningful content."
                )
            
            if config.max_total_words > 5000:
                validation_results["warnings"].append(
                    f"Total word limit ({config.max_total_words}) is quite high. Consider reducing for better readability."
                )
            
            # Check section/word balance
            if len(config.sections) > 6:
                validation_results["warnings"].append(
                    f"Many sections ({len(config.sections)}) may result in very short content per section (~{word_budget['words_per_section']} words each)."
                )
            
            if word_budget['words_per_section'] < 100:
                validation_results["recommendations"].append(
                    "Consider reducing number of sections or increasing total word limit for more substantial content."
                )
            
            # Validate sections
            if not config.sections:
                validation_results["errors"].append("No sections specified")
                validation_results["valid"] = False
            
            # Check article limits vs word budget
            articles_per_section = config.max_articles // len(config.sections) if config.sections else 0
            words_per_article = config.max_article_summary_words
            section_content_estimate = articles_per_section * words_per_article
            
            if section_content_estimate > config.max_section_words:
                validation_results["recommendations"].append(
                    f"Article distribution may exceed section word limits. Consider reducing max_articles or increasing section word limits."
                )
            
            return validation_results
            
        except Exception as e:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Validation error: {str(e)}")
            return validation_results

    async def preview_word_distribution(self, config: NewsletterConfig) -> dict:
        """Preview how words will be distributed across sections"""
        try:
            word_manager = WordLimitManager(config)
            section_budgets = word_manager.calculate_section_word_budget(config.sections)
            word_budget = config.get_word_budget_summary()
            
            return {
                "total_budget": word_budget,
                "section_budgets": section_budgets,
                "estimated_articles_per_section": {
                    section: budget // config.max_article_summary_words
                    for section, budget in section_budgets.items()
                },
                "content_density": {
                    "light": word_budget['words_per_section'] < 200,
                    "moderate": 200 <= word_budget['words_per_section'] <= 400,
                    "heavy": word_budget['words_per_section'] > 400
                }
            }
            
        except Exception as e:
            return {"error": str(e)}


# Global orchestrator instance
orchestrator = Orchestrator()