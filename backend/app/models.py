# File: app/models.py
"""
Data models for AI Watchtower
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class NewsletterFormat(str, Enum):
    """Newsletter format types"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class TemplateType(str, Enum):
    """Newsletter template types"""

    PROFESSIONAL = "professional"
    BRIEF = "brief"
    DETAILED = "detailed"
    CUSTOM = "custom"


class UserPreferences(BaseModel):
    """User preferences for newsletter personalization"""

    user_id: str
    keywords: List[str] = Field(default_factory=list)
    preferred_sources: List[str] = Field(default_factory=list)
    excluded_sources: List[str] = Field(default_factory=list)
    industry_focus: List[str] = Field(default_factory=list)
    content_types: List[str] = Field(
        default_factory=lambda: ["regulatory", "technical", "market"]
    )
    urgency_threshold: int = Field(default=5, ge=1, le=10)
    relevance_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class NewsletterConfig(BaseModel):
    """Configuration for newsletter generation"""

    format: NewsletterFormat = NewsletterFormat.MONTHLY
    date_range: Dict[str, str] = Field(
        default_factory=dict
    )  # {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
    sections: List[str] = Field(
        default_factory=lambda: [
            "Executive Highlights",
            "Technical Breakthroughs",
            "Compliance & Risk Watch",
            "Industry Applications",
            "Forward Intelligence",
        ]
    )
    max_articles: int = Field(default=20, ge=5, le=100)
    template: TemplateType = TemplateType.PROFESSIONAL
    include_links: bool = True
    include_summary: bool = True


class Article(BaseModel):
    """Article data model"""

    title: str
    url: HttpUrl
    source: str
    summary: str
    content: Optional[str] = None
    published_at: Optional[datetime] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    topic: Optional[str] = None
    quality_score: float = 0.0


class AnalyzedArticle(BaseModel):
    """Article with analysis results"""

    article: Article
    relevance_score: float
    sentiment: str  # positive, negative, neutral
    impact_score: int  # 1-10
    urgency_score: int  # 1-10
    assigned_section: str
    personalization_score: float
    processed_at: datetime = Field(default_factory=datetime.utcnow)


class Newsletter(BaseModel):
    """Newsletter model"""

    user_id: str
    title: str
    content: str
    config: NewsletterConfig
    total_articles: int
    sections: Dict[str, str]  # section_name -> content
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def summary_stats(self) -> Dict[str, Any]:
        """Get newsletter summary statistics"""
        return {
            "format": self.config.format,
            "total_articles": self.total_articles,
            "sections_count": len(self.sections),
            "generation_time": self.generated_at.isoformat(),
            "word_count": len(self.content.split()),
        }


class WorkflowState(BaseModel):
    """Workflow state for agent coordination"""

    workflow_id: str
    user_id: str
    user_preferences: UserPreferences
    newsletter_config: NewsletterConfig
    status: str = (
        "initialized"  # initialized, collecting, analyzing, generating, completed, failed
    )
    collected_articles: Optional[List[Article]] = None
    analyzed_articles: Optional[List[AnalyzedArticle]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None
