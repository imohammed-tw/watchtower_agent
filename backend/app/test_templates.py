# File: app/test_templates.py
"""
Test template system
"""


def test_templates():
    """Test if templates are working"""
    try:
        from templates.newsletter_templates import NewsletterTemplateFactory
        from models import TemplateType, NewsletterFormat

        print("🧪 Testing template system...")

        factory = NewsletterTemplateFactory()
        template = factory.get_template(
            TemplateType.PROFESSIONAL, NewsletterFormat.MONTHLY
        )

        # Test data
        test_sections = {
            "Executive Highlights": "This is a test executive highlight section.",
            "Technical Breakthroughs": "This is a test technical section.",
        }

        test_content = {
            "title": "Test Newsletter",
            "sections": test_sections,
            "total_articles": 5,
            "generated_at": "2025-07-04",
        }

        result = template.render(test_content)
        print(f"✅ Template rendered successfully: {len(result)} characters")
        print("📄 Sample output:")
        print(result[:200] + "..." if len(result) > 200 else result)

        return True

    except Exception as e:
        print(f"❌ Template test failed: {e}")
        import traceback

        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    test_templates()
