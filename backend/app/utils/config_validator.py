# File: app/utils/config_validator.py - NEW FILE

from models import NewsletterConfig, NewsletterFormat, TemplateType
from typing import List


class ConfigValidator:
    """Validate and fix newsletter configurations"""

    DEFAULT_SECTIONS = [
        "Executive Highlights",
        "Technical Breakthroughs",
        "Compliance & Risk Watch",
        "Industry Applications",
        "Forward Intelligence",
    ]

    VALID_SECTIONS = [
        "Executive Highlights",
        "Technical Breakthroughs",
        "Compliance & Risk Watch",
        "Industry Applications",
        "Workforce & Operations",
        "Forward Intelligence",
        "Quick Intel",
        "Action Items",
        "Strategic Resources",
        "Weekly Highlights",
        "Daily Updates",
        "Urgent Alerts",
    ]

    @classmethod
    def validate_and_fix_config(cls, config: NewsletterConfig) -> NewsletterConfig:
        """Validate and fix newsletter configuration"""

        # 🔧 FIX: Check for invalid sections
        if not config.sections or config.sections == ["string"]:
            print(f"🔧 FIXING: Invalid sections {config.sections}, using defaults")
            config.sections = cls.DEFAULT_SECTIONS.copy()

        # 🔧 FIX: Validate each section name
        validated_sections = []
        for section in config.sections:
            if isinstance(section, str) and section.strip() and section != "string":
                validated_sections.append(section.strip())
            else:
                print(f"🔧 FIXING: Invalid section '{section}', skipping")

        if not validated_sections:
            print("🔧 FIXING: No valid sections found, using defaults")
            validated_sections = cls.DEFAULT_SECTIONS.copy()

        config.sections = validated_sections

        # 🔧 FIX: Ensure reasonable max_articles
        if config.max_articles <= 0 or config.max_articles > 100:
            config.max_articles = 20

        print(f"✅ Config validated with sections: {config.sections}")
        return config
