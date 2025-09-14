# File: backend/app/templates/newsletter_templates.py - UPDATED with word limits

"""
Newsletter template system for flexible formatting with word limit support
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime

from models import NewsletterFormat, TemplateType


class NewsletterTemplate(ABC):
    """Base class for newsletter templates with word limit awareness"""

    def __init__(self, format_type: NewsletterFormat):
        self.format_type = format_type

    @abstractmethod
    def render(self, content: Dict[str, Any]) -> str:
        """Render newsletter content"""
        pass

    def _format_header(self, title: str, generated_at: datetime, config=None) -> str:
        """Format newsletter header with word limit info"""
        word_info = ""
        if config and hasattr(config, 'max_total_words'):
            word_info = f"*Target Length: {config.max_total_words} words*\n"
        
        return f"""# {title}

**AI Watchtower** - Trusted Insights on Navigating AI Safety, Security, and Sustainability  
*Generated: {generated_at.strftime("%B %d, %Y at %I:%M %p UTC")}*  
{word_info}
---

"""

    def _format_footer(self) -> str:
        """Format newsletter footer"""
        return """

---

**Thank you for choosing AI Watchtower** as your source for dependable AI intelligence.

AI Watchtower is committed to your data privacy and security. This digest is generated using privacy-preserving techniques. Your preference data stays secured within our system and is never shared with third parties.

*Customize Your Digest | Manage Subscription | Privacy Policy*  
© 2025 AI Watchtower, Inc. All rights reserved.

"""

    def _get_word_summary(self, config, total_articles: int, sections_count: int) -> str:
        """Generate word usage summary for templates"""
        if not config or not hasattr(config, 'max_total_words'):
            return ""
        
        word_budget = config.get_word_budget_summary() if hasattr(config, 'get_word_budget_summary') else {}
        
        return f"""
**Newsletter Configuration:**
- Format: {config.format.value.title()}
- Articles: {total_articles}
- Sections: {sections_count}
- Word Budget: {config.max_total_words} words
- Words per Section: ~{config.max_section_words} words

"""

    def _ensure_section_word_limits(self, sections: Dict[str, str], config) -> Dict[str, str]:
        """Ensure sections don't exceed word limits (backup check)"""
        if not config or not hasattr(config, 'max_section_words'):
            return sections
        
        from utils.word_limit_manager import WordLimitManager
        word_manager = WordLimitManager(config)
        
        optimized_sections = {}
        for section_name, content in sections.items():
            word_count = len(content.split())
            if word_count > config.max_section_words:
                print(f"⚠️ Template: Section '{section_name}' ({word_count} words) exceeds limit ({config.max_section_words}), truncating...")
                optimized_content = word_manager.truncate_text(content, config.max_section_words, preserve_sentences=True)
                optimized_sections[section_name] = optimized_content
            else:
                optimized_sections[section_name] = content
        
        return optimized_sections


class ProfessionalTemplate(NewsletterTemplate):
    """Professional newsletter template with word limit support"""

    def render(self, content: Dict[str, Any]) -> str:
        """Render professional newsletter with word limits"""
        sections = content.get("sections", {})
        config = content.get("config")
        
        # Ensure sections respect word limits
        sections = self._ensure_section_word_limits(sections, config)

        # Build newsletter content
        newsletter_content = []

        # Header with word limit info
        newsletter_content.append(
            self._format_header(
                content.get("title", "AI Watchtower Newsletter"),
                content.get("generated_at", datetime.utcnow()),
                config
            )
        )

        # Executive Summary (word-conscious)
        total_articles = content.get('total_articles', 0)
        sections_count = len(sections)
        
        if config and hasattr(config, 'format'):
            newsletter_content.append(
                f"""## Executive Summary

Welcome to your {config.format.value} AI Watchtower briefing. This edition covers {total_articles} carefully curated articles spanning {sections_count} key areas of AI development and governance.

{self._get_word_summary(config, total_articles, sections_count)}"""
            )
        else:
            newsletter_content.append(
                f"""## Executive Summary

Welcome to your AI Watchtower briefing covering {total_articles} articles across {sections_count} key areas.

"""
            )

        # Sections (already word-limited)
        for section_name, section_content in sections.items():
            newsletter_content.append(f"## {section_name}\n\n{section_content}\n\n")

        # Footer
        newsletter_content.append(self._format_footer())

        final_content = "".join(newsletter_content)
        
        # Final word count check and warning
        if config and hasattr(config, 'max_total_words'):
            final_word_count = len(final_content.split())
            if final_word_count > config.max_total_words:
                print(f"⚠️ Professional Template: Final content ({final_word_count} words) exceeds limit ({config.max_total_words} words)")

        return final_content


class BriefTemplate(NewsletterTemplate):
    """Brief newsletter template optimized for shorter content"""

    def render(self, content: Dict[str, Any]) -> str:
        """Render brief newsletter with minimal overhead"""
        sections = content.get("sections", {})
        config = content.get("config")
        
        # Ensure sections respect word limits
        sections = self._ensure_section_word_limits(sections, config)

        newsletter_content = []

        # Very compact header for brief template
        title = content.get("title", "AI Watchtower Brief")
        generated_at = content.get("generated_at", datetime.utcnow())
        total_articles = content.get("total_articles", 0)
        
        newsletter_content.append(
            f"""# {title}

*{total_articles} articles • {generated_at.strftime("%b %d, %Y")}*

"""
        )

        # Add word budget info for brief template
        if config and hasattr(config, 'max_total_words'):
            newsletter_content.append(f"*Word Budget: {config.max_total_words} words*\n\n")

        # Compact sections - no extra headers, just section name in bold
        for section_name, section_content in sections.items():
            # For brief template, remove any redundant section headers from content
            clean_content = self._clean_brief_content(section_content, section_name)
            newsletter_content.append(f"**{section_name}**\n{clean_content}\n\n")

        # Minimal footer for brief template
        newsletter_content.append(f"""---

*Generated by AI Watchtower • {datetime.utcnow().year}*

""")

        final_content = "".join(newsletter_content)
        
        # Word count check for brief template
        if config and hasattr(config, 'max_total_words'):
            final_word_count = len(final_content.split())
            if final_word_count > config.max_total_words:
                print(f"⚠️ Brief Template: Final content ({final_word_count} words) exceeds limit ({config.max_total_words} words)")
                # For brief template, be more aggressive with truncation
                from utils.word_limit_manager import WordLimitManager
                word_manager = WordLimitManager(config)
                final_content = word_manager.truncate_text(final_content, config.max_total_words)
                print(f"🔧 Brief Template: Content truncated to {len(final_content.split())} words")

        return final_content

    def _clean_brief_content(self, content: str, section_name: str) -> str:
        """Clean content for brief template - remove redundant headers"""
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip markdown headers that match section name
            if line.startswith('#') and section_name.lower() in line.lower():
                continue
                
            # Skip bold headers that match section name  
            if line.startswith('**') and line.endswith('**') and section_name.lower() in line.lower():
                continue
                
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()


class DetailedTemplate(NewsletterTemplate):
    """Detailed newsletter template with comprehensive information and word management"""

    def render(self, content: Dict[str, Any]) -> str:
        """Render detailed newsletter with full word analysis"""
        sections = content.get("sections", {})
        config = content.get("config")
        user_preferences = content.get("user_preferences")
        
        # Ensure sections respect word limits
        sections = self._ensure_section_word_limits(sections, config)

        newsletter_content = []

        # Detailed header with word information
        newsletter_content.append(
            self._format_header(
                content.get("title", "AI Watchtower Newsletter"),
                content.get("generated_at", datetime.utcnow()),
                config
            )
        )

        # Personalization info (word-conscious)
        if user_preferences:
            newsletter_content.append(
                f"""## Personalization Summary

This newsletter was tailored based on your preferences:
- **Keywords**: {", ".join(user_preferences.keywords[:5]) if user_preferences.keywords else "General AI topics"}
- **Focus Areas**: {", ".join(user_preferences.industry_focus[:3]) if user_preferences.industry_focus else "All industries"}
- **Format**: {config.format.value.title() if config else "Standard"} update
- **Articles Analyzed**: {content.get('total_articles', 0)}

"""
            )

        # Word budget analysis for detailed template
        if config and hasattr(config, 'max_total_words'):
            newsletter_content.append(
                f"""## Content Analysis

**Word Budget Management:**
- Total Word Limit: {config.max_total_words} words
- Section Limit: {config.max_section_words} words each
- Article Summary Limit: {config.max_article_summary_words} words each
- Sections: {len(sections)}
- Estimated Words per Section: ~{config.max_total_words // len(sections) if sections else 0} words

"""
            )

        # Table of contents
        newsletter_content.append("## Table of Contents\n\n")
        for i, section_name in enumerate(sections.keys(), 1):
            newsletter_content.append(
                f"{i}. [{section_name}](#{section_name.lower().replace(' ', '-')})\n"
            )
        newsletter_content.append("\n")

        # Detailed sections with word counts
        for section_name, section_content in sections.items():
            section_word_count = len(section_content.split())
            section_limit = config.max_section_words if config and hasattr(config, 'max_section_words') else "N/A"
            
            newsletter_content.append(
                f"""## {section_name}
*Section word count: {section_word_count} / {section_limit} words*

{section_content}

---

"""
            )

        # Comprehensive footer with statistics
        total_words = sum(len(content.split()) for content in sections.values())
        
        # Calculate word efficiency safely
        word_efficiency = "N/A"
        if config and hasattr(config, 'max_total_words') and config.max_total_words > 0:
            word_efficiency = f"{(total_words / config.max_total_words * 100):.1f}%"
        
        newsletter_content.append(
            f"""## Newsletter Statistics

- **Total Articles Processed**: {content.get('total_articles', 0)}
- **Sections Generated**: {len(sections)}
- **Total Content Words**: {total_words}
- **Generation Time**: {content.get('generated_at', datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S UTC')}
- **Format**: {config.format.value.title() if config else "Standard"}
- **Template**: {config.template.value.title() if config else "Detailed"}
- **Word Efficiency**: {word_efficiency}

"""
        )

        newsletter_content.append(self._format_footer())

        final_content = "".join(newsletter_content)
        
        # Final word count analysis for detailed template
        if config and hasattr(config, 'max_total_words'):
            final_word_count = len(final_content.split())
            print(f"📊 Detailed Template: Final content: {final_word_count}/{config.max_total_words} words")
            
            if final_word_count > config.max_total_words:
                print(f"⚠️ Detailed Template: Content exceeds limit by {final_word_count - config.max_total_words} words")

        return final_content


class NewsletterTemplateFactory:
    """Factory for creating newsletter templates with word limit support"""

    def __init__(self):
        self.templates = {
            TemplateType.PROFESSIONAL: ProfessionalTemplate,
            TemplateType.BRIEF: BriefTemplate,
            TemplateType.DETAILED: DetailedTemplate,
        }

    def get_template(
        self, template_type: TemplateType, format_type: NewsletterFormat
    ) -> NewsletterTemplate:
        """Get template instance"""
        template_class = self.templates.get(template_type, ProfessionalTemplate)
        return template_class(format_type)

    def preview_template_structure(self, template_type: TemplateType, format_type: NewsletterFormat) -> Dict[str, Any]:
        """Preview template structure and estimated word usage"""
        template = self.get_template(template_type, format_type)
        
        # Estimate template overhead words
        overhead_estimates = {
            TemplateType.PROFESSIONAL: {
                "header": 50,
                "executive_summary": 80,
                "footer": 60,
                "section_headers": 5,  # per section
                "total_overhead": 190,
            },
            TemplateType.BRIEF: {
                "header": 15,
                "footer": 10,
                "section_headers": 2,  # per section
                "total_overhead": 25,
            },
            TemplateType.DETAILED: {
                "header": 60,
                "personalization": 100,
                "toc": 30,
                "statistics": 100,
                "footer": 80,
                "section_headers": 10,  # per section
                "total_overhead": 370,
            },
        }
        
        template_overhead = overhead_estimates.get(template_type, overhead_estimates[TemplateType.PROFESSIONAL])
        
        return {
            "template_type": template_type.value,
            "format_type": format_type.value,
            "estimated_overhead": template_overhead,
            "recommended_for": {
                TemplateType.PROFESSIONAL: "Monthly reports, executive summaries",
                TemplateType.BRIEF: "Daily/weekly updates, quick reads", 
                TemplateType.DETAILED: "Comprehensive analysis, research reports"
            }.get(template_type, "General use"),
            "word_efficiency": {
                TemplateType.PROFESSIONAL: "Medium",
                TemplateType.BRIEF: "High",
                TemplateType.DETAILED: "Low"
            }.get(template_type, "Medium"),
        }

    def get_optimal_template_for_word_limit(self, word_limit: int, sections_count: int) -> TemplateType:
        """Recommend optimal template based on word limit"""
        
        # Calculate content space after template overhead
        brief_content_space = word_limit - 25 - (sections_count * 2)
        professional_content_space = word_limit - 190 - (sections_count * 5)
        detailed_content_space = word_limit - 370 - (sections_count * 10)
        
        if word_limit < 800:
            return TemplateType.BRIEF
        elif word_limit < 2000:
            return TemplateType.PROFESSIONAL
        else:
            return TemplateType.DETAILED if detailed_content_space > 500 else TemplateType.PROFESSIONAL