# File: backend/app/utils/content_quality_manager.py - NEW FILE

"""
Content Quality and Threshold Management
Ensures minimum article requirements and prevents empty sections
"""

from typing import List, Dict, Any, Optional, Tuple
from models import AnalyzedArticle, NewsletterConfig, NewsletterFormat
from collections import defaultdict


class ContentQualityManager:
    """
    Manages content quality and ensures minimum thresholds
    
    WHAT THIS DOES:
    1. Validates minimum article counts per newsletter format
    2. Prevents empty sections by redistributing content
    3. Enhances article-to-section assignment accuracy
    4. Provides quality recommendations for improvement
    """
    
    # MINIMUM ARTICLE REQUIREMENTS (based on your feedback)
    MINIMUM_ARTICLES = {
        NewsletterFormat.DAILY: 5,      # At least 5 articles for daily
        NewsletterFormat.WEEKLY: 10,    # At least 10 articles for weekly  
        NewsletterFormat.MONTHLY: 15,   # At least 15 articles for monthly
        NewsletterFormat.CUSTOM: 8      # At least 8 articles for custom
    }
    
    # Minimum articles per section to prevent empty sections
    MIN_ARTICLES_PER_SECTION = 1  # At least 1 article per section
    
    def __init__(self):
        self.quality_stats = {}
    
    def validate_content_threshold(
        self, 
        articles: List[AnalyzedArticle], 
        config: NewsletterConfig
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate that we have minimum required articles for newsletter generation
        
        WHAT THIS RETURNS:
        - Boolean: Whether content meets threshold
        - Dict: Detailed quality report with recommendations
        """
        
        total_articles = len(articles)
        min_required = self.MINIMUM_ARTICLES.get(config.format, 10)
        
        print(f"📊 Quality Check: Found {total_articles} articles, need {min_required}")
        
        # Analyze section distribution
        section_dist = self._analyze_section_distribution(articles, config.sections)
        section_issues = self._check_section_coverage(articles, config.sections)
        
        quality_report = {
            "total_articles": total_articles,
            "minimum_required": min_required,
            "meets_threshold": total_articles >= min_required,
            "shortage": max(0, min_required - total_articles),
            "section_distribution": section_dist,
            "section_issues": section_issues,
            "quality_issues": [],
            "recommendations": []
        }
        
        # Assess overall quality
        empty_sections_count = len(section_issues["empty_sections"])
        is_valid = (
            total_articles >= min_required and 
            empty_sections_count <= 1  # Allow max 1 empty section
        )
        
        print(f"📊 Quality Assessment:")
        print(f"   Articles: {total_articles}/{min_required} ({'✅' if total_articles >= min_required else '❌'})")
        print(f"   Empty sections: {empty_sections_count} ({'✅' if empty_sections_count <= 1 else '❌'})")
        print(f"   Overall: {'✅ PASS' if is_valid else '❌ FAIL'}")
        
        # Generate recommendations if needed
        if not is_valid:
            quality_report["recommendations"] = self._generate_quality_recommendations(quality_report)
        
        return is_valid, quality_report
    
    def _analyze_section_distribution(
        self, 
        articles: List[AnalyzedArticle], 
        sections: List[str]
    ) -> Dict[str, Any]:
        """Analyze how articles are distributed across sections"""
        
        section_counts = defaultdict(int)
        section_articles = defaultdict(list)
        unassigned_articles = []
        
        for article in articles:
            section = article.assigned_section
            if section in sections:
                section_counts[section] += 1
                section_articles[section].append(article)
            else:
                # Handle misassigned articles
                section_counts["unassigned"] += 1
                unassigned_articles.append(article)
                print(f"⚠️ Article assigned to unknown section '{section}': '{article.article.title[:50]}...'")
        
        return {
            "section_counts": dict(section_counts),
            "section_articles": dict(section_articles),
            "unassigned_articles": unassigned_articles,
            "average_per_section": len(articles) / len(sections) if sections else 0,
            "well_distributed": all(count >= self.MIN_ARTICLES_PER_SECTION for count in section_counts.values() if count > 0)
        }
    
    def _check_section_coverage(
        self, 
        articles: List[AnalyzedArticle], 
        sections: List[str]
    ) -> Dict[str, Any]:
        """Check which sections have insufficient content"""
        
        section_counts = defaultdict(int)
        for article in articles:
            if article.assigned_section in sections:
                section_counts[article.assigned_section] += 1
        
        empty_sections = []
        low_content_sections = []
        
        for section in sections:
            count = section_counts.get(section, 0)
            if count == 0:
                empty_sections.append(section)
                print(f"❌ Empty section detected: '{section}'")
            elif count < self.MIN_ARTICLES_PER_SECTION:
                low_content_sections.append((section, count))
                print(f"⚠️ Low content section: '{section}' ({count} articles)")
        
        return {
            "empty_sections": empty_sections,
            "low_content_sections": low_content_sections,
            "well_covered_sections": [s for s in sections if section_counts.get(s, 0) >= self.MIN_ARTICLES_PER_SECTION],
            "section_counts": dict(section_counts)
        }
    
    def redistribute_articles_to_sections(
        self, 
        articles: List[AnalyzedArticle], 
        sections: List[str]
    ) -> List[AnalyzedArticle]:
        """
        Redistribute articles to ensure no sections are completely empty
        
        WHAT THIS DOES:
        1. Identifies empty sections
        2. Finds sections with excess articles
        3. Redistributes articles to balance content
        4. Updates article assignments in-place
        """
        
        if not articles or not sections:
            return articles
            
        print(f"🔄 Redistributing {len(articles)} articles across {len(sections)} sections")
        
        # Get current distribution
        section_articles = defaultdict(list)
        for article in articles:
            target_section = article.assigned_section if article.assigned_section in sections else sections[0]
            section_articles[target_section].append(article)
            article.assigned_section = target_section  # Ensure valid section
        
        # Find empty sections
        empty_sections = [s for s in sections if len(section_articles[s]) == 0]
        
        if not empty_sections:
            print("✅ No empty sections found, no redistribution needed")
            return articles
        
        print(f"🎯 Found {len(empty_sections)} empty sections: {empty_sections}")
        
        # Redistribute from sections with multiple articles
        for empty_section in empty_sections:
            # Find section with most articles (and more than minimum)
            donor_candidates = [(s, len(articles)) for s, articles in section_articles.items() 
                              if len(articles) > self.MIN_ARTICLES_PER_SECTION]
            
            if not donor_candidates:
                # No suitable donors, assign any unassigned articles
                unassigned = [a for a in articles if a.assigned_section not in sections]
                if unassigned:
                    article_to_move = unassigned[0]
                    article_to_move.assigned_section = empty_section
                    section_articles[empty_section].append(article_to_move)
                    print(f"🔄 Assigned unassigned article to '{empty_section}'")
                continue
            
            # Find best donor (most articles)
            donor_section = max(donor_candidates, key=lambda x: x[1])[0]
            
            # Move one article to empty section
            if section_articles[donor_section]:
                article_to_move = section_articles[donor_section].pop()
                article_to_move.assigned_section = empty_section
                section_articles[empty_section].append(article_to_move)
                
                print(f"🔄 Moved article from '{donor_section}' to '{empty_section}': '{article_to_move.article.title[:30]}...'")
        
        # Final verification
        final_empty = [s for s in sections if len(section_articles[s]) == 0]
        if final_empty:
            print(f"⚠️ Still have empty sections after redistribution: {final_empty}")
        else:
            print("✅ All sections now have content")
        
        return articles
    
    def enhance_article_assignment(
        self, 
        articles: List[AnalyzedArticle], 
        sections: List[str]
    ) -> List[AnalyzedArticle]:
        """
        Enhance article-to-section assignment using better matching
        
        WHAT THIS DOES:
        1. Uses section-specific keywords for better matching
        2. Analyzes article content for relevance
        3. Reassigns articles to more appropriate sections
        4. Improves overall content distribution
        """
        
        if not articles or not sections:
            return articles
            
        print(f"🎯 Enhancing article assignments for {len(articles)} articles")
        
        # Get section keywords for better matching
        try:
            from utils.section_manager import SectionManager
            section_keywords = {}
            for section in sections:
                section_keywords[section] = SectionManager.get_section_keywords(section)
        except ImportError:
            print("⚠️ Section Manager not available, using basic assignment")
            return articles
        
        reassigned_count = 0
        
        # Reassign articles based on content relevance
        for article in articles:
            original_section = article.assigned_section
            best_section = self._find_best_section_match(
                article, sections, section_keywords
            )
            
            if best_section != original_section and best_section in sections:
                article.assigned_section = best_section
                reassigned_count += 1
                print(f"🎯 Reassigned '{article.article.title[:30]}...' from '{original_section}' to '{best_section}'")
        
        print(f"✅ Article assignment enhancement complete: {reassigned_count} articles reassigned")
        return articles
    
    def _find_best_section_match(
        self, 
        article: AnalyzedArticle, 
        sections: List[str],
        section_keywords: Dict[str, List[str]]
    ) -> str:
        """Find the best section match for an article based on content analysis"""
        
        content = f"{article.article.title} {article.article.summary}".lower()
        
        # Score each section based on keyword matches
        section_scores = {}
        for section in sections:
            keywords = section_keywords.get(section, [])
            if not keywords:
                section_scores[section] = 0
                continue
                
            # Count keyword matches (case-insensitive)
            score = sum(1 for keyword in keywords if keyword.lower() in content)
            
            # Boost score for exact title matches
            title_lower = article.article.title.lower()
            title_boost = sum(2 for keyword in keywords if keyword.lower() in title_lower)
            
            section_scores[section] = score + title_boost
        
        # Return section with highest score
        if section_scores and max(section_scores.values()) > 0:
            best_section = max(section_scores.keys(), key=lambda x: section_scores[x])
            return best_section
        else:
            # No good match found, keep current assignment or use first section
            return article.assigned_section if article.assigned_section in sections else sections[0]
    
    def should_generate_newsletter(
        self, 
        articles: List[AnalyzedArticle], 
        config: NewsletterConfig
    ) -> Tuple[bool, str]:
        """
        Main quality gate: Determine if newsletter should be generated
        
        WHAT THIS RETURNS:
        - Boolean: Whether to proceed with generation
        - String: Human-readable reason for decision
        """
        
        article_count = len(articles)
        min_required = self.MINIMUM_ARTICLES.get(config.format, 10)
        
        print(f"🚪 Quality Gate Check: {article_count} articles for {config.format.value} format")
        
        # Absolute minimums
        if article_count == 0:
            return False, "No articles found - check search criteria and date range"
        
        if article_count < 3:
            return False, f"Insufficient content: only {article_count} articles found (minimum 3 required for any newsletter)"
        
        # Format-specific thresholds
        if article_count < min_required:
            shortage = min_required - article_count
            if article_count >= min_required * 0.7:  # Allow 30% tolerance
                return True, f"Proceeding with {article_count} articles (slightly below target of {min_required})"
            else:
                return False, f"Content below threshold: {article_count} articles found, need {min_required} ({shortage} short)"
        
        # Check section distribution
        is_valid, quality_report = self.validate_content_threshold(articles, config)
        empty_sections = quality_report["section_issues"]["empty_sections"]
        
        if len(empty_sections) > 2:
            return False, f"Too many sections would be empty ({len(empty_sections)}/{len(config.sections)}) - improve search criteria"
        
        # All checks passed
        return True, f"Quality check passed with {article_count} articles across {len(config.sections)} sections"
    
    def _generate_quality_recommendations(self, quality_report: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations to improve content quality"""
        
        recommendations = []
        
        if quality_report["shortage"] > 0:
            recommendations.append(
                f"🔍 Expand search: Add {quality_report['shortage']} more articles by widening keywords or date range"
            )
        
        empty_sections = quality_report["section_issues"]["empty_sections"]
        if empty_sections:
            recommendations.append(
                f"📂 Fill empty sections: Find content for {', '.join(empty_sections[:2])}"
            )
        
        low_sections = quality_report["section_issues"]["low_content_sections"]
        if low_sections:
            section_names = [name for name, count in low_sections[:2]]
            recommendations.append(
                f"📈 Boost content: Add more articles to {', '.join(section_names)}"
            )
        
        if quality_report["total_articles"] < 5:
            recommendations.append(
                "🎯 Improve targeting: Consider broader keywords or longer date range"
            )
        
        unassigned_count = len(quality_report["section_distribution"].get("unassigned_articles", []))
        if unassigned_count > 0:
            recommendations.append(
                f"🔧 Fix assignments: {unassigned_count} articles assigned to unknown sections"
            )
        
        return recommendations
    
    def generate_quality_summary(self, quality_report: Dict[str, Any]) -> str:
        """Generate human-readable quality summary for logging"""
        
        summary_parts = []
        
        # Article count status
        total = quality_report['total_articles']
        required = quality_report['minimum_required']
        summary_parts.append(f"Found {total}/{required} articles")
        
        if quality_report["meets_threshold"]:
            summary_parts.append("✅ Meets minimum")
        else:
            summary_parts.append(f"❌ {quality_report['shortage']} short")
        
        # Section status
        section_dist = quality_report["section_distribution"]
        if section_dist["well_distributed"]:
            summary_parts.append("✅ Well distributed")
        else:
            empty_count = len(quality_report["section_issues"]["empty_sections"])
            if empty_count > 0:
                summary_parts.append(f"⚠️ {empty_count} empty sections")
        
        return " | ".join(summary_parts)
    
    def get_distribution_stats(self, articles: List[AnalyzedArticle], sections: List[str]) -> Dict[str, Any]:
        """Get detailed distribution statistics for debugging"""
        
        section_counts = defaultdict(int)
        for article in articles:
            section_counts[article.assigned_section] += 1
        
        return {
            "total_articles": len(articles),
            "target_sections": sections,
            "section_counts": dict(section_counts),
            "empty_sections": [s for s in sections if section_counts[s] == 0],
            "well_populated_sections": [s for s in sections if section_counts[s] >= 2],
            "average_per_section": len(articles) / len(sections) if sections else 0,
            "distribution_balance": max(section_counts.values()) - min(section_counts.values()) if section_counts else 0
        }