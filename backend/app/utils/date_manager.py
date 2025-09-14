"""
Date and timezone management utilities
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple
import pytz
from config import settings
from models import NewsletterFormat


class DateManager:
    """Manages dates and timezones for content collection"""
    
    def __init__(self):
        self.user_timezone = settings.get_user_timezone()
        self.utc_timezone = pytz.UTC
    
    def get_search_date_range(self, format_type: NewsletterFormat) -> Dict[str, str]:
        """Get appropriate date range for content search based on user timezone"""
        
        # Get current time in user's timezone
        current_time = settings.get_current_time()
        
        print(f"🕐 Current time in {settings.timezone}: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        if format_type == NewsletterFormat.DAILY:
            # For daily: get articles from last 24 hours in user timezone
            start_time = current_time - timedelta(hours=settings.search_hours_daily)
            end_time = current_time
            
        elif format_type == NewsletterFormat.WEEKLY:
            # For weekly: get articles from last 7 days
            start_time = current_time - timedelta(days=settings.search_days_weekly)
            end_time = current_time
            
        elif format_type == NewsletterFormat.MONTHLY:
            # For monthly: get articles from last 30 days
            start_time = current_time - timedelta(days=settings.search_days_monthly)
            end_time = current_time
            
        else:  # CUSTOM
            start_time = current_time - timedelta(days=7)  # Default fallback
            end_time = current_time
        
        # Convert to UTC for API calls (many APIs expect UTC)
        start_utc = start_time.astimezone(self.utc_timezone)
        end_utc = end_time.astimezone(self.utc_timezone)
        
        date_range = {
            "start": start_utc.strftime(settings.date_format),
            "end": end_utc.strftime(settings.date_format),
            "start_datetime": start_utc.strftime(settings.datetime_format),
            "end_datetime": end_utc.strftime(settings.datetime_format)
        }
        
        print(f"📅 Search date range ({format_type.value}):")
        print(f"   User timezone ({settings.timezone}): {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"   UTC for APIs: {start_utc.strftime('%Y-%m-%d %H:%M')} to {end_utc.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Search span: {(end_time - start_time).days} days, {(end_time - start_time).seconds // 3600} hours")
        
        return date_range
    
    def is_article_in_range(self, article_date: datetime, date_range: Dict[str, str]) -> bool:
        """Check if article date falls within the search range"""
        if not article_date:
            return True  # Include articles without dates
        
        try:
            start_date = datetime.strptime(date_range["start"], settings.date_format)
            end_date = datetime.strptime(date_range["end"], settings.date_format)
            
            # Make sure article_date is timezone-aware
            if article_date.tzinfo is None:
                article_date = pytz.UTC.localize(article_date)
            
            # Convert to UTC for comparison
            article_utc = article_date.astimezone(self.utc_timezone)
            start_utc = pytz.UTC.localize(start_date)
            end_utc = pytz.UTC.localize(end_date)
            
            return start_utc <= article_utc <= end_utc
            
        except Exception as e:
            print(f"⚠️ Error checking article date range: {e}")
            return True  # Include article if date check fails
    
    def format_display_time(self, dt: datetime, include_timezone: bool = True) -> str:
        """Format datetime for display in user's timezone"""
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        
        user_time = dt.astimezone(self.user_timezone)
        
        if include_timezone:
            return user_time.strftime(f"%B %d, %Y at %I:%M %p {self.user_timezone.zone}")
        else:
            return user_time.strftime("%B %d, %Y at %I:%M %p")
    
    def get_relative_time_description(self, format_type: NewsletterFormat) -> str:
        """Get human-readable description of search timeframe"""
        descriptions = {
            NewsletterFormat.DAILY: f"last {settings.search_hours_daily} hours",
            NewsletterFormat.WEEKLY: f"last {settings.search_days_weekly} days", 
            NewsletterFormat.MONTHLY: f"last {settings.search_days_monthly} days"
        }
        return descriptions.get(format_type, "recent period")
