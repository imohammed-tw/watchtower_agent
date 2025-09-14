# File: backend/app/utils/risk_assessment.py - NEW FILE

"""
Risk Assessment and Alert System for AI Watchtower
Implements executive-level risk scoring and action item generation per requirements
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
from models import AnalyzedArticle, NewsletterConfig
from dataclasses import dataclass
import re


class RiskLevel(str, Enum):
    """
    Risk level classification
    WHAT THIS IS: Executive-friendly risk categories for dashboard display
    """
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """
    Alert categorization for different business areas
    WHAT THIS IS: Groups alerts by business impact area for better management
    """
    COMPLIANCE_DEADLINE = "compliance_deadline"
    SECURITY_THREAT = "security_threat"
    REGULATORY_CHANGE = "regulatory_change"
    MARKET_DISRUPTION = "market_disruption"
    TECHNICAL_ISSUE = "technical_issue"


@dataclass
class RiskAlert:
    """
    Individual risk alert structure
    WHAT THIS IS: Single alert item with all necessary information for action
    """
    id: str
    title: str
    description: str
    risk_level: RiskLevel
    alert_type: AlertType
    deadline: Optional[datetime]      # For compliance deadlines
    action_required: str              # Specific action recommendation
    source_article_id: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class RiskAssessment:
    """
    Main risk assessment engine for newsletter content analysis
    
    WHAT THIS DOES:
    1. Analyzes articles for business risk indicators
    2. Generates impact scores (1-10 as required)
    3. Creates actionable alerts for leadership
    4. Provides executive summary data
    """
    
    # Risk keywords by category (from requirements document)
    RISK_KEYWORDS = {
        "compliance": [
            "regulation", "compliance", "deadline", "GDPR", "AI Act", "FTC", "SEC", 
            "audit", "fine", "penalty", "violation", "legal", "court", "lawsuit"
        ],
        "security": [
            "security", "breach", "vulnerability", "attack", "threat", "malware", 
            "exploit", "hack", "data leak", "cyber", "phishing", "ransomware"
        ],
        "market": [
            "disruption", "competition", "market share", "revenue loss", "acquisition",
            "competitor", "startup", "funding", "valuation", "IPO", "merger"
        ],
        "technical": [
            "outage", "failure", "bug", "performance", "scalability", "downtime",
            "error", "crash", "latency", "capacity", "infrastructure"
        ]
    }
    
    # Compliance deadline extraction patterns
    COMPLIANCE_PATTERNS = [
        r"deadline.*?(\d{1,2}[-/]\d{1,2}[-/]\d{4})",
        r"by.*?(\d{1,2}[-/]\d{1,2}[-/]\d{4})",
        r"before.*?(\d{1,2}[-/]\d{1,2}[-/]\d{4})",
        r"(\d{1,2}[-/]\d{1,2}[-/]\d{4}).*?compliance",
        r"effective.*?(\d{1,2}[-/]\d{1,2}[-/]\d{4})",
        r"(\d{1,2}[-/]\d{1,2}[-/]\d{4}).*?requirement"
    ]
    
    # High-impact terms that increase urgency
    HIGH_IMPACT_TERMS = [
        "immediate", "urgent", "critical", "emergency", "breaking", "alert",
        "mandatory", "required", "must", "shall", "penalty", "fine"
    ]
    
    def __init__(self):
        self.active_alerts: List[RiskAlert] = []
    
    def assess_articles_risk(self, articles: List[AnalyzedArticle]) -> Dict[str, Any]:
        """
        Main risk assessment method - analyzes all articles for enterprise risk
        
        WHAT THIS RETURNS:
        - Overall risk level for executive dashboard
        - Impact score (1-10) as required by specifications  
        - Category-specific risk scores
        - Generated alerts requiring action
        - Action items for leadership
        """
        
        print(f"⚠️ Starting risk assessment of {len(articles)} articles")
        
        # Initialize risk scoring
        risk_scores = {
            "compliance": 0,
            "security": 0, 
            "market": 0,
            "technical": 0
        }
        
        high_risk_articles = []
        alerts_generated = []
        total_urgency = 0
        total_impact = 0
        
        # Analyze each article
        for article in articles:
            article_risks = self._analyze_article_risk(article)
            
            # Accumulate risk scores
            for category, score in article_risks.items():
                risk_scores[category] += score
            
            # Track high-risk articles
            max_article_risk = max(article_risks.values()) if article_risks.values() else 0
            if max_article_risk >= 7:  # High risk threshold
                high_risk_articles.append(article)
                print(f"🚨 High-risk article detected: '{article.article.title[:50]}...' (risk: {max_article_risk})")
                
                # Generate alert
                alert = self._generate_alert_from_article(article, article_risks)
                if alert:
                    alerts_generated.append(alert)
                    self.active_alerts.append(alert)
            
            # Accumulate for impact calculation
            total_urgency += article.urgency_score
            total_impact += article.impact_score
        
        # Calculate overall metrics
        article_count = len(articles)
        avg_urgency = total_urgency / article_count if article_count > 0 else 0
        avg_impact = total_impact / article_count if article_count > 0 else 0
        
        # Calculate overall risk level
        max_risk_score = max(risk_scores.values()) if risk_scores.values() else 0
        overall_risk_level = self._calculate_risk_level(max_risk_score, len(high_risk_articles))
        
        # Calculate Week's Impact Score (1-10 as per requirements)
        impact_score = min(10, max(1, int(
            (avg_impact * 0.4) +           # Article impact scores
            (avg_urgency * 0.3) +          # Article urgency scores  
            (len(alerts_generated) * 0.3)  # Number of alerts generated
        )))
        
        # Generate action items
        action_items = self._generate_action_items(risk_scores, alerts_generated, high_risk_articles)
        
        # Investment implications
        investment_implications = self._assess_investment_implications(risk_scores, alerts_generated)
        
        assessment_result = {
            "overall_risk_level": overall_risk_level.value,
            "impact_score": impact_score,
            "weeks_impact_score": impact_score,  # Alias for requirements
            "category_scores": risk_scores,
            "high_risk_articles_count": len(high_risk_articles),
            "alerts_generated": len(alerts_generated),
            "active_alerts": alerts_generated,
            "action_items": action_items,
            "top_3_critical_updates": self._get_top_critical_updates(high_risk_articles),
            "investment_implications": investment_implications,
            "threat_assessment": self._generate_threat_assessment(risk_scores),
            "compliance_deadlines": self._extract_compliance_deadlines(articles)
        }
        
        print(f"📊 Risk Assessment Complete:")
        print(f"   Overall Risk: {overall_risk_level.value.upper()}")
        print(f"   Impact Score: {impact_score}/10")
        print(f"   Alerts: {len(alerts_generated)}")
        print(f"   Action Items: {len(action_items)}")
        
        return assessment_result
    
    def _analyze_article_risk(self, article: AnalyzedArticle) -> Dict[str, int]:
        """
        Analyze individual article for risk indicators across all categories
        
        WHAT THIS DOES:
        - Scans article content for risk-related keywords
        - Considers existing urgency/impact scores
        - Returns risk score per category (0-10)
        """
        content = f"{article.article.title} {article.article.summary}".lower()
        
        risks = {"compliance": 0, "security": 0, "market": 0, "technical": 0}
        
        # Keyword-based risk scoring
        for category, keywords in self.RISK_KEYWORDS.items():
            keyword_matches = sum(1 for keyword in keywords if keyword.lower() in content)
            
            # Base risk from keyword density
            base_risk = min(keyword_matches * 2, 6)  # Cap base at 6
            
            # Boost based on article's existing scores
            if article.urgency_score >= 8:
                base_risk += 2  # High urgency boosts risk
            if article.impact_score >= 8:
                base_risk += 1  # High impact adds risk
                
            # Check for high-impact terms
            high_impact_matches = sum(1 for term in self.HIGH_IMPACT_TERMS if term in content)
            if high_impact_matches > 0:
                base_risk += high_impact_matches
                
            risks[category] = min(base_risk, 10)  # Cap at 10
        
        return risks
    
    def _calculate_risk_level(self, max_score: int, high_risk_count: int) -> RiskLevel:
        """
        Convert numeric scores to executive-friendly risk levels
        
        WHAT THIS DOES:
        - Maps numeric risk scores to business risk categories
        - Considers both score intensity and article count
        - Provides clear executive communication
        """
        if max_score >= 8 or high_risk_count >= 3:
            return RiskLevel.CRITICAL
        elif max_score >= 6 or high_risk_count >= 2:
            return RiskLevel.HIGH
        elif max_score >= 4 or high_risk_count >= 1:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_alert_from_article(self, article: AnalyzedArticle, risks: Dict[str, int]) -> Optional[RiskAlert]:
        """
        Generate actionable alert from high-risk article
        
        WHAT THIS DOES:
        - Creates structured alert for executive action
        - Extracts deadlines from compliance content
        - Provides specific action recommendations
        """
        max_risk_category = max(risks, key=risks.get)
        max_risk_score = risks[max_risk_category]
        
        if max_risk_score < 7:  # Only generate alerts for high risk
            return None
        
        # Map risk categories to alert types
        alert_type_map = {
            "compliance": AlertType.COMPLIANCE_DEADLINE,
            "security": AlertType.SECURITY_THREAT,
            "market": AlertType.MARKET_DISRUPTION,
            "technical": AlertType.TECHNICAL_ISSUE
        }
        
        alert = RiskAlert(
            id=f"alert_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(article.article.url) % 10000}",
            title=f"HIGH RISK: {article.article.title[:60]}{'...' if len(article.article.title) > 60 else ''}",
            description=article.article.summary[:300] + ("..." if len(article.article.summary) > 300 else ""),
            risk_level=self._calculate_risk_level(max_risk_score, 1),
            alert_type=alert_type_map[max_risk_category],
            deadline=self._extract_deadline(article.article.summary),
            action_required=self._generate_action_item(max_risk_category, article),
            source_article_id=str(hash(article.article.url))
        )
        
        return alert
    
    def _extract_deadline(self, text: str) -> Optional[datetime]:
        """
        Extract compliance deadlines from article text
        
        WHAT THIS DOES:
        - Uses regex patterns to find dates in compliance content
        - Converts to datetime objects for calendar integration
        - Handles multiple date formats
        """
        for pattern in self.COMPLIANCE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for date_str in matches:
                    try:
                        # Try different date formats
                        for fmt in ["%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%d-%m-%Y"]:
                            try:
                                parsed_date = datetime.strptime(date_str, fmt)
                                # Only return future dates (deadlines)
                                if parsed_date > datetime.utcnow():
                                    return parsed_date
                            except ValueError:
                                continue
                    except Exception:
                        continue
        return None
    
    def _generate_action_item(self, risk_category: str, article: AnalyzedArticle) -> str:
        """
        Generate specific, actionable recommendations based on risk type
        
        WHAT THIS DOES:
        - Provides concrete next steps for each risk category
        - Tailored to executive decision-making needs
        - Includes timeframes and responsibilities
        """
        actions = {
            "compliance": f"IMMEDIATE: Review compliance requirements mentioned in this article. Assign legal counsel to assess impact on current AI systems within 48 hours. Set calendar reminders for any regulatory deadlines.",
            
            "security": f"URGENT: Conduct security assessment of AI systems for vulnerabilities mentioned. Implement recommended security measures immediately. Brief security team within 24 hours.", 
            
            "market": f"STRATEGIC: Analyze competitive impact and market positioning implications. Schedule strategy review meeting within 1 week. Consider strategic response to market changes mentioned.",
            
            "technical": f"OPERATIONAL: Review technical infrastructure for issues highlighted. Assign technical lead to investigate and report back within 72 hours. Plan necessary updates or patches."
        }
        
        base_action = actions.get(risk_category, "REVIEW: Assess impact on AI initiatives and determine appropriate response.")
        
        # Add article-specific context
        source_info = f" | Source: {article.article.source} | Urgency: {article.urgency_score}/10"
        
        return base_action + source_info
    
    def _generate_action_items(self, risk_scores: Dict[str, int], alerts: List[RiskAlert], high_risk_articles: List[AnalyzedArticle]) -> List[str]:
        """
        Generate overall action items for executive summary (as required)
        
        WHAT THIS RETURNS:
        - Top 5 priority actions for leadership
        - Time-bound and responsibility-specific
        - Based on highest risk categories
        """
        actions = []
        
        # Priority actions based on highest risk categories
        sorted_risks = sorted(risk_scores.items(), key=lambda x: x[1], reverse=True)
        
        for category, score in sorted_risks[:3]:  # Top 3 risk categories
            if score >= 5:  # Meaningful risk threshold
                if category == "compliance":
                    actions.append("📋 IMMEDIATE: Schedule compliance review meeting with legal team within 48 hours")
                elif category == "security": 
                    actions.append("🔒 URGENT: Initiate comprehensive security assessment of all AI systems")
                elif category == "market":
                    actions.append("📊 STRATEGIC: Conduct competitive analysis and market strategy review by end of week")
                elif category == "technical":
                    actions.append("⚙️ OPERATIONAL: Technical infrastructure review and patch management assessment")
        
        # Add deadline-driven actions from alerts
        urgent_deadlines = [a for a in alerts if a.deadline and a.deadline <= datetime.utcnow() + timedelta(days=30)]
        if urgent_deadlines:
            actions.append(f"⏰ CALENDAR: Address {len(urgent_deadlines)} upcoming compliance deadlines within 30 days")
        
        # Add high-priority actions based on article count
        if len(high_risk_articles) >= 3:
            actions.append("🚨 ESCALATE: Multiple high-risk items detected - consider emergency leadership briefing")
        
        return actions[:5]  # Max 5 action items for executive summary
    
    def _get_top_critical_updates(self, high_risk_articles: List[AnalyzedArticle]) -> List[Dict[str, str]]:
        """
        Generate "Top 3 Critical Updates" for Executive Summary (per requirements)
        
        WHAT THIS RETURNS:
        - Most urgent items requiring immediate attention
        - Formatted for executive briefing
        - Max 3 items for focus
        """
        if not high_risk_articles:
            return []
        
        # Sort by urgency and impact
        sorted_articles = sorted(
            high_risk_articles, 
            key=lambda x: (x.urgency_score * x.impact_score), 
            reverse=True
        )
        
        critical_updates = []
        for i, article in enumerate(sorted_articles[:3], 1):
            critical_updates.append({
                "rank": i,
                "title": article.article.title,
                "summary": article.article.summary[:150] + "..." if len(article.article.summary) > 150 else article.article.summary,
                "urgency": article.urgency_score,
                "impact": article.impact_score,
                "source": article.article.source,
                "url": str(article.article.url)
            })
        
        return critical_updates
    
    def _assess_investment_implications(self, risk_scores: Dict[str, int], alerts: List[RiskAlert]) -> List[str]:
        """
        Assess budget/resource implications (per requirements)
        
        WHAT THIS RETURNS:
        - Financial impact considerations
        - Resource allocation recommendations
        - Investment priority guidance
        """
        implications = []
        
        # Compliance costs
        compliance_alerts = [a for a in alerts if a.alert_type == AlertType.COMPLIANCE_DEADLINE]
        if compliance_alerts or risk_scores["compliance"] >= 6:
            implications.append("💰 BUDGET: Allocate compliance budget for regulatory requirements and potential legal counsel")
        
        # Security investments  
        if risk_scores["security"] >= 6:
            implications.append("🔒 SECURITY: Consider increased cybersecurity budget allocation for AI system protection")
        
        # Market positioning investments
        if risk_scores["market"] >= 6:
            implications.append("📊 STRATEGY: Evaluate R&D and competitive response investments based on market developments")
        
        # Technical infrastructure
        if risk_scores["technical"] >= 5:
            implications.append("⚙️ INFRASTRUCTURE: Plan technical infrastructure upgrades and maintenance budget")
        
        return implications[:3]  # Max 3 for executive focus
    
    def _generate_threat_assessment(self, risk_scores: Dict[str, int]) -> str:
        """Generate overall threat assessment for enterprise AI initiatives"""
        max_risk = max(risk_scores.values()) if risk_scores.values() else 0
        
        if max_risk >= 8:
            return "CRITICAL: Multiple high-impact threats detected requiring immediate executive attention"
        elif max_risk >= 6:
            return "HIGH: Significant risks to AI initiatives requiring strategic response within 1 week"
        elif max_risk >= 4:
            return "MODERATE: Some risks present, monitor closely and prepare contingency plans"
        else:
            return "LOW: No significant immediate threats to AI initiatives detected"
    
    def _extract_compliance_deadlines(self, articles: List[AnalyzedArticle]) -> List[Dict[str, Any]]:
        """Extract all compliance deadlines for calendar tracking"""
        deadlines = []
        
        for article in articles:
            deadline_date = self._extract_deadline(article.article.summary)
            if deadline_date:
                deadlines.append({
                    "date": deadline_date.isoformat(),
                    "title": article.article.title,
                    "description": article.article.summary[:100] + "...",
                    "source": article.article.source,
                    "days_remaining": (deadline_date - datetime.utcnow()).days
                })
        
        # Sort by date
        deadlines.sort(key=lambda x: x["date"])
        return deadlines


class AlertManager:
    """
    Manages alerts and notifications for frontend integration
    
    WHAT THIS DOES:
    1. Stores and retrieves alerts
    2. Provides dashboard metrics
    3. Manages alert lifecycle
    4. Supports frontend requirements
    """
    
    def __init__(self):
        self.alerts: List[RiskAlert] = []
    
    def add_alert(self, alert: RiskAlert):
        """Add new alert to management system"""
        self.alerts.append(alert)
        print(f"🔔 New alert added: {alert.risk_level.value.upper()} - {alert.title}")
    
    def get_active_alerts(self, days_ahead: int = 30) -> List[RiskAlert]:
        """
        Get alerts requiring attention within specified timeframe
        
        WHAT THIS RETURNS:
        - Alerts with upcoming deadlines
        - High/Critical risk alerts regardless of deadline
        - Sorted by priority and urgency
        """
        cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        active = []
        for alert in self.alerts:
            # Include if has deadline within timeframe
            if alert.deadline and alert.deadline <= cutoff_date:
                active.append(alert)
            # Include if high/critical risk regardless of deadline
            elif alert.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                active.append(alert)
        
        # Sort by risk level (critical first) then by deadline
        risk_priority = {RiskLevel.CRITICAL: 4, RiskLevel.HIGH: 3, RiskLevel.MEDIUM: 2, RiskLevel.LOW: 1}
        
        return sorted(active, key=lambda x: (
            risk_priority.get(x.risk_level, 0),
            x.deadline or datetime.max
        ), reverse=True)
    
    def get_metrics(self) -> Dict[str, int]:
        """
        Get dashboard metrics for frontend display
        
        WHAT THIS RETURNS:
        - Numbers for header metrics display
        - Breakdown by risk level and type
        - Action count for "Actions Required" metric
        """
        active_alerts = self.get_active_alerts()
        
        return {
            "total_alerts": len(active_alerts),
            "critical_alerts": len([a for a in active_alerts if a.risk_level == RiskLevel.CRITICAL]),
            "high_risk_items": len([a for a in active_alerts if a.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]),
            "compliance_deadlines": len([a for a in active_alerts if a.alert_type == AlertType.COMPLIANCE_DEADLINE]),
            "security_threats": len([a for a in active_alerts if a.alert_type == AlertType.SECURITY_THREAT]),
            "actions_required": len(active_alerts),  # All active alerts require action
            "market_disruptions": len([a for a in active_alerts if a.alert_type == AlertType.MARKET_DISRUPTION]),
            "regulatory_changes": len([a for a in active_alerts if a.alert_type == AlertType.REGULATORY_CHANGE])
        }
    
    def clear_old_alerts(self, days_old: int = 30):
        """Clean up old alerts to prevent memory bloat"""
        cutoff = datetime.utcnow() - timedelta(days=days_old)
        original_count = len(self.alerts)
        
        self.alerts = [a for a in self.alerts if a.created_at > cutoff]
        
        removed_count = original_count - len(self.alerts)
        if removed_count > 0:
            print(f"🧹 Cleaned up {removed_count} old alerts")
    
    def get_alerts_summary(self) -> Dict[str, Any]:
        """Get comprehensive alerts summary for API responses"""
        active_alerts = self.get_active_alerts()
        metrics = self.get_metrics()
        
        return {
            "summary": metrics,
            "active_alerts_count": len(active_alerts),
            "by_risk_level": {
                "critical": len([a for a in active_alerts if a.risk_level == RiskLevel.CRITICAL]),
                "high": len([a for a in active_alerts if a.risk_level == RiskLevel.HIGH]),
                "medium": len([a for a in active_alerts if a.risk_level == RiskLevel.MEDIUM]),
                "low": len([a for a in active_alerts if a.risk_level == RiskLevel.LOW])
            },
            "upcoming_deadlines": len([a for a in active_alerts if a.deadline and a.deadline <= datetime.utcnow() + timedelta(days=7)]),
            "requires_immediate_attention": len([a for a in active_alerts if a.risk_level == RiskLevel.CRITICAL])
        }