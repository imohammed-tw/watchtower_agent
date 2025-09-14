# File: app/agents/newsletter_agent.py - UPDATED with WordLimitManager

"""
Newsletter Agent with enhanced debugging and word limit management
"""
from typing import List, Any, Dict
from datetime import datetime
from collections import defaultdict

from agents.base_agent import BaseAgent
from models import WorkflowState, AnalyzedArticle, Newsletter
from tools.openai_client import OpenAIClient
from templates.newsletter_templates import NewsletterTemplateFactory
from utils.word_limit_manager import WordLimitManager


class NewsletterAgent(BaseAgent):
    """Newsletter generation and distribution agent with word limit control"""

    def __init__(self):
        super().__init__("NewsletterAgent")
        self.openai_client = None
        self.template_factory = None
        self.word_manager = None

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
        """Execute newsletter generation workflow with word limit enforcement"""
        self.last_execution = datetime.utcnow()

        try:
            analyzed_articles = input_data
            config = workflow_state.newsletter_config

            # Initialize word limit manager
            self.word_manager = WordLimitManager(config)
            
            print(f"📄 Newsletter Agent: Starting generation with {len(analyzed_articles)} articles")
            print(f"📋 Target sections: {config.sections}")
            print(f"🎯 Word limits: Total {config.max_total_words}, Section {config.max_section_words}, Article {config.max_article_summary_words}")

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

            # 1. Calculate word budgets per section
            print("💰 Step 1: Calculating word budgets...")
            section_budgets = self.word_manager.calculate_section_word_budget(config.sections)

            # 2. Distribute articles to sections with word optimization
            print("🔄 Step 2: Distributing content to sections with word limits...")
            section_content = await self._distribute_content_with_word_limits(
                analyzed_articles, config.sections, section_budgets
            )

            print(f"📊 Optimized distribution result:")
            for section_name, articles in section_content.items():
                estimated_words = self.word_manager.estimate_content_length(articles)
                budget = section_budgets.get(section_name, config.max_section_words)
                print(f"   {section_name}: {len(articles)} articles (~{estimated_words}/{budget} words)")

            if not section_content:
                print("❌ No content distributed to any sections!")
                return self._create_empty_newsletter(workflow_state)

            # 3. Generate each section with word limits
            print("✍️ Step 3: Generating section content with word limits...")
            newsletter_sections = {}
            total_generated_words = 0

            for section_name in config.sections:
                articles = section_content.get(section_name, [])
                section_budget = section_budgets.get(section_name, config.max_section_words)
                
                print(f"📝 Generating '{section_name}' with {len(articles)} articles (budget: {section_budget} words)...")

                if articles:
                    try:
                        section_content_text = await self._generate_section_with_word_limits(
                            section_name, articles, workflow_state, section_budget
                        )
                        newsletter_sections[section_name] = section_content_text
                        
                        # Track word usage
                        section_words = len(section_content_text.split())
                        total_generated_words += section_words
                        
                        status = "✅" if section_words <= section_budget else "⚠️"
                        print(f"{status} '{section_name}' generated: {section_words}/{section_budget} words")
                        
                    except Exception as e:
                        print(f"❌ Error generating '{section_name}': {e}")
                        fallback_content = self._create_fallback_section(section_name, articles, section_budget)
                        newsletter_sections[section_name] = fallback_content
                        total_generated_words += len(fallback_content.split())
                else:
                    print(f"⚠️ '{section_name}' has no articles, skipping...")

            print(f"📊 Section generation complete: {len(newsletter_sections)} sections")
            print(f"🎯 Total words generated: {total_generated_words}/{config.max_total_words}")

            # 4. Validate total word count and optimize if necessary
            if total_generated_words > config.max_total_words:
                print(f"⚠️ Content exceeds word limit by {total_generated_words - config.max_total_words} words")
                newsletter_sections = await self._optimize_sections_for_word_limit(
                    newsletter_sections, config.max_total_words
                )
                total_generated_words = sum(len(content.split()) for content in newsletter_sections.values())
                print(f"🔧 After optimization: {total_generated_words}/{config.max_total_words} words")

            # 5. Compile final newsletter using template
            print("📋 Step 4: Compiling final newsletter...")
            try:
                template = self.template_factory.get_template(config.template, config.format)
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
                
                final_word_count = len(newsletter_content.split())
                print(f"✅ Template rendered: {final_word_count} total words")
                
                # Final word count validation
                if final_word_count > config.max_total_words:
                    print(f"⚠️ Final content still exceeds limit, truncating...")
                    newsletter_content = self.word_manager.truncate_text(
                        newsletter_content, 
                        config.max_total_words, 
                        preserve_sentences=True
                    )
                    final_word_count = len(newsletter_content.split())
                    print(f"🔧 After final truncation: {final_word_count} words")
                
            except Exception as e:
                print(f"❌ Template rendering failed: {e}")
                # Fallback to simple content
                newsletter_content = self._create_simple_newsletter_with_limits(
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

            # Final statistics
            word_analysis = newsletter.get_detailed_word_analysis()
            print(f"✅ Newsletter generation completed successfully")
            print(f"📊 Final statistics:")
            print(f"   Total words: {word_analysis['total_analysis']['actual_words']}")
            print(f"   Target words: {word_analysis['total_analysis']['target_words']}")
            print(f"   Utilization: {word_analysis['total_analysis']['utilization']}")
            print(f"   Within limit: {word_analysis['total_analysis']['within_limit']}")

            return newsletter

        except Exception as e:
            print(f"❌ Newsletter generation failed: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            raise

    async def _distribute_content_with_word_limits(
        self, analyzed_articles: List[AnalyzedArticle], sections: List[str], section_budgets: Dict[str, int]
    ) -> Dict[str, List[AnalyzedArticle]]:
        """Distribute articles to sections with word budget optimization"""
        print(f"🔄 Distributing {len(analyzed_articles)} articles to {len(sections)} sections with word limits")

        # First, do basic distribution based on OpenAI assignments
        section_assignments = defaultdict(list)
        
        for article in analyzed_articles:
            assigned_section = article.assigned_section
            if assigned_section in sections:
                section_assignments[assigned_section].append(article)
            else:
                # Fallback to first available section
                section_assignments[sections[0]].append(article)

        print(f"📊 Initial distribution:")
        for section, articles in section_assignments.items():
            print(f"   {section}: {len(articles)} articles")

        # Now optimize based on word budgets using WordLimitManager
        optimized_assignments = self.word_manager.optimize_article_distribution(
            dict(section_assignments), section_budgets
        )

        print(f"📊 Word-optimized distribution:")
        for section_name in sections:
            articles = optimized_assignments.get(section_name, [])
            estimated_words = self.word_manager.estimate_content_length(articles)
            budget = section_budgets.get(section_name, 0)
            print(f"   {section_name}: {len(articles)} articles (~{estimated_words}/{budget} words)")

        return optimized_assignments

    async def _generate_section_with_word_limits(
        self,
        section_name: str,
        articles: List[AnalyzedArticle],
        workflow_state: WorkflowState,
        word_budget: int,
    ) -> str:
        """Generate content for a specific section with strict word limits"""
        try:
            print(f"✍️ Generating section '{section_name}' with {len(articles)} articles, budget: {word_budget} words")

            # Limit articles per section based on word budget
            max_articles_for_budget = max(1, min(len(articles), word_budget // self.word_manager.config.max_article_summary_words))
            selected_articles = articles[:max_articles_for_budget]
            
            print(f"📝 Using {len(selected_articles)} articles for '{section_name}' (budget allows {max_articles_for_budget})")

            # Generate section content using OpenAI with word limit enforcement
            section_content = await self.openai_client.generate_section_content_with_limits(
                section_name, selected_articles, workflow_state.newsletter_config, word_budget
            )

            # Ensure content is within word limit (backup enforcement)
            actual_words = len(section_content.split())
            if actual_words > word_budget:
                print(f"⚠️ Section '{section_name}' exceeded budget ({actual_words}/{word_budget}), truncating...")
                section_content = self.word_manager.truncate_text(section_content, word_budget, preserve_sentences=True)
                actual_words = len(section_content.split())

            print(f"✅ Section '{section_name}' final: {actual_words}/{word_budget} words")
            return section_content

        except Exception as e:
            print(f"❌ Error generating section '{section_name}': {e}")
            return self._create_fallback_section(section_name, articles, word_budget)

    def _create_fallback_section(self, section_name: str, articles: List[AnalyzedArticle], word_budget: int) -> str:
        """Create fallback content for a section within word limits"""
        fallback_content = f"**{section_name}**\n\nRecent developments in this area include:\n\n"
        
        words_used = len(fallback_content.split())
        remaining_budget = word_budget - words_used
        
        for i, article in enumerate(articles[:3], 1):
            # Calculate words for this article entry
            article_summary = article.article.summary[:100] + "..." if len(article.article.summary) > 100 else article.article.summary
            article_entry = f"{i}. **{article.article.title}** - {article_summary} [Read more]({article.article.url})\n\n"
            
            entry_words = len(article_entry.split())
            if words_used + entry_words <= word_budget:
                fallback_content += article_entry
                words_used += entry_words
            else:
                # Truncate this entry to fit
                remaining_words = word_budget - words_used - 5  # Reserve 5 words for safety
                if remaining_words > 20:  # Only add if we have reasonable space
                    truncated_summary = self.word_manager.truncate_text(article_summary, remaining_words - 10)
                    fallback_content += f"{i}. **{article.article.title}** - {truncated_summary}\n\n"
                break
        
        return fallback_content

    async def _optimize_sections_for_word_limit(self, sections: Dict[str, str], total_word_limit: int) -> Dict[str, str]:
        """Optimize sections to fit within total word limit"""
        current_total = sum(len(content.split()) for content in sections.values())
        
        if current_total <= total_word_limit:
            return sections
        
        # Calculate reduction factor
        reduction_factor = total_word_limit / current_total
        
        print(f"🔧 Optimizing sections: reducing by factor of {reduction_factor:.2f}")
        
        optimized_sections = {}
        for section_name, content in sections.items():
            current_words = len(content.split())
            target_words = int(current_words * reduction_factor)
            
            if target_words < current_words:
                optimized_content = self.word_manager.truncate_text(content, target_words, preserve_sentences=True)
                optimized_sections[section_name] = optimized_content
                print(f"   {section_name}: {current_words} -> {len(optimized_content.split())} words")
            else:
                optimized_sections[section_name] = content
        
        return optimized_sections

    def _create_empty_newsletter(self, workflow_state: WorkflowState) -> Newsletter:
        """Create empty newsletter for debugging with word limits"""
        print("📝 Creating empty newsletter")

        config = workflow_state.newsletter_config
        word_budget = config.max_total_words

        empty_content = f"""# AI Watchtower {config.format.value.title()} Brief

**No content available** - Please check the configuration and try again.

Generated: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}

Word Budget: {word_budget} words
"""

        # Ensure even empty newsletter respects word limits
        if len(empty_content.split()) > word_budget:
            empty_content = self.word_manager.truncate_text(empty_content, word_budget)

        return Newsletter(
            user_id=workflow_state.user_id,
            title=f"AI Watchtower {config.format.value.title()} Brief - {datetime.utcnow().strftime('%B %Y')}",
            content=empty_content,
            config=config,
            total_articles=0,
            sections={},
        )

    def _create_simple_newsletter_with_limits(
        self, sections: Dict[str, str], config, total_articles: int
    ) -> str:
        """Create simple newsletter content as fallback with word limits"""
        header = f"""# AI Watchtower {config.format.value.title()} Brief

Generated: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}
Total Articles: {total_articles}
Word Limit: {config.max_total_words} words

"""
        
        content = header
        words_used = len(header.split())
        remaining_budget = config.max_total_words - words_used
        
        # Distribute remaining budget across sections
        section_budget = remaining_budget // len(sections) if sections else remaining_budget
        
        for section_name, section_content in sections.items():
            section_header = f"## {section_name}\n\n"
            available_for_content = section_budget - len(section_header.split())
            
            if available_for_content > 20:  # Only add if reasonable space
                truncated_content = self.word_manager.truncate_text(
                    section_content, available_for_content, preserve_sentences=True
                )
                content += section_header + truncated_content + "\n\n"
            else:
                content += section_header + "Content truncated due to word limits.\n\n"
        
        return content