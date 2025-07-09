# File: app/agents/newsletter_agent.py
"""
Newsletter Agent with enhanced debugging
"""
from typing import List, Any, Dict
from datetime import datetime
from collections import defaultdict

from agents.base_agent import BaseAgent
from models import WorkflowState, AnalyzedArticle, Newsletter
from tools.openai_client import OpenAIClient
from templates.newsletter_templates import NewsletterTemplateFactory


class NewsletterAgent(BaseAgent):
    """Newsletter generation and distribution agent with debugging"""

    def __init__(self):
        super().__init__("NewsletterAgent")
        self.openai_client = None
        self.template_factory = None

    async def initialize(self):
        """Initialize newsletter agent resources"""
        await super().initialize()
        self.openai_client = OpenAIClient()
        self.template_factory = NewsletterTemplateFactory()
        await self.openai_client.initialize()
        print("✅ Newsletter agent initialized")

    async def execute(
        self, input_data: List[AnalyzedArticle], workflow_state: WorkflowState
    ) -> Newsletter:
        """Execute newsletter generation workflow with debugging"""
        self.last_execution = datetime.utcnow()

        try:
            analyzed_articles = input_data
            config = workflow_state.newsletter_config

            print(
                f"📄 Newsletter Agent: Starting generation with {len(analyzed_articles)} articles"
            )
            print(f"📋 Target sections: {config.sections}")

            if not analyzed_articles:
                print("⚠️ No analyzed articles provided to newsletter agent")
                return self._create_empty_newsletter(workflow_state)

            # Debug: Show article section assignments
            section_counts = defaultdict(int)
            for article in analyzed_articles:
                section_counts[article.assigned_section] += 1

            print(f"📊 Article distribution by section:")
            for section, count in section_counts.items():
                print(f"   {section}: {count} articles")

            # 1. Distribute articles to sections (no duplicates)
            print("🔄 Step 1: Distributing content to sections...")
            section_content = await self._distribute_content_to_sections(
                analyzed_articles, config.sections
            )

            print(f"📊 Distribution result:")
            for section_name, articles in section_content.items():
                print(f"   {section_name}: {len(articles)} articles")

            if not section_content:
                print("❌ No content distributed to any sections!")
                return self._create_empty_newsletter(workflow_state)

            # 2. Generate each section
            print("✍️ Step 2: Generating section content...")
            newsletter_sections = {}

            for section_name in config.sections:
                articles = section_content.get(section_name, [])
                print(
                    f"📝 Generating '{section_name}' with {len(articles)} articles..."
                )

                if articles:
                    try:
                        section_content_text = await self._generate_section(
                            section_name, articles, workflow_state
                        )
                        newsletter_sections[section_name] = section_content_text
                        print(
                            f"✅ '{section_name}' generated: {len(section_content_text)} characters"
                        )
                    except Exception as e:
                        print(f"❌ Error generating '{section_name}': {e}")
                        newsletter_sections[section_name] = (
                            f"**{section_name}**\n\nContent generation failed: {str(e)}\n"
                        )
                else:
                    print(f"⚠️ '{section_name}' has no articles, skipping...")

            print(
                f"📊 Section generation complete: {len(newsletter_sections)} sections"
            )

            # 3. Compile final newsletter using template
            print("📋 Step 3: Compiling final newsletter...")
            try:
                template = self.template_factory.get_template(
                    config.template, config.format
                )
                newsletter_content = template.render(
                    {
                        "title": f"AI Watchtower {config.format.value.title()} Brief",
                        "sections": newsletter_sections,
                        "config": config,
                        "user_preferences": workflow_state.user_preferences,
                        "total_articles": len(analyzed_articles),
                        "generated_at": datetime.utcnow(),
                    }
                )
                print(f"✅ Template rendered: {len(newsletter_content)} characters")
            except Exception as e:
                print(f"❌ Template rendering failed: {e}")
                # Fallback to simple content
                newsletter_content = self._create_simple_newsletter(
                    newsletter_sections, config, len(analyzed_articles)
                )

            newsletter = Newsletter(
                user_id=workflow_state.user_id,
                title=f"AI Watchtower {config.format.value.title()} Brief - {datetime.utcnow().strftime('%B %Y')}",
                content=newsletter_content,
                config=config,
                total_articles=len(analyzed_articles),
                sections=newsletter_sections,
            )

            print(f"✅ Newsletter generation completed successfully")
            print(
                f"📊 Final newsletter: {len(newsletter.content)} characters, {len(newsletter.sections)} sections"
            )

            return newsletter

        except Exception as e:
            print(f"❌ Newsletter generation failed: {e}")
            import traceback

            print(f"   Traceback: {traceback.format_exc()}")
            raise

    async def _distribute_content_to_sections(
        self, analyzed_articles: List[AnalyzedArticle], sections: List[str]
    ) -> Dict[str, List[AnalyzedArticle]]:
        """Distribute articles to sections ensuring no duplicates with debugging"""
        print(
            f"🔄 Distributing {len(analyzed_articles)} articles to {len(sections)} sections"
        )

        section_assignments = defaultdict(list)

        # Sort articles by composite score (relevance + personalization + impact)
        sorted_articles = sorted(
            analyzed_articles,
            key=lambda x: (
                x.relevance_score * 0.4
                + x.personalization_score * 0.4
                + x.impact_score / 10 * 0.2
            ),
            reverse=True,
        )

        print(f"📋 Available target sections: {sections}")

        # Assign each article to its best section (only once)
        assigned_count = 0
        for article in sorted_articles:
            assigned_section = article.assigned_section
            print(
                f"   Article '{article.article.title[:30]}...' -> '{assigned_section}'"
            )

            if assigned_section in sections:
                section_assignments[assigned_section].append(article)
                assigned_count += 1
                print(f"     ✅ Assigned to '{assigned_section}'")
            else:
                print(
                    f"     ❌ Section '{assigned_section}' not in target sections {sections}"
                )
                # Try to assign to first available section
                if sections:
                    fallback_section = sections[0]
                    section_assignments[fallback_section].append(article)
                    assigned_count += 1
                    print(f"     🔄 Fallback: assigned to '{fallback_section}'")

        print(
            f"📊 Distribution complete: {assigned_count}/{len(analyzed_articles)} articles assigned"
        )

        result = dict(section_assignments)
        if not result:
            print("❌ WARNING: No articles were assigned to any sections!")
            print(f"   Available sections: {sections}")
            print(
                f"   Article sections: {set(a.assigned_section for a in analyzed_articles)}"
            )

        return result

    async def _generate_section(
        self,
        section_name: str,
        articles: List[AnalyzedArticle],
        workflow_state: WorkflowState,
    ) -> str:
        """Generate content for a specific section with debugging"""
        try:
            print(
                f"✍️ Generating section '{section_name}' with {len(articles)} articles"
            )

            # Limit articles per section
            max_articles = min(len(articles), 5)
            selected_articles = articles[:max_articles]
            print(
                f"📝 Using top {len(selected_articles)} articles for '{section_name}'"
            )

            # Generate section content using OpenAI
            section_content = await self.openai_client.generate_section_content(
                section_name, selected_articles, workflow_state.newsletter_config
            )

            print(
                f"✅ Section '{section_name}' generated: {len(section_content)} characters"
            )
            return section_content

        except Exception as e:
            print(f"❌ Error generating section '{section_name}': {e}")
            # Create fallback content
            fallback_content = f"""**{section_name}**

Recent developments in this area include:

"""
            for i, article in enumerate(articles[:3], 1):
                fallback_content += f"{i}. **{article.article.title}** - {article.article.summary[:100]}... [Read more]({article.article.url})\n\n"

            return fallback_content

    def _create_empty_newsletter(self, workflow_state: WorkflowState) -> Newsletter:
        """Create empty newsletter for debugging"""
        print("📝 Creating empty newsletter")

        config = workflow_state.newsletter_config

        empty_content = f"""# AI Watchtower {config.format.value.title()} Brief

**No content available** - Please check the configuration and try again.

Generated: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}
"""

        return Newsletter(
            user_id=workflow_state.user_id,
            title=f"AI Watchtower {config.format.value.title()} Brief - {datetime.utcnow().strftime('%B %Y')}",
            content=empty_content,
            config=config,
            total_articles=0,
            sections={},
        )

    def _create_simple_newsletter(
        self, sections: Dict[str, str], config, total_articles: int
    ) -> str:
        """Create simple newsletter content as fallback"""
        content = f"""# AI Watchtower {config.format.value.title()} Brief

Generated: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}

Total Articles: {total_articles}

"""

        for section_name, section_content in sections.items():
            content += f"## {section_name}\n\n{section_content}\n\n"

        return content
