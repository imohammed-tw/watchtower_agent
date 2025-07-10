# File: test_newsletter_fix.py

import asyncio
import json
from models import NewsletterConfig, NewsletterFormat, TemplateType


async def test_newsletter_generation():
    """Test the newsletter generation with proper configuration"""

    # Test 1: Create proper config
    config = NewsletterConfig(
        format=NewsletterFormat.MONTHLY,
        sections=[
            "Executive Highlights",
            "Technical Breakthroughs",
            "Compliance & Risk Watch",
            "Industry Applications",
            "Forward Intelligence",
        ],
        template=TemplateType.PROFESSIONAL,
        max_articles=20,
    )

    print("✅ Test 1: Proper config created")
    print(f"   Sections: {config.sections}")

    # Test 2: Test with invalid config (what was causing the issue)
    bad_config = NewsletterConfig(
        format=NewsletterFormat.MONTHLY,
        sections=["string"],  # This was the problem!
        template=TemplateType.PROFESSIONAL,
        max_articles=20,
    )

    print("❌ Test 2: Bad config (what you had)")
    print(f"   Sections: {bad_config.sections}")

    # Test 3: Simulate API call
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            # Proper API call with correct sections
            response = await client.post(
                "http://127.0.0.1:8000/api/v1/newsletter/generate",
                params={"user_id": "test123"},
                json={
                    "format": "monthly",
                    "sections": [
                        "Executive Highlights",
                        "Technical Breakthroughs",
                        "Compliance & Risk Watch",
                        "Industry Applications",
                        "Forward Intelligence",
                    ],
                    "template": "professional",
                    "max_articles": 20,
                },
            )

            if response.status_code == 200:
                result = response.json()
                print("✅ Test 3: API call successful!")
                print(
                    f"   Newsletter sections: {list(result['newsletter']['sections'].keys())}"
                )
            else:
                print(f"❌ Test 3: API call failed: {response.status_code}")
                print(f"   Error: {response.text}")

    except Exception as e:
        print(f"❌ Test 3: Connection error: {e}")
        print("   Make sure your server is running!")


# Run the test
if __name__ == "__main__":
    asyncio.run(test_newsletter_generation())
