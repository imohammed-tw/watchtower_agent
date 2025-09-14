# File: backend/app/models.py - UPDATED with word limit fields

"""
Data models for AI Watchtower - Enhanced with word limit controls
"""
from pydantic import BaseModel, Field, HttpUrl, validator
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
    """Enhanced configuration for newsletter generation with word limits"""
    format: NewsletterFormat = NewsletterFormat.MONTHLY
    date_range: Dict[str, str] = Field(default_factory=dict)
    sections: List[str] = Field(default_factory=list)
    max_articles: int = Field(default=20, ge=5, le=100)
    template: TemplateType = TemplateType.PROFESSIONAL
    include_links: bool = True
    include_summary: bool = True
    
    # NEW: Word limit controls
    max_total_words: int = Field(default=2000, ge=500, le=10000)
    max_section_words: int = Field(default=400, ge=100, le=2000)
    max_article_summary_words: int = Field(default=80, ge=20, le=200)

    @validator('sections', pre=True, always=True)
    def validate_sections(cls, v):
        """Validate sections are not empty or invalid - PRESERVE user sections"""
        print(f"🔍 SECTIONS VALIDATOR: input = {v}, type = {type(v)}")
        
        # 🔧 FIX: Don't automatically replace user sections with defaults
        # Only fix obviously broken cases
        
        # If sections is ['string'] or contains 'string', fix it
        if v == ['string'] or (isinstance(v, list) and 'string' in v):
            print(f"🔧 SECTIONS VALIDATOR: Converting ['string'] to default sections")
            return [
                "Executive Summary",
                "Technology Breakthroughs",
                "Regulatory & Compliance Watch",
                "Market Intelligence",
                "Security & Risk Alerts",
            ]
        
        # If sections is completely empty or None, return defaults
        if not v or (isinstance(v, list) and len(v) == 0):
            print(f"🔧 SECTIONS VALIDATOR: Empty sections, using defaults")
            return [
                "Executive Summary",
                "Technology Breakthroughs",
                "Regulatory & Compliance Watch",
                "Market Intelligence",
                "Security & Risk Alerts",
            ]
        
        # 🔧 CRITICAL FIX: If sections is valid user input, PRESERVE IT
        if isinstance(v, list) and len(v) > 0:
            # Clean up section names but preserve user choice
            cleaned_sections = []
            for section in v:
                if isinstance(section, str) and section.strip() and section != 'string':
                    cleaned_sections.append(section.strip())
                    
            if len(cleaned_sections) > 0:
                print(f"✅ SECTIONS VALIDATOR: Preserving user sections: {cleaned_sections}")
                return cleaned_sections
                
        # If we get here, something's wrong, return defaults
        print(f"⚠️ SECTIONS VALIDATOR: Invalid sections format, using defaults")
        return [
            "Executive Summary",
            "Technology Breakthroughs",
            "Regulatory & Compliance Watch", 
            "Market Intelligence",
            "Security & Risk Alerts",
        ]

    @validator('max_section_words', always=True)
    def validate_section_words(cls, v, values):
        """Ensure section words don't exceed reasonable limits relative to total"""
        total_words = values.get('max_total_words', 2000)
        sections = values.get('sections', [])
        
        if sections:
            # Ensure sections can fit within total budget (with 20% overhead)
            available_for_content = int(total_words * 0.8)
            max_per_section = available_for_content // len(sections)
            
            if v > max_per_section:
                adjusted = max_per_section
                print(f"🔧 Adjusting max_section_words from {v} to {adjusted} based on total budget")
                return adjusted
        
        return v

    @validator('max_article_summary_words', always=True)
    def validate_article_words(cls, v, values):
        """Ensure article summary words are reasonable relative to section words"""
        section_words = values.get('max_section_words', 400)
        
        # Article summaries should be at most 1/3 of section budget to allow multiple articles
        max_reasonable = section_words // 3
        
        if v > max_reasonable:
            adjusted = max_reasonable
            print(f"🔧 Adjusting max_article_summary_words from {v} to {adjusted} based on section budget")
            return adjusted
        
        return v

    def get_word_budget_summary(self) -> Dict[str, Any]:
        """Get a summary of word budget allocation"""
        overhead = int(self.max_total_words * 0.2)  # Headers, footers, formatting
        content_budget = self.max_total_words - overhead
        sections_count = len(self.sections) if self.sections else 5
        
        return {
            "total_budget": self.max_total_words,
            "overhead_words": overhead,
            "content_budget": content_budget,
            "sections_count": sections_count,
            "words_per_section": content_budget // sections_count,
            "max_section_limit": self.max_section_words,
            "article_summary_limit": self.max_article_summary_words
        }


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
    """Newsletter model with enhanced statistics"""
    user_id: str
    title: str
    content: str
    config: NewsletterConfig
    total_articles: int
    sections: Dict[str, str]  # section_name -> content
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def summary_stats(self) -> Dict[str, Any]:
        """Get enhanced newsletter summary statistics"""
        word_count = len(self.content.split())
        
        # Calculate section word counts
        section_word_counts = {}
        for section_name, section_content in self.sections.items():
            section_word_counts[section_name] = len(section_content.split())
        
        return {
            "format": self.config.format,
            "total_articles": self.total_articles,
            "sections_count": len(self.sections),
            "generation_time": self.generated_at.isoformat(),
            "word_count": word_count,
            "target_word_count": self.config.max_total_words,
            "word_utilization": f"{(word_count / self.config.max_total_words * 100):.1f}%" if self.config.max_total_words > 0 else "N/A",
            "within_word_limit": word_count <= self.config.max_total_words,
            "section_word_counts": section_word_counts,
            "avg_words_per_section": sum(section_word_counts.values()) // len(section_word_counts) if section_word_counts else 0
        }

    def get_detailed_word_analysis(self) -> Dict[str, Any]:
        """Get detailed word count analysis"""
        total_words = len(self.content.split())
        budget = self.config.get_word_budget_summary()
        
        section_analysis = {}
        for section_name, content in self.sections.items():
            section_words = len(content.split())
            section_analysis[section_name] = {
                "word_count": section_words,
                "target_limit": self.config.max_section_words,
                "within_limit": section_words <= self.config.max_section_words,
                "utilization": f"{(section_words / self.config.max_section_words * 100):.1f}%" if self.config.max_section_words > 0 else "N/A"
            }
        
        return {
            "total_analysis": {
                "actual_words": total_words,
                "target_words": self.config.max_total_words,
                "within_limit": total_words <= self.config.max_total_words,
                "utilization": f"{(total_words / self.config.max_total_words * 100):.1f}%" if self.config.max_total_words > 0 else "N/A",
                "words_remaining": max(0, self.config.max_total_words - total_words)
            },
            "section_analysis": section_analysis,
            "budget_breakdown": budget
        }


class WorkflowState(BaseModel):
    """Workflow state for agent coordination"""
    workflow_id: str
    user_id: str
    user_preferences: UserPreferences
    newsletter_config: NewsletterConfig
    status: str = "initialized"  # initialized, collecting, analyzing, generating, completed, failed
    collected_articles: Optional[List[Article]] = None
    analyzed_articles: Optional[List[AnalyzedArticle]] = None
    risk_analysis: Optional[Dict[str, Any]] = None
    alert_metrics: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None