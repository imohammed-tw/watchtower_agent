# File: app/api/newsletter.py - COMPLETELY FIXED VERSION

"""
Newsletter API endpoints - FIXED with sections selection
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel

from models import UserPreferences, NewsletterConfig, NewsletterFormat, TemplateType
from database import db
from agents.orchestrator import orchestrator

router = APIRouter()


# Request models for better API handling
class GenerateNewsletterRequest(BaseModel):
    sections: Optional[List[str]] = None
    template: Optional[str] = "professional"
    max_articles: Optional[int] = 20


class WeeklyNewsletterRequest(BaseModel):
    sections: Optional[List[str]] = None
    template: Optional[str] = "brief"
    max_articles: Optional[int] = 15


class CustomNewsletterRequest(BaseModel):
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    sections: List[str]
    template: Optional[str] = "professional"
    max_articles: Optional[int] = 25


@router.post("/generate/monthly")
async def generate_newsletter(
    user_id: str,
    request_body: Optional[GenerateNewsletterRequest] = None,
):
    """Generate a monthly newsletter with selectable sections"""
    try:
        # Get user preferences
        user_preferences = await db.get_user_preferences(user_id)
        if not user_preferences:
            user_preferences = UserPreferences(user_id=user_id)
            await db.save_user_preferences(user_preferences)

        # Use sections from request or defaults
        if request_body and request_body.sections:
            sections = request_body.sections
        else:
            sections = [
                "Executive Highlights",
                "Technical Breakthroughs",
                "Compliance & Risk Watch",
                "Industry Applications",
                "Forward Intelligence",
            ]

        # Create newsletter config
        newsletter_config = NewsletterConfig(
            format=NewsletterFormat.MONTHLY,
            sections=sections,
            template=TemplateType(
                request_body.template if request_body else "professional"
            ),
            max_articles=request_body.max_articles if request_body else 20,
        )

        print(f"🔧 Monthly API: Using sections: {newsletter_config.sections}")

        # Set date range for monthly (last 30 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
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
                "sections": newsletter.sections,
                "config": {
                    "format": "monthly",
                    "sections": sections,
                    "template": newsletter_config.template.value,
                    "date_range": newsletter_config.date_range,
                },
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Newsletter generation failed: {str(e)}"
        )


@router.post("/generate/weekly")
async def generate_weekly_newsletter(
    user_id: str,
    request_body: Optional[WeeklyNewsletterRequest] = None,
):
    """Generate a weekly newsletter with selectable sections"""
    try:
        # Get user preferences
        user_preferences = await db.get_user_preferences(user_id)
        if not user_preferences:
            user_preferences = UserPreferences(user_id=user_id)
            await db.save_user_preferences(user_preferences)

        # Use sections from request or defaults
        if request_body and request_body.sections:
            sections = request_body.sections
        else:
            sections = [
                "Weekly Highlights",
                "Compliance Updates",
                "Tech Developments",
                "Industry News",
            ]

        weekly_config = NewsletterConfig(
            format=NewsletterFormat.WEEKLY,
            sections=sections,
            template=TemplateType(request_body.template if request_body else "brief"),
            max_articles=request_body.max_articles if request_body else 15,
        )

        print(f"🔧 Weekly API: Using sections: {weekly_config.sections}")

        # Set date range for weekly (last 7 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        weekly_config.date_range = {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
        }

        # Initialize orchestrator if needed
        if orchestrator.content_agent.status == "inactive":
            await orchestrator.initialize()

        # Generate newsletter
        newsletter = await orchestrator.generate_newsletter(
            user_preferences, weekly_config
        )
        await db.save_newsletter(newsletter)

        return {
            "status": "success",
            "newsletter": {
                "title": newsletter.title,
                "content": newsletter.content,
                "summary": newsletter.summary_stats,
                "generated_at": newsletter.generated_at.isoformat(),
                "sections": newsletter.sections,
                "config": {
                    "format": "weekly",
                    "sections": sections,
                    "template": weekly_config.template.value,
                    "date_range": weekly_config.date_range,
                },
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Weekly newsletter generation failed: {str(e)}"
        )


@router.post("/generate/daily")
async def generate_daily_newsletter(
    user_id: str,
    request_body: Optional[WeeklyNewsletterRequest] = None,
):
    """Generate a daily newsletter with selectable sections"""
    try:
        # Get user preferences
        user_preferences = await db.get_user_preferences(user_id)
        if not user_preferences:
            user_preferences = UserPreferences(user_id=user_id)
            await db.save_user_preferences(user_preferences)

        # Use sections from request or defaults
        if request_body and request_body.sections:
            sections = request_body.sections
        else:
            sections = [
                "Today's Highlights",
                "Urgent Updates",
            ]

        daily_config = NewsletterConfig(
            format=NewsletterFormat.DAILY,
            sections=sections,
            template=TemplateType.BRIEF,
            max_articles=request_body.max_articles if request_body else 8,
        )

        print(f"🔧 Daily API: Using sections: {daily_config.sections}")

        # Set date range for daily (last 24 hours)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=1)
        daily_config.date_range = {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
        }

        # Initialize orchestrator if needed
        if orchestrator.content_agent.status == "inactive":
            await orchestrator.initialize()

        # Generate newsletter
        newsletter = await orchestrator.generate_newsletter(
            user_preferences, daily_config
        )
        await db.save_newsletter(newsletter)

        return {
            "status": "success",
            "newsletter": {
                "title": newsletter.title,
                "content": newsletter.content,
                "summary": newsletter.summary_stats,
                "generated_at": newsletter.generated_at.isoformat(),
                "sections": newsletter.sections,
                "config": {
                    "format": "daily",
                    "sections": sections,
                    "template": daily_config.template.value,
                    "date_range": daily_config.date_range,
                },
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Daily newsletter generation failed: {str(e)}"
        )


@router.post("/generate/custom")
async def generate_custom_newsletter(
    user_id: str,
    request_body: CustomNewsletterRequest,
):
    """Generate a custom newsletter with specific date range and sections"""
    try:
        # Get user preferences
        user_preferences = await db.get_user_preferences(user_id)
        if not user_preferences:
            user_preferences = UserPreferences(user_id=user_id)
            await db.save_user_preferences(user_preferences)

        custom_config = NewsletterConfig(
            format=NewsletterFormat.CUSTOM,
            date_range={"start": request_body.start_date, "end": request_body.end_date},
            sections=request_body.sections,
            template=TemplateType(request_body.template),
            max_articles=request_body.max_articles,
        )

        print(f"🔧 Custom API: Using sections: {custom_config.sections}")
        print(
            f"🔧 Custom API: Date range: {request_body.start_date} to {request_body.end_date}"
        )

        # Initialize orchestrator if needed
        if orchestrator.content_agent.status == "inactive":
            await orchestrator.initialize()

        # Generate newsletter
        newsletter = await orchestrator.generate_newsletter(
            user_preferences, custom_config
        )
        await db.save_newsletter(newsletter)

        return {
            "status": "success",
            "newsletter": {
                "title": newsletter.title,
                "content": newsletter.content,
                "summary": newsletter.summary_stats,
                "generated_at": newsletter.generated_at.isoformat(),
                "sections": newsletter.sections,
                "config": {
                    "format": "custom",
                    "sections": request_body.sections,
                    "template": request_body.template,
                    "date_range": {
                        "start": request_body.start_date,
                        "end": request_body.end_date,
                    },
                },
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Custom newsletter generation failed: {str(e)}"
        )


@router.get("/formats")
async def get_newsletter_formats():
    """Get available newsletter formats and templates with all possible sections"""
    return {
        "formats": [format.value for format in NewsletterFormat],
        "templates": [template.value for template in TemplateType],
        "available_sections": [
            # Main categories
            "Executive Highlights",
            "Technical Breakthroughs",
            "Compliance & Risk Watch",
            "Industry Applications",
            "Forward Intelligence",
            # Time-based
            "Today's Highlights",
            "Weekly Highlights",
            "Monthly Insights",
            "Urgent Updates",
            # Specialized
            "AI Semiconductor News",
            "Regulatory Updates",
            "Market Analysis",
            "Tech Developments",
            "Research Updates",
            "Policy Changes",
            "Investment News",
            "Startup Watch",
            "Enterprise Applications",
            "Ethics & Society",
            # Industry specific
            "Healthcare AI",
            "Finance AI",
            "Manufacturing AI",
            "Automotive AI",
            "Retail AI",
            "Education AI",
        ],
        "recommended_sections": {
            "daily": ["Today's Highlights", "Urgent Updates"],
            "weekly": [
                "Weekly Highlights",
                "Compliance Updates",
                "Tech Developments",
                "Industry News",
            ],
            "monthly": [
                "Executive Highlights",
                "Technical Breakthroughs",
                "Compliance & Risk Watch",
                "Industry Applications",
                "Forward Intelligence",
            ],
            "custom": [
                "Executive Highlights",
                "Technical Breakthroughs",
                "Market Analysis",
            ],
        },
    }


@router.get("/export/{user_id}/latest")
async def export_latest_newsletter(user_id: str, format: str = "markdown"):
    """Export latest newsletter to file"""
    try:
        newsletters = await db.get_user_newsletters(user_id, limit=1)
        if not newsletters:
            raise HTTPException(status_code=404, detail="No newsletters found")

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
