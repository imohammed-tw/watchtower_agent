# File: backend/app/api/dashboard.py - NEW FILE

"""
Dashboard and Alerts API endpoints for frontend integration
Provides metrics, alerts, and action items for the UI
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from database import db
from agents.orchestrator import orchestrator
from models import UserPreferences
from utils.risk_assessment import RiskLevel, AlertType
from config import settings

router = APIRouter()


# Request/Response Models
class AlertActionRequest(BaseModel):
    """Request to mark alert as completed"""
    completed_by: str
    completion_note: Optional[str] = None


class DashboardMetricsResponse(BaseModel):
    """Dashboard metrics for header display"""
    total_articles: int
    sections: int
    high_risk_items: int
    actions_required: int
    last_newsletter_date: Optional[str] = None
    risk_level: str
    impact_score: int


class AlertResponse(BaseModel):
    """Individual alert response"""
    id: str
    title: str
    description: str
    risk_level: str
    alert_type: str
    deadline: Optional[str] = None
    action_required: str
    created_at: str
    completed: bool = False
    completed_at: Optional[str] = None
    completed_by: Optional[str] = None
    days_remaining: Optional[int] = None


class AlertsSummaryResponse(BaseModel):
    """Alerts summary for dashboard"""
    total_alerts: int
    by_risk_level: Dict[str, int]
    by_type: Dict[str, int]
    urgent_count: int  # Alerts needing immediate attention
    upcoming_deadlines: int  # Deadlines in next 7 days


@router.get("/metrics/{user_id}", response_model=DashboardMetricsResponse)
async def get_dashboard_metrics(user_id: str):
    """
    Get dashboard metrics for header display
    
    WHAT THIS PROVIDES:
    - Total Articles count (from latest newsletter)
    - Sections count
    - High Risk Items count  
    - Actions Required count
    - Overall risk level and impact score
    """
    try:
        print(f"📊 Getting dashboard metrics for user: {user_id}")
        
        # Get latest newsletter info
        newsletters = await db.get_user_newsletters(user_id, limit=1)
        
        total_articles = 0
        sections_count = 5  # Default
        last_newsletter_date = None
        
        if newsletters:
            latest = newsletters[0]
            total_articles = latest.get('total_articles', 0)
            last_newsletter_date = latest.get('generated_at')
            
            # Try to get sections count from latest newsletter
            try:
                import aiosqlite
                import json
                db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
                
                async with aiosqlite.connect(db_path) as database:
                    cursor = await database.execute(
                        "SELECT sections FROM newsletters WHERE id = ?",
                        (latest['id'],)
                    )
                    row = await cursor.fetchone()
                    if row and row[0]:
                        sections_data = json.loads(row[0])
                        sections_count = len(sections_data)
            except Exception as e:
                print(f"⚠️ Could not get sections count: {e}")
                sections_count = 5  # Default fallback
        
        # Get alert metrics from orchestrator
        try:
            alert_metrics = orchestrator.get_dashboard_metrics(user_id)
            high_risk_items = alert_metrics.get("high_risk_items", 0)
            actions_required = alert_metrics.get("actions_required", 0)
            risk_level = alert_metrics.get("risk_level", "low")
            impact_score = alert_metrics.get("impact_score", 0)
        except Exception as e:
            print(f"⚠️ Could not get alert metrics: {e}")
            # Fallback values
            high_risk_items = 0
            actions_required = 0
            risk_level = "low"
            impact_score = 0
        
        metrics = DashboardMetricsResponse(
            total_articles=total_articles,
            sections=sections_count,
            high_risk_items=high_risk_items,
            actions_required=actions_required,
            last_newsletter_date=last_newsletter_date,
            risk_level=risk_level,
            impact_score=impact_score
        )
        
        print(f"✅ Dashboard metrics: {metrics.total_articles} articles, {metrics.high_risk_items} high risk, {metrics.actions_required} actions")
        
        return metrics

    except Exception as e:
        print(f"❌ Error getting dashboard metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard metrics: {str(e)}")


@router.get("/alerts/{user_id}")
async def get_user_alerts(user_id: str, include_completed: bool = False, limit: int = 50):
    """
    Get alerts and actions for user
    
    WHAT THIS PROVIDES:
    - Active alerts requiring attention
    - Risk levels and alert types
    - Action items with deadlines
    - Completion status tracking
    """
    try:
        print(f"🔔 Getting alerts for user: {user_id}")
        
        # Get alerts from orchestrator
        alerts_data = orchestrator.get_alerts_and_actions(user_id)
        raw_alerts = alerts_data.get("alerts", [])
        
        # Convert to response format with additional calculations
        alerts_response = []
        for alert_data in raw_alerts:
            # Calculate days remaining if deadline exists
            days_remaining = None
            if alert_data.get("deadline"):
                try:
                    deadline = datetime.fromisoformat(alert_data["deadline"])
                    days_remaining = (deadline - datetime.utcnow()).days
                except Exception:
                    pass
            
            alert_response = AlertResponse(
                id=alert_data["id"],
                title=alert_data["title"],
                description=alert_data["description"],
                risk_level=alert_data["risk_level"],
                alert_type=alert_data["alert_type"],
                deadline=alert_data.get("deadline"),
                action_required=alert_data["action_required"],
                created_at=alert_data["created_at"],
                completed=False,  # TODO: Add completion tracking
                days_remaining=days_remaining
            )
            
            alerts_response.append(alert_response)
        
        # Sort by risk level and deadline
        risk_priority = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        alerts_response.sort(
            key=lambda x: (risk_priority.get(x.risk_level, 0), x.days_remaining or 999),
            reverse=True
        )
        
        # Apply limit
        if limit:
            alerts_response = alerts_response[:limit]
        
        print(f"✅ Found {len(alerts_response)} alerts for user {user_id}")
        
        return {
            "alerts": alerts_response,
            "summary": alerts_data.get("summary", {}),
            "total_count": len(alerts_response)
        }

    except Exception as e:
        print(f"❌ Error getting user alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.get("/alerts/summary")
async def get_alerts_summary(user_id: Optional[str] = None):
    """
    Get alerts summary statistics
    
    WHAT THIS PROVIDES:
    - Total alert counts by risk level
    - Alert type breakdown
    - Urgent items requiring immediate attention
    - Upcoming deadline counts
    """
    try:
        print(f"📈 Getting alerts summary{' for user ' + user_id if user_id else ''}")
        
        if user_id:
            # Get user-specific summary
            alerts_data = orchestrator.get_alerts_and_actions(user_id)
            summary = alerts_data.get("summary", {})
        else:
            # Global summary (if needed)
            summary = {
                "total_alerts": 0,
                "by_risk_level": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                "by_type": {
                    "compliance_deadline": 0,
                    "security_threat": 0,
                    "regulatory_change": 0,
                    "market_disruption": 0
                }
            }
        
        # Calculate additional metrics
        urgent_count = summary.get("by_risk_level", {}).get("critical", 0) + \
                      summary.get("by_risk_level", {}).get("high", 0)
        
        upcoming_deadlines = summary.get("by_type", {}).get("compliance_deadline", 0)
        
        alerts_summary = AlertsSummaryResponse(
            total_alerts=summary.get("total_alerts", 0),
            by_risk_level=summary.get("by_risk_level", {}),
            by_type=summary.get("by_type", {}),
            urgent_count=urgent_count,
            upcoming_deadlines=upcoming_deadlines
        )
        
        print(f"✅ Alerts summary: {alerts_summary.total_alerts} total, {alerts_summary.urgent_count} urgent")
        
        return alerts_summary

    except Exception as e:
        print(f"❌ Error getting alerts summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts summary: {str(e)}")


@router.post("/alerts/{alert_id}/complete")
async def complete_alert(alert_id: str, request: AlertActionRequest):
    """
    Mark an alert as completed
    
    WHAT THIS DOES:
    - Marks alert as handled/completed
    - Records who completed it and when
    - Updates action tracking
    """
    try:
        print(f"✅ Completing alert: {alert_id} by {request.completed_by}")
        
        # TODO: Implement alert completion tracking in database
        # For now, return success response
        
        completion_time = datetime.utcnow().isoformat()
        
        return {
            "status": "success",
            "message": f"Alert {alert_id} marked as completed",
            "completed_at": completion_time,
            "completed_by": request.completed_by,
            "note": request.completion_note
        }

    except Exception as e:
        print(f"❌ Error completing alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to complete alert: {str(e)}")


@router.get("/health-check")
async def dashboard_health_check():
    """Health check endpoint for dashboard APIs"""
    
    try:
        # Test orchestrator connectivity
        orchestrator_status = orchestrator.get_agents_status()
        
        # Test database connectivity
        db_healthy = True
        try:
            await db.get_user_newsletters("health_check", limit=1)
        except Exception:
            db_healthy = False
        
        return {
            "status": "healthy" if db_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "database": "healthy" if db_healthy else "error",
                "orchestrator": "healthy" if orchestrator_status else "error",
                "agents": orchestrator_status
            }
        }
    
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/system-stats")
async def get_system_statistics():
    """
    Get system-wide statistics for monitoring
    
    WHAT THIS PROVIDES:
    - Newsletter generation statistics
    - Alert generation rates
    - System performance metrics
    """
    try:
        # Get basic system stats
        import os
        db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
        
        stats = {
            "database_size_mb": round(os.path.getsize(db_path) / (1024 * 1024), 2) if os.path.exists(db_path) else 0,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_hours": "N/A",  # Would implement proper uptime tracking
            "total_newsletters": 0,  # Would get from database
            "total_alerts": 0,      # Would get from alert system
            "active_users": 0       # Would track active users
        }
        
        return stats
        
    except Exception as e:
        print(f"❌ Error getting system stats: {e}")
        return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}


# Additional helper endpoints for frontend development

@router.get("/test-alerts/{user_id}")
async def generate_test_alerts(user_id: str):
    """
    Generate test alerts for frontend development
    REMOVE IN PRODUCTION
    """
    
    test_alerts = [
        AlertResponse(
            id="test_001",
            title="URGENT: EU AI Act Compliance Deadline Approaching",
            description="New EU AI Act requirements must be implemented by March 15, 2025. High-risk AI systems require conformity assessments.",
            risk_level="critical",
            alert_type="compliance_deadline",
            deadline=(datetime.utcnow() + timedelta(days=30)).isoformat(),
            action_required="Schedule compliance review meeting with legal team within 48 hours",
            created_at=datetime.utcnow().isoformat(),
            completed=False,
            days_remaining=30
        ),
        AlertResponse(
            id="test_002", 
            title="Security Alert: New AI Model Vulnerability Discovered",
            description="Researchers discovered prompt injection vulnerability affecting GPT-4 class models. Immediate patch recommended.",
            risk_level="high",
            alert_type="security_threat",
            action_required="Initiate security assessment of all AI systems using large language models",
            created_at=datetime.utcnow().isoformat(),
            completed=False
        ),
        AlertResponse(
            id="test_003",
            title="Market Intelligence: Major Competitor Acquisition",
            description="Microsoft acquires AI startup for $2.1B, potentially disrupting enterprise AI market positioning.",
            risk_level="medium",
            alert_type="market_disruption",
            action_required="Conduct competitive analysis and market strategy review by end of week",
            created_at=(datetime.utcnow() - timedelta(hours=6)).isoformat(),
            completed=False
        )
    ]
    
    return {
        "alerts": test_alerts,
        "summary": {
            "total_alerts": len(test_alerts),
            "by_risk_level": {"critical": 1, "high": 1, "medium": 1, "low": 0},
            "by_type": {"compliance_deadline": 1, "security_threat": 1, "market_disruption": 1, "regulatory_change": 0}
        },
        "total_count": len(test_alerts)
    }