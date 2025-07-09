"""
Newsletter template system for flexible formatting
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime

from models import NewsletterFormat, TemplateType


class NewsletterTemplate(ABC):
    """Base class for newsletter templates"""

    def __init__(self, format_type: NewsletterFormat):
        self.format_type = format_type

    @abstractmethod
    def render(self, content: Dict[str, Any]) -> str:
        """Render newsletter content"""
        pass

    def _format_header(self, title: str, generated_at: datetime) -> str:
        """Format newsletter header"""
        return f"""# {title}

**AI Watchtower** - Trusted Insights in Artificial Intelligence  
*Generated: {generated_at.strftime("%B %d, %Y at %I:%M %p UTC")}*

---

"""

    def _format_footer(self) -> str:
        """Format newsletter footer"""
        return """

---

**Thank you for choosing AI Watchtower** as your source for dependable AI intelligence.

*This newsletter was generated using advanced AI agents to provide you with the most relevant and personalized content.*

"""


class ProfessionalTemplate(NewsletterTemplate):
    """Professional newsletter template"""

    def render(self, content: Dict[str, Any]) -> str:
        """Render professional newsletter"""
        sections = content.get("sections", {})
        config = content.get("config")

        # Build newsletter content
        newsletter_content = []

        # Header
        newsletter_content.append(
            self._format_header(
                content.get("title", "AI Watchtower Newsletter"),
                content.get("generated_at", datetime.utcnow()),
            )
        )

        # Introduction
        newsletter_content.append(
            f"""## Executive Summary

Welcome to your {config.format.value} AI Watchtower briefing. This edition covers {content.get('total_articles', 0)} carefully curated articles spanning {len(sections)} key areas of AI development and governance.

"""
        )

        # Sections
        for section_name, section_content in sections.items():
            newsletter_content.append(f"## {section_name}\n\n{section_content}\n\n")

        # Footer
        newsletter_content.append(self._format_footer())

        return "".join(newsletter_content)


class BriefTemplate(NewsletterTemplate):
    """Brief newsletter template"""

    def render(self, content: Dict[str, Any]) -> str:
        """Render brief newsletter"""
        sections = content.get("sections", {})

        newsletter_content = []

        # Compact header
        newsletter_content.append(
            f"""# {content.get("title", "AI Watchtower Brief")}

*{content.get("total_articles", 0)} articles • {content.get("generated_at", datetime.utcnow()).strftime("%b %d, %Y")}*

"""
        )

        # Compact sections
        for section_name, section_content in sections.items():
            newsletter_content.append(f"**{section_name}**\n{section_content}\n\n")

        return "".join(newsletter_content)


class DetailedTemplate(NewsletterTemplate):
    """Detailed newsletter template"""

    def render(self, content: Dict[str, Any]) -> str:
        """Render detailed newsletter"""
        sections = content.get("sections", {})
        config = content.get("config")
        user_preferences = content.get("user_preferences")

        newsletter_content = []

        # Detailed header
        newsletter_content.append(
            self._format_header(
                content.get("title", "AI Watchtower Newsletter"),
                content.get("generated_at", datetime.utcnow()),
            )
        )

        # Personalization info
        if user_preferences:
            newsletter_content.append(
                f"""## Personalization Summary

This newsletter was tailored based on your preferences:
- **Keywords**: {", ".join(user_preferences.keywords[:5]) if user_preferences.keywords else "General AI topics"}
- **Focus Areas**: {", ".join(user_preferences.industry_focus[:3]) if user_preferences.industry_focus else "All industries"}
- **Format**: {config.format.value.title()} update
- **Articles Analyzed**: {content.get('total_articles', 0)}

"""
            )

        # Table of contents
        newsletter_content.append("## Table of Contents\n\n")
        for i, section_name in enumerate(sections.keys(), 1):
            newsletter_content.append(
                f"{i}. [{section_name}](#{section_name.lower().replace(' ', '-')})\n"
            )
        newsletter_content.append("\n")

        # Detailed sections
        for section_name, section_content in sections.items():
            newsletter_content.append(
                f"""## {section_name}

{section_content}

---

"""
            )

        # Footer with stats
        newsletter_content.append(
            f"""## Newsletter Statistics

- **Total Articles Processed**: {content.get('total_articles', 0)}
- **Sections Generated**: {len(sections)}
- **Generation Time**: {content.get('generated_at', datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S UTC')}
- **Format**: {config.format.value.title()}
- **Template**: {config.template.value.title()}

"""
        )

        newsletter_content.append(self._format_footer())

        return "".join(newsletter_content)


class NewsletterTemplateFactory:
    """Factory for creating newsletter templates"""

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
