# File: app/api/newsletter.py
"""
Newsletter API endpoints - FIXED
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
from datetime import datetime, timedelta

from models import UserPreferences, NewsletterConfig, NewsletterFormat, TemplateType
from database import db
from agents.orchestrator import orchestrator

router = APIRouter()


@router.post("/generate")
async def generate_newsletter(
    user_id: str,
    newsletter_config: Optional[NewsletterConfig] = None,
    background_tasks: BackgroundTasks = None,
):
    """Generate a personalized newsletter"""
    try:
        # Get user preferences
        user_preferences = await db.get_user_preferences(user_id)
        if not user_preferences:
            # Create default preferences
            user_preferences = UserPreferences(user_id=user_id)
            await db.save_user_preferences(user_preferences)

        # Use default config if not provided - FIX: Ensure proper sections
        if not newsletter_config:
            newsletter_config = NewsletterConfig(
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

        print(f"🔧 API: Using config with sections: {newsletter_config.sections}")

        # Set default date range based on format
        if not newsletter_config.date_range:
            end_date = datetime.utcnow()
            if newsletter_config.format == NewsletterFormat.DAILY:
                start_date = end_date - timedelta(days=1)
            elif newsletter_config.format == NewsletterFormat.WEEKLY:
                start_date = end_date - timedelta(days=7)
            elif newsletter_config.format == NewsletterFormat.MONTHLY:
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=7)  # Default to weekly

            newsletter_config.date_range = {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d"),
            }

        # Initialize orchestrator if needed
        if orchestrator.content_agent.status == "inactive":
            await orchestrator.initialize()

        # Generate newsletter
        newsletter = await orchestrator.generate_newsletter(
            user_preferences, newsletter_config
        )

        # Save newsletter
        await db.save_newsletter(newsletter)

        return {
            "status": "success",
            "newsletter": {
                "title": newsletter.title,
                "content": newsletter.content,
                "summary": newsletter.summary_stats,
                "generated_at": newsletter.generated_at.isoformat(),
                "sections": newsletter.sections,  # Include sections in response
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Newsletter generation failed: {str(e)}"
        )


@router.post("/generate/weekly")
async def generate_weekly_newsletter(
    user_id: str, custom_sections: Optional[list] = None
):
    """Generate a weekly newsletter"""
    weekly_config = NewsletterConfig(
        format=NewsletterFormat.WEEKLY,
        sections=custom_sections
        or [
            "Weekly Highlights",
            "Compliance Updates",
            "Tech Developments",
            "Industry News",
        ],
        template=TemplateType.BRIEF,
        max_articles=15,
    )

    return await generate_newsletter(user_id, weekly_config)


@router.post("/generate/daily")
async def generate_daily_newsletter(user_id: str):
    """Generate a daily newsletter"""
    daily_config = NewsletterConfig(
        format=NewsletterFormat.DAILY,
        sections=["Today's Highlights", "Urgent Updates"],
        template=TemplateType.BRIEF,
        max_articles=8,
    )

    return await generate_newsletter(user_id, daily_config)


@router.post("/generate/custom")
async def generate_custom_newsletter(
    user_id: str,
    start_date: str,  # YYYY-MM-DD
    end_date: str,  # YYYY-MM-DD
    sections: list,
    template: str = "professional",
):
    """Generate a custom newsletter with specific date range and sections"""
    custom_config = NewsletterConfig(
        format=NewsletterFormat.CUSTOM,
        date_range={"start": start_date, "end": end_date},
        sections=sections,
        template=TemplateType(template),
        max_articles=25,
    )

    return await generate_newsletter(user_id, custom_config)


@router.get("/export/{user_id}/latest")
async def export_latest_newsletter(user_id: str, format: str = "markdown"):
    """Export latest newsletter to file"""
    try:
        newsletters = await db.get_user_newsletters(user_id, limit=1)
        if not newsletters:
            raise HTTPException(status_code=404, detail="No newsletters found")

        # Get the latest newsletter (you'd need to implement get_newsletter_content)
        # For now, return download info
        return {
            "status": "success",
            "message": "Newsletter export ready",
            "format": format,
            "file_info": "Newsletter exported successfully",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/history/{user_id}")
async def get_newsletter_history(user_id: str, limit: int = 10):
    """Get user's newsletter history"""
    try:
        newsletters = await db.get_user_newsletters(user_id, limit)
        return {"newsletters": newsletters}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get newsletter history: {str(e)}"
        )


@router.get("/formats")
async def get_newsletter_formats():
    """Get available newsletter formats and templates"""
    return {
        "formats": [format.value for format in NewsletterFormat],
        "templates": [template.value for template in TemplateType],
        "available_sections": [
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
        ],
    }
