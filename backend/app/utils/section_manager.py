# File: backend/app/utils/section_manager.py - COMPLETE REPLACEMENT

"""
Section Manager - Requirements-Compliant Version
Implements exact sections from requirements document with proper content mapping
"""

from typing import List, Dict
from models import NewsletterFormat


class SectionManager:
    """
    Manages section configurations per exact requirements
    
    KEY CHANGES:
    1. Replaced all sections with exact names from requirements
    2. Added section-specific keywords for better content matching
    3. Added content priorities and focus areas per section
    4. Ensures minimum viable sections for each format
    """
    
    # EXACT SECTIONS FROM REQUIREMENTS DOCUMENT
    REQUIRED_SECTIONS = {
        NewsletterFormat.DAILY: [
            "Executive Summary",           # Critical decisions for leadership
            "Security & Risk Alerts",     # Immediate threats and vulnerabilities
        ],
        NewsletterFormat.WEEKLY: [
            "Executive Summary", 
            "Regulatory & Compliance Watch",  # Legal/regulatory with business impact
            "Security & Risk Alerts",
            "Technology Breakthroughs",       # Competitive advantages
            "Market Intelligence",            # Market movements affecting positioning
        ],
        NewsletterFormat.MONTHLY: [
            "Executive Summary",
            "Regulatory & Compliance Watch", 
            "Security & Risk Alerts",
            "Technology Breakthroughs",
            "Market Intelligence",
        ],
        NewsletterFormat.CUSTOM: [
            "Executive Summary",
            "Technology Breakthroughs", 
            "Market Intelligence"
        ]
    }
    
    # EXACT CONTENT DESCRIPTIONS FROM REQUIREMENTS
    SECTION_CONTENT_SPECS = {
        "Executive Summary": {
            "purpose": "Critical decision-making intelligence for leadership",
            "content_focus": [
                "Top 3 Critical Updates - Most urgent items requiring immediate attention",
                "Week's Impact Score - Overall significance rating (1-10)",
                "Action Items - Key decisions or preparations needed",
                "Risk Level - Current threat assessment for enterprise AI initiatives",
                "Investment Implications - Budget/resource considerations"
            ],
            "keywords": ["critical", "urgent", "decision", "leadership", "impact", "risk", "investment", "action"],
            "ai_agent_focus": "High-impact, executive-level content requiring immediate attention"
        },
        
        "Regulatory & Compliance Watch": {
            "purpose": "Legal/regulatory changes with immediate business impact and compliance requirements",
            "content_focus": [
                "New Regulations - Recently announced or enacted AI laws",
                "Compliance Deadlines - Upcoming regulatory milestones (next 90 days)",
                "Industry Standards Updates - Changes to AI safety/ethics standards", 
                "Geographic Focus - Region-specific developments affecting global operations",
                "Compliance Cost Estimates - Financial impact of new requirements"
            ],
            "keywords": ["regulation", "compliance", "GDPR", "AI Act", "FTC", "SEC", "deadline", "law", "policy"],
            "ai_agent_focus": "Government sites, legal publications, regulatory bodies",
            "alert_system": "Urgent compliance deadlines with calendar integration"
        },
        
        "Security & Risk Alerts": {
            "purpose": "AI security threats that evolve rapidly and can cause immediate operational damage",
            "content_focus": [
                "Emerging Threats - New AI-related security vulnerabilities",
                "Incident Reports - Notable AI security breaches in last 7 days",
                "Vulnerability Assessments - Specific risks to enterprise AI systems",
                "Mitigation Strategies - Actionable defense recommendations",
                "Threat Intelligence - Attack patterns and adversarial techniques"
            ],
            "keywords": ["AI security", "prompt injection", "model poisoning", "data breach", "vulnerability", "attack", "threat"],
            "ai_agent_focus": "Security vendors, OWASP, CVE databases",
            "integration_note": "Uses OWASP AI threat taxonomy from documents"
        },
        
        "Technology Breakthroughs": {
            "purpose": "New AI capabilities that can create competitive advantages or disrupt existing strategies",
            "content_focus": [
                "Model Releases - New AI models and their enterprise implications",
                "Performance Benchmarks - Comparative analysis with business relevance",
                "Enterprise-Ready Technologies - Tools ready for production deployment",
                "Cost-Benefit Analysis - ROI potential of new technologies",
                "Implementation Timeline - Realistic adoption schedules"
            ],
            "keywords": ["new model", "breakthrough", "benchmark", "release", "GPT", "Claude", "innovation", "AI model"],
            "ai_agent_focus": "ArXiv, company blogs, tech publications",
            "tracking": "Performance tracking of model capabilities over time"
        },
        
        "Market Intelligence": {
            "purpose": "Market movements affecting competitive positioning, investment decisions, and strategic planning",
            "content_focus": [
                "Investment Trends - AI funding rounds, acquisitions, valuations",
                "Competitive Landscape - Key player movements and market share changes",
                "Industry Adoption Metrics - Sector-specific AI implementation rates",
                "Economic Impact - Market size changes, revenue implications", 
                "Strategic Partnerships - Alliances affecting market dynamics"
            ],
            "keywords": ["funding", "acquisition", "partnership", "market share", "revenue", "investment", "valuation"],
            "ai_agent_focus": "Financial publications, company press releases, analyst reports",
            "analysis": "Trend analysis using 72-hour window tracking"
        }
    }
    
    @classmethod
    def get_required_sections(cls, format_type: NewsletterFormat) -> List[str]:
        """
        Get EXACT required sections per requirements document
        
        WHAT THIS DOES:
        - Returns the specific sections needed for each newsletter format
        - Ensures consistency with requirements document
        - Provides fallback for unknown formats
        """
        sections = cls.REQUIRED_SECTIONS.get(format_type, cls.REQUIRED_SECTIONS[NewsletterFormat.MONTHLY])
        print(f"📋 SectionManager: Required sections for {format_type.value}: {sections}")
        return sections.copy()
    
    @classmethod  
    def validate_sections(cls, user_sections: List[str], format_type: NewsletterFormat) -> List[str]:
        """
        Validate user-provided sections against requirements
        
        WHAT THIS DOES:
        - Checks if user sections match available options
        - Falls back to required sections if invalid
        - Ensures minimum viable newsletter structure
        """
        
        print(f"🔍 SectionManager: Validating sections: {user_sections} for format: {format_type.value}")
        
        if not user_sections:
            # No user sections provided, use required ones
            print(f"🔧 No sections provided, using required sections for {format_type.value}")
            return cls.get_required_sections(format_type)
        
        # Validate user sections against available specs
        valid_sections = []
        available_sections = list(cls.SECTION_CONTENT_SPECS.keys())
        
        for section in user_sections:
            if section in available_sections:
                valid_sections.append(section)
                print(f"✅ Valid section: {section}")
            else:
                print(f"⚠️ Invalid section '{section}' - not in requirements. Available: {available_sections}")
        
        # Ensure we have minimum viable sections
        if len(valid_sections) >= 2:
            print(f"✅ Using validated custom sections: {valid_sections}")
            return valid_sections
        else:
            print(f"🔧 Insufficient valid sections ({len(valid_sections)}), using required defaults")
            return cls.get_required_sections(format_type)
    
    @classmethod
    def get_section_keywords(cls, section_name: str) -> List[str]:
        """
        Get AI agent keywords for better content matching
        
        WHAT THIS DOES:
        - Provides specific keywords that help AI agents find relevant content
        - Improves article-to-section assignment accuracy
        - Based on exact requirements specifications
        """
        section_spec = cls.SECTION_CONTENT_SPECS.get(section_name, {})
        keywords = section_spec.get("keywords", [])
        
        if keywords:
            print(f"🎯 Keywords for '{section_name}': {keywords[:3]}... ({len(keywords)} total)")
        
        return keywords
    
    @classmethod
    def get_section_purpose(cls, section_name: str) -> str:
        """Get the business purpose of a section"""
        section_spec = cls.SECTION_CONTENT_SPECS.get(section_name, {})
        return section_spec.get("purpose", f"Content related to {section_name}")
    
    @classmethod
    def get_content_focus(cls, section_name: str) -> List[str]:
        """Get specific content focus areas for a section"""
        section_spec = cls.SECTION_CONTENT_SPECS.get(section_name, {})
        return section_spec.get("content_focus", [])
    
    @classmethod
    def get_ai_agent_guidance(cls, section_name: str) -> str:
        """Get AI agent guidance for content collection"""
        section_spec = cls.SECTION_CONTENT_SPECS.get(section_name, {})
        return section_spec.get("ai_agent_focus", "General AI-related content")
    
    @classmethod
    def ensure_minimum_sections(cls, sections: List[str]) -> List[str]:
        """
        Ensure we have minimum required sections for viable newsletter
        
        WHAT THIS DOES:
        - Guarantees at least 2-3 core sections
        - Adds essential sections if missing
        - Caps at maximum reasonable sections (5)
        """
        if len(sections) < 2:
            print(f"⚠️ Only {len(sections)} sections, adding core requirements")
            core_sections = ["Executive Summary", "Technology Breakthroughs", "Market Intelligence"]
            
            for core_section in core_sections:
                if core_section not in sections:
                    sections.append(core_section)
                    print(f"➕ Added core section: {core_section}")
                if len(sections) >= 3:  # Minimum viable
                    break
        
        # Cap at 5 sections maximum for readability
        if len(sections) > 5:
            sections = sections[:5]
            print(f"🔧 Capped sections at 5 for optimal readability")
        
        return sections
    
    @classmethod
    def get_section_specifications(cls) -> Dict[str, Dict]:
        """
        Get complete section specifications for reference
        
        WHAT THIS RETURNS:
        - Complete mapping of all available sections
        - Their purposes, content focus, and keywords
        - Used by other systems for content matching
        """
        return cls.SECTION_CONTENT_SPECS.copy()
    
    @classmethod
    def suggest_sections_for_preferences(cls, user_keywords: List[str], industry_focus: List[str]) -> List[str]:
        """
        Suggest optimal sections based on user preferences
        
        WHAT THIS DOES:
        - Analyzes user keywords and industry focus
        - Recommends sections most likely to have relevant content
        - Helps personalize newsletter structure
        """
        # Always include Executive Summary (required for leadership)
        suggested = ["Executive Summary"]
        
        # Analyze keywords for section relevance
        user_content = " ".join(user_keywords + industry_focus).lower()
        
        # Score sections based on keyword overlap
        section_scores = {}
        for section_name, spec in cls.SECTION_CONTENT_SPECS.items():
            if section_name == "Executive Summary":
                continue  # Already included
                
            keywords = spec.get("keywords", [])
            score = sum(1 for keyword in keywords if keyword.lower() in user_content)
            section_scores[section_name] = score
        
        # Add top-scoring sections
        sorted_sections = sorted(section_scores.items(), key=lambda x: x[1], reverse=True)
        
        for section_name, score in sorted_sections[:4]:  # Max 4 additional sections
            if score > 0:  # Only add if there's keyword relevance
                suggested.append(section_name)
                print(f"🎯 Suggested '{section_name}' (relevance score: {score})")
        
        # Ensure minimum viable sections
        if len(suggested) < 3:
            for default in ["Technology Breakthroughs", "Market Intelligence"]:
                if default not in suggested:
                    suggested.append(default)
                if len(suggested) >= 3:
                    break
        
        return suggested