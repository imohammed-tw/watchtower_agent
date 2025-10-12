# File: backend/app/api/newsletter.py - COMPLETE UPDATED VERSION WITH MANAGERS

"""
Newsletter API endpoints - Enhanced with SectionManager and WordLimitManager
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
import aiosqlite
import json
import os

from models import UserPreferences, NewsletterConfig, NewsletterFormat, TemplateType
from database import db
from agents.orchestrator import orchestrator
from config import settings
from utils.newsletter_exporter import NewsletterExporter
from utils.section_manager import SectionManager
from utils.word_limit_manager import WordLimitManager

router = APIRouter()


# Enhanced Request models with word limit controls
class GenerateNewsletterRequest(BaseModel):
    sections: Optional[List[str]] = None
    template: Optional[str] = "professional"
    max_articles: Optional[int] = 20
    max_total_words: Optional[int] = None  # Allow user override
    max_section_words: Optional[int] = None
    max_article_summary_words: Optional[int] = None


class WeeklyNewsletterRequest(BaseModel):
    sections: Optional[List[str]] = None
    template: Optional[str] = "professional"
    max_articles: Optional[int] = 20
    max_total_words: Optional[int] = None
    max_section_words: Optional[int] = None
    max_article_summary_words: Optional[int] = None


class DailyNewsletterRequest(BaseModel):
    sections: Optional[List[str]] = None
    template: Optional[str] = "brief"
    max_articles: Optional[int] = 8
    max_total_words: Optional[int] = None
    max_section_words: Optional[int] = None
    max_article_summary_words: Optional[int] = None


class CustomNewsletterRequest(BaseModel):
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    sections: List[str]
    template: Optional[str] = "professional"
    max_articles: Optional[int] = 25
    max_total_words: Optional[int] = None
    max_section_words: Optional[int] = None
    max_article_summary_words: Optional[int] = None


def _get_default_word_limits(format_type: NewsletterFormat) -> dict:
    """Get default word limits based on newsletter format"""
    limits = {
        NewsletterFormat.DAILY: {
            "max_total_words": 1000,
            "max_section_words": 400,
            "max_article_summary_words": 50
        },
        NewsletterFormat.WEEKLY: {
            "max_total_words": 4000,
            "max_section_words": 500,
            "max_article_summary_words": 50
        },
        NewsletterFormat.MONTHLY: {
            "max_total_words": 2500,
            "max_section_words": 500,
            "max_article_summary_words": 80
        },
        NewsletterFormat.CUSTOM: {
            "max_total_words": 2000,
            "max_section_words": 400,
            "max_article_summary_words": 70
        }
    }
    return limits.get(format_type, limits[NewsletterFormat.MONTHLY])


def _create_newsletter_config(format_type: NewsletterFormat, request_body, user_sections: List[str] = None) -> NewsletterConfig:
    """Create newsletter configuration with proper sections and word limits - FIXED PERSONALIZATION"""
    
    # 🔧 FIX: Properly handle user sections vs defaults
    if user_sections and len(user_sections) > 0:
        # User provided custom sections - validate but don't replace with defaults
        print(f"📋 USER PROVIDED custom sections: {user_sections}")
        
        # Only validate format, don't change the sections
        from utils.section_manager import SectionManager
        
        # Check if sections are valid but preserve user choice
        valid_sections = []
        available_sections = list(SectionManager.get_section_specifications().keys()) if hasattr(SectionManager, 'get_section_specifications') else user_sections
        
        for section in user_sections:
            if section and isinstance(section, str) and section.strip():
                valid_sections.append(section.strip())
                print(f"✅ Accepted user section: '{section}'")
            else:
                print(f"⚠️ Skipped invalid section: '{section}'")
        
        # Use user sections if we have any valid ones
        if len(valid_sections) >= 1:
            sections = valid_sections
            print(f"📋 Using {len(sections)} validated user sections: {sections}")
        else:
            # Fallback to defaults only if no valid user sections
            print("⚠️ No valid user sections found, falling back to defaults")
            sections = SectionManager.get_required_sections(format_type) if hasattr(SectionManager, 'get_required_sections') else [
                "Executive Summary", "Technology Breakthroughs", "Market Intelligence"
            ]
    else:
        # No user sections provided, use format defaults
        print(f"📋 No user sections provided, using defaults for {format_type.value}")
        try:
            from utils.section_manager import SectionManager
            sections = SectionManager.get_required_sections(format_type)
        except ImportError:
            # Fallback if SectionManager not available
            default_sections = {
                NewsletterFormat.DAILY: ["Executive Summary", "Security & Risk Alerts"],
                NewsletterFormat.WEEKLY: ["Executive Summary", "Regulatory & Compliance Watch", "Security & Risk Alerts", "Technology Breakthroughs", "Market Intelligence"],
                NewsletterFormat.MONTHLY: ["Executive Summary", "Regulatory & Compliance Watch", "Security & Risk Alerts", "Technology Breakthroughs", "Market Intelligence"],
                NewsletterFormat.CUSTOM: ["Executive Summary", "Technology Breakthroughs", "Market Intelligence"]
            }
            sections = default_sections.get(format_type, default_sections[NewsletterFormat.MONTHLY])
        
        print(f"📋 Using default {format_type.value} sections: {sections}")
    
    # Get default word limits for format
    default_limits = _get_default_word_limits(format_type)
    
    # Use request values or defaults
    max_total_words = getattr(request_body, 'max_total_words', None) or default_limits["max_total_words"]
    max_section_words = getattr(request_body, 'max_section_words', None) or default_limits["max_section_words"]
    max_article_summary_words = getattr(request_body, 'max_article_summary_words', None) or default_limits["max_article_summary_words"]
    max_articles = getattr(request_body, 'max_articles', None) or (20 if format_type == NewsletterFormat.MONTHLY else 15 if format_type == NewsletterFormat.WEEKLY else 8)
    template = getattr(request_body, 'template', None) or ("professional" if format_type == NewsletterFormat.MONTHLY else "brief")
    
    # Create config with word limits
    config = NewsletterConfig(
        format=format_type,
        sections=sections,
        template=TemplateType(template),
        max_articles=max_articles,
        max_total_words=max_total_words,
        max_section_words=max_section_words,
        max_article_summary_words=max_article_summary_words,
    )
    
    print(f"✅ {format_type.value.title()} Config Created:")
    print(f"   Sections: {config.sections} ({'USER-DEFINED' if user_sections else 'DEFAULT'})")
    print(f"   Word Limits: Total={config.max_total_words}, Section={config.max_section_words}, Article={config.max_article_summary_words}")
    
    return config

@router.post("/generate")
async def generate_newsletter(
    user_id: str,
    request_body: Optional[GenerateNewsletterRequest] = None,
):
    """Generate a monthly newsletter with proper sections and word limits"""
    try:
        print(f"📝 Monthly newsletter request for user: {user_id}")
        
        # Get user preferences
        user_preferences = await db.get_user_preferences(user_id)
        if not user_preferences:
            user_preferences = UserPreferences(user_id=user_id)
            await db.save_user_preferences(user_preferences)

        # Create newsletter config using helper
        user_sections = request_body.sections if request_body else None
        newsletter_config = _create_newsletter_config(
            NewsletterFormat.MONTHLY, 
            request_body, 
            user_sections
        )

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
                    "sections": newsletter_config.sections,
                    "template": newsletter_config.template.value,
                    "date_range": newsletter_config.date_range,
                    "word_limits": {
                        "total": newsletter_config.max_total_words,
                        "per_section": newsletter_config.max_section_words,
                        "per_article": newsletter_config.max_article_summary_words
                    }
                }
            },
        }

    except Exception as e:
        print(f"❌ Monthly newsletter generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Newsletter generation failed: {str(e)}"
        )


@router.post("/generate/weekly")
async def generate_weekly_newsletter(
    user_id: str, 
    request_body: Optional[WeeklyNewsletterRequest] = None,
):
    """Generate a weekly newsletter with proper sections and word limits"""
    try:
        print(f"📝 Weekly newsletter request for user: {user_id}")
        
        # Get user preferences
        user_preferences = await db.get_user_preferences(user_id)
        if not user_preferences:
            user_preferences = UserPreferences(user_id=user_id)
            await db.save_user_preferences(user_preferences)

        # Create weekly config using helper
        user_sections = request_body.sections if request_body else None
        weekly_config = _create_newsletter_config(
            NewsletterFormat.WEEKLY, 
            request_body, 
            user_sections
        )

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
        newsletter = await orchestrator.generate_newsletter(user_preferences, weekly_config)
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
                    "sections": weekly_config.sections,
                    "template": weekly_config.template.value,
                    "date_range": weekly_config.date_range,
                    "word_limits": {
                        "total": weekly_config.max_total_words,
                        "per_section": weekly_config.max_section_words,
                        "per_article": weekly_config.max_article_summary_words
                    }
                }
            },
        }

    except Exception as e:
        print(f"❌ Weekly newsletter generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Weekly newsletter generation failed: {str(e)}")


@router.post("/generate/daily")
async def generate_daily_newsletter(
    user_id: str,
    request_body: Optional[DailyNewsletterRequest] = None,
):
    """Generate a daily newsletter with timezone-aware date range"""
    try:
        print(f"📝 Daily newsletter request for user: {user_id}")
        print(f"🕐 User timezone: {settings.timezone}")
        
        # Get user preferences
        user_preferences = await db.get_user_preferences(user_id)
        if not user_preferences:
            user_preferences = UserPreferences(user_id=user_id)
            await db.save_user_preferences(user_preferences)

        # Create daily config using helper
        user_sections = request_body.sections if request_body else None
        daily_config = _create_newsletter_config(
            NewsletterFormat.DAILY, 
            request_body, 
            user_sections
        )

        # 🔧 FIX: Use timezone-aware date calculation
        from utils.date_manager import DateManager
        date_manager = DateManager()
        timezone_date_range = date_manager.get_search_date_range(NewsletterFormat.DAILY)
        daily_config.date_range = timezone_date_range
        
        print(f"📅 Daily search range: {timezone_date_range['start']} to {timezone_date_range['end']}")
        print(f"🔍 Searching for articles from: {date_manager.get_relative_time_description(NewsletterFormat.DAILY)}")

        # Initialize orchestrator if needed
        if orchestrator.content_agent.status == "inactive":
            await orchestrator.initialize()

        # Generate newsletter
        newsletter = await orchestrator.generate_newsletter(user_preferences, daily_config)
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
                    "sections": daily_config.sections,
                    "template": daily_config.template.value,
                    "date_range": daily_config.date_range,
                    "timezone": settings.timezone,
                    "search_description": date_manager.get_relative_time_description(NewsletterFormat.DAILY),
                    "word_limits": {
                        "total": daily_config.max_total_words,
                        "per_section": daily_config.max_section_words,
                        "per_article": daily_config.max_article_summary_words
                    }
                }
            },
        }

    except Exception as e:
        print(f"❌ Daily newsletter generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Daily newsletter generation failed: {str(e)}")


@router.post("/generate/custom")
async def generate_custom_newsletter(
    user_id: str,
    request_body: CustomNewsletterRequest,
):
    """Generate a custom newsletter with specific date range, sections and word limits"""
    try:
        print(f"📝 Custom newsletter request for user: {user_id}")
        print(f"📅 Date range: {request_body.start_date} to {request_body.end_date}")
        
        # Get user preferences
        user_preferences = await db.get_user_preferences(user_id)
        if not user_preferences:
            user_preferences = UserPreferences(user_id=user_id)
            await db.save_user_preferences(user_preferences)

        # Create custom config using helper
        custom_config = _create_newsletter_config(
            NewsletterFormat.CUSTOM, 
            request_body, 
            request_body.sections
        )

        # Set custom date range
        custom_config.date_range = {
            "start": request_body.start_date, 
            "end": request_body.end_date
        }

        # Initialize orchestrator if needed
        if orchestrator.content_agent.status == "inactive":
            await orchestrator.initialize()

        # Generate newsletter
        newsletter = await orchestrator.generate_newsletter(user_preferences, custom_config)
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
                    "sections": custom_config.sections,
                    "template": custom_config.template.value,
                    "date_range": custom_config.date_range,
                    "word_limits": {
                        "total": custom_config.max_total_words,
                        "per_section": custom_config.max_section_words,
                        "per_article": custom_config.max_article_summary_words
                    }
                }
            },
        }

    except Exception as e:
        print(f"❌ Custom newsletter generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Custom newsletter generation failed: {str(e)}")


@router.get("/formats")
async def get_newsletter_formats():
    """Get available newsletter formats, templates, sections and word limit recommendations"""
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
            "daily": SectionManager.get_default_sections(NewsletterFormat.DAILY),
            "weekly": SectionManager.get_default_sections(NewsletterFormat.WEEKLY), 
            "monthly": SectionManager.get_default_sections(NewsletterFormat.MONTHLY),
            "custom": SectionManager.get_default_sections(NewsletterFormat.CUSTOM)
        },
        "word_limit_defaults": {
            "daily": _get_default_word_limits(NewsletterFormat.DAILY),
            "weekly": _get_default_word_limits(NewsletterFormat.WEEKLY),
            "monthly": _get_default_word_limits(NewsletterFormat.MONTHLY),
            "custom": _get_default_word_limits(NewsletterFormat.CUSTOM)
        }
    }


@router.get("/word-limits/{format_type}")
async def get_word_limits_for_format(format_type: str):
    """Get recommended word limits for a specific format"""
    try:
        format_enum = NewsletterFormat(format_type.lower())
        limits = _get_default_word_limits(format_enum)
        sections = SectionManager.get_default_sections(format_enum)
        
        # Calculate words per section
        words_per_section = limits["max_total_words"] // len(sections) if sections else 0
        
        return {
            "format": format_type,
            "word_limits": limits,
            "default_sections": sections,
            "calculated_words_per_section": words_per_section,
            "recommendations": {
                "total_words": f"Keep total content under {limits['max_total_words']} words for optimal readability",
                "section_words": f"Each section should be around {limits['max_section_words']} words",
                "article_summaries": f"Article summaries limited to {limits['max_article_summary_words']} words each"
            }
        }
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid format type: {format_type}. Use: daily, weekly, monthly, custom")


# EXPORT ENDPOINTS
@router.get("/export/{user_id}/debug")
async def debug_newsletter_database(user_id: str):
    """Debug what's actually in the database"""
    try:
        # Check database path
        db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
        
        print(f"🔍 Database path: {db_path}")
        print(f"🔍 Database exists: {os.path.exists(db_path)}")
        
        if not os.path.exists(db_path):
            return {
                "error": "Database file not found",
                "db_path": db_path,
                "exists": False
            }
        
        # Check what's in the database
        async with aiosqlite.connect(db_path) as database:
            # Count newsletters for this user
            cursor = await database.execute(
                "SELECT COUNT(*) FROM newsletters WHERE user_id = ?", 
                (user_id,)
            )
            count = await cursor.fetchone()
            
            # Get all newsletters for this user
            cursor = await database.execute(
                """
                SELECT id, title, LENGTH(content) as content_length, generated_at, total_articles
                FROM newsletters 
                WHERE user_id = ?
                ORDER BY generated_at DESC
                """,
                (user_id,)
            )
            newsletters = await cursor.fetchall()
            
            # Get latest newsletter content preview and word count
            latest_content = None
            latest_word_count = 0
            if newsletters:
                cursor = await database.execute(
                    "SELECT content FROM newsletters WHERE user_id = ? ORDER BY generated_at DESC LIMIT 1",
                    (user_id,)
                )
                content_row = await cursor.fetchone()
                if content_row:
                    full_content = content_row[0]
                    latest_word_count = len(full_content.split())
                    latest_content = full_content[:300] + "..." if len(full_content) > 300 else full_content
            
            return {
                "db_path": db_path,
                "newsletter_count": count[0] if count else 0,
                "newsletters": [
                    {
                        "id": row[0],
                        "title": row[1], 
                        "content_length": row[2],
                        "generated_at": row[3],
                        "total_articles": row[4]
                    } for row in newsletters
                ],
                "latest_content_preview": latest_content,
                "latest_word_count": latest_word_count
            }
            
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.get("/export/{user_id}/latest")
async def export_latest_newsletter(user_id: str, format: str = "html"):
    """Export latest newsletter - FIXED VERSION with proper Newsletter object"""
    try:
        print(f"📤 Starting export for user: {user_id}, format: {format}")
        
        # Get database path
        db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
        
        if not os.path.exists(db_path):
            raise HTTPException(status_code=500, detail=f"Database file not found: {db_path}")
        
        # Get latest newsletter from database
        async with aiosqlite.connect(db_path) as database:
            cursor = await database.execute(
                """
                SELECT id, user_id, title, content, config, sections, total_articles, generated_at
                FROM newsletters 
                WHERE user_id = ?
                ORDER BY generated_at DESC
                LIMIT 1
                """,
                (user_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                raise HTTPException(
                    status_code=404, 
                    detail=f"No newsletters found for user {user_id}. Generate a newsletter first using /generate/* endpoints."
                )

            # Extract data
            newsletter_id, user_id_db, title, content, config_json, sections_json, total_articles, generated_at = row
            
            print(f"📋 Found newsletter: {title}")
            print(f"📄 Content length: {len(content)} characters")
            print(f"📊 Word count: {len(content.split())} words")
            
            if len(content) < 100:
                raise HTTPException(
                    status_code=500, 
                    detail="Newsletter content is too short. Generate a proper newsletter first."
                )
            
            # Parse JSON data
            try:
                config_data = json.loads(config_json)
                sections_data = json.loads(sections_json)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=500, detail="Invalid newsletter data in database")

        # Create proper Newsletter object with all methods
        from models import Newsletter, NewsletterConfig, NewsletterFormat, TemplateType
        
        # Reconstruct the NewsletterConfig object
        try:
            newsletter_format = NewsletterFormat(config_data.get('format', 'monthly'))
            template_type = TemplateType(config_data.get('template', 'professional'))
            
            newsletter_config = NewsletterConfig(
                format=newsletter_format,
                sections=config_data.get('sections', []),
                template=template_type,
                max_articles=config_data.get('max_articles', 20),
                max_total_words=config_data.get('max_total_words', 2000),
                max_section_words=config_data.get('max_section_words', 400),
                max_article_summary_words=config_data.get('max_article_summary_words', 80),
                date_range=config_data.get('date_range', {}),
                include_links=config_data.get('include_links', True),
                include_summary=config_data.get('include_summary', True)
            )
            
        except Exception as e:
            print(f"⚠️ Error reconstructing NewsletterConfig: {e}")
            # Fallback to basic config
            newsletter_config = NewsletterConfig(
                format=NewsletterFormat.MONTHLY,
                sections=list(sections_data.keys()) if sections_data else [],
                template=TemplateType.PROFESSIONAL,
                max_total_words=2000,
                max_section_words=400,
                max_article_summary_words=80
            )
        
        # Create proper Newsletter object
        newsletter = Newsletter(
            user_id=user_id_db,
            title=title,
            content=content,
            config=newsletter_config,
            total_articles=total_articles,
            sections=sections_data,
            generated_at=datetime.fromisoformat(generated_at)
        )
        
        print(f"✅ Created proper Newsletter object with word analysis capabilities")
        
        # Test word analysis
        try:
            word_analysis = newsletter.get_detailed_word_analysis()
            print(f"📊 Word analysis: {word_analysis['total_analysis']['actual_words']} words")
        except Exception as e:
            print(f"⚠️ Word analysis error: {e}")
        
        # Initialize exporter
        from utils.newsletter_exporter import NewsletterExporter
        exporter = NewsletterExporter()
        
        # Create export file
        if format.lower() == "html":
            filepath = exporter.export_to_html(newsletter)
            media_type = "text/html"
        elif format.lower() in ["markdown", "md"]:
            filepath = exporter.export_to_markdown(newsletter)
            media_type = "text/markdown"
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'html' or 'markdown'")
        
        # Verify export was successful
        if not os.path.exists(filepath):
            raise HTTPException(status_code=500, detail="Export file creation failed")
            
        file_size = os.path.getsize(filepath)
        print(f"✅ Export successful: {filepath} ({file_size} bytes)")
        
        filename = os.path.basename(filepath)
        
        # Return file for download
        return FileResponse(
            filepath, 
            filename=filename, 
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise


@router.get("/export/by-id/{newsletter_id}")
async def export_newsletter_by_id(newsletter_id: str, format: str = "html"):
    """Export a specific newsletter by id in html or markdown."""
    try:
        db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
        if not os.path.exists(db_path):
            raise HTTPException(status_code=500, detail=f"Database file not found: {db_path}")

        async with aiosqlite.connect(db_path) as database:
            cursor = await database.execute(
                """
                SELECT id, user_id, title, content, config, sections, total_articles, generated_at
                FROM newsletters 
                WHERE id = ?
                """,
                (newsletter_id,)
            )
            row = await cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Newsletter not found")

            id_db, user_id_db, title, content, config_json, sections_json, total_articles, generated_at = row

            if not content or len(content) < 50:
                raise HTTPException(status_code=500, detail="Newsletter content is too short or empty")

            try:
                import json as _json
                from datetime import datetime as _dt
                config_data = _json.loads(config_json) if config_json else {}
                sections_data = _json.loads(sections_json) if sections_json else []
            except Exception:
                config_data, sections_data = {}, []

        from models import Newsletter as _Newsletter
        newsletter = _Newsletter(
            user_id=user_id_db,
            title=title,
            content=content,
            config=config_data,
            total_articles=total_articles,
            sections=sections_data,
            generated_at=_dt.fromisoformat(generated_at) if isinstance(generated_at, str) else generated_at,
        )

        exporter = NewsletterExporter()
        if format.lower() == "html":
            filepath = exporter.export_to_html(newsletter)
            media_type = "text/html"
        elif format.lower() in ["markdown", "md"]:
            filepath = exporter.export_to_markdown(newsletter)
            media_type = "text/markdown"
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'html' or 'markdown'")

        if not os.path.exists(filepath):
            raise HTTPException(status_code=500, detail="Export file creation failed")

        filename = os.path.basename(filepath)
        return FileResponse(
            filepath,
            filename=filename,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export by id failed: {str(e)}")
    except Exception as e:
        print(f"❌ Export failed: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/get/{newsletter_id}")
async def get_newsletter_by_id(newsletter_id: str):
    """Return a newsletter by id as JSON for on-page viewing (no file download)."""
    try:
        db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
        if not os.path.exists(db_path):
            raise HTTPException(status_code=500, detail=f"Database file not found: {db_path}")

        async with aiosqlite.connect(db_path) as database:
            cursor = await database.execute(
                """
                SELECT id, user_id, title, content, config, sections, total_articles, generated_at, format
                FROM newsletters 
                WHERE id = ?
                """,
                (newsletter_id,)
            )
            row = await cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Newsletter not found")

            id_db, user_id_db, title, content, config_json, sections_json, total_articles, generated_at, fmt = row
            try:
                config_data = json.loads(config_json) if config_json else {}
                sections_data = json.loads(sections_json) if sections_json else {}
            except Exception:
                config_data, sections_data = {}, {}

        from models import Newsletter, NewsletterConfig, NewsletterFormat, TemplateType
        try:
            newsletter_format = NewsletterFormat((fmt or config_data.get('format') or 'monthly'))
            template_type = TemplateType(config_data.get('template', 'professional'))
            cfg = NewsletterConfig(
                format=newsletter_format,
                sections=config_data.get('sections', list(sections_data.keys()) if isinstance(sections_data, dict) else []),
                template=template_type,
                max_articles=config_data.get('max_articles', 20),
                max_total_words=config_data.get('max_total_words', 2000),
                max_section_words=config_data.get('max_section_words', 400),
                max_article_summary_words=config_data.get('max_article_summary_words', 80),
                date_range=config_data.get('date_range', {}),
            )
        except Exception:
            cfg = NewsletterConfig()

        newsletter = Newsletter(
            user_id=user_id_db,
            title=title,
            content=content,
            config=cfg,
            total_articles=total_articles,
            sections=sections_data if isinstance(sections_data, dict) else {},
            generated_at=datetime.fromisoformat(generated_at) if isinstance(generated_at, str) else generated_at,
        )

        return {
            "id": newsletter_id,
            "title": newsletter.title,
            "content": newsletter.content,
            "summary": newsletter.summary_stats,
            "generated_at": newsletter.generated_at.isoformat(),
            "sections": newsletter.sections,
            "config": {
                "format": newsletter.config.format.value,
                "template": newsletter.config.template.value,
                "date_range": newsletter.config.date_range,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get newsletter failed: {str(e)}")

@router.get("/history/{user_id}")
async def get_newsletter_history(user_id: str, limit: int = 10):
    """Get user's newsletter history with word counts"""
    try:
        newsletters = await db.get_user_newsletters(user_id, limit)
        
        # Add word count information
        enhanced_newsletters = []
        for newsletter in newsletters:
            # Get full content to calculate word count
            if newsletter.get('id'):
                db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
                async with aiosqlite.connect(db_path) as database:
                    cursor = await database.execute(
                        "SELECT content, format, config FROM newsletters WHERE id = ?",
                        (newsletter['id'],)
                    )
                    content_row = await cursor.fetchone()
                    if content_row:
                        word_count = len(content_row[0].split())
                        newsletter['word_count'] = word_count
                        # Prefer explicit format column; fallback to config
                        if content_row[1]:
                            newsletter['format'] = content_row[1]
                        else:
                            try:
                                cfg = json.loads(content_row[2] or '{}')
                                newsletter['format'] = cfg.get('format', 'unknown')
                            except Exception:
                                newsletter['format'] = 'unknown'
            
            enhanced_newsletters.append(newsletter)
        
        return {"newsletters": enhanced_newsletters}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get newsletter history: {str(e)}"
        )