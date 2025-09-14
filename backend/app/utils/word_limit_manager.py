# File: backend/app/utils/word_limit_manager.py

"""
Word Limit Manager - Controls newsletter length and content optimization
"""

from typing import List, Dict, Any
from models import NewsletterConfig, AnalyzedArticle
import re


class WordLimitManager:
    """Manages word limits across newsletter generation"""
    
    def __init__(self, config: NewsletterConfig):
        self.config = config
        
        # Calculate header/footer overhead (approximately 20% of total)
        self.overhead_percentage = 0.2
        self.content_budget = int(config.max_total_words * (1 - self.overhead_percentage))
        
        print(f"📊 WordLimitManager initialized:")
        print(f"   Total budget: {config.max_total_words} words")
        print(f"   Content budget: {self.content_budget} words (after {self.overhead_percentage*100}% overhead)")
        print(f"   Per section limit: {config.max_section_words} words")
        print(f"   Per article limit: {config.max_article_summary_words} words")
        
    def truncate_text(self, text: str, max_words: int, preserve_sentences: bool = True) -> str:
        """Truncate text to specified word limit while preserving readability"""
        if not text or max_words <= 0:
            return ""
            
        words = text.split()
        if len(words) <= max_words:
            return text
        
        if preserve_sentences:
            # Try to preserve complete sentences
            sentences = re.split(r'[.!?]+', text)
            truncated_text = ""
            word_count = 0
            
            for sentence in sentences:
                sentence_words = len(sentence.split())
                if word_count + sentence_words <= max_words:
                    truncated_text += sentence + ". "
                    word_count += sentence_words
                else:
                    break
            
            # If we got at least half the desired words, return the sentence-preserved version
            if word_count >= max_words * 0.5:
                return truncated_text.strip()
        
        # Fallback: simple word truncation
        truncated = ' '.join(words[:max_words])
        return f"{truncated}..."
    
    def calculate_section_word_budget(self, sections: List[str]) -> Dict[str, int]:
        """Calculate word budget per section with smart distribution"""
        if not sections:
            return {}
        
        # Base budget per section
        base_budget_per_section = self.content_budget // len(sections)
        
        # Ensure no section exceeds the configured limit
        budget_per_section = min(base_budget_per_section, self.config.max_section_words)
        
        section_budgets = {section: budget_per_section for section in sections}
        
        print(f"📊 Section word budgets:")
        for section, budget in section_budgets.items():
            print(f"   {section}: {budget} words")
        
        return section_budgets
    
    def optimize_article_distribution(self, articles_by_section: Dict[str, List[AnalyzedArticle]], 
                                    section_budgets: Dict[str, int]) -> Dict[str, List[AnalyzedArticle]]:
        """Optimize article distribution based on word budgets and relevance"""
        optimized = {}
        
        print(f"🔄 Optimizing article distribution with word budgets...")
        
        for section, articles in articles_by_section.items():
            if not articles:
                optimized[section] = []
                continue
                
            budget = section_budgets.get(section, self.config.max_section_words)
            
            # Calculate how many articles can fit in budget
            # Reserve some words for section headers and formatting (30% of budget)
            article_content_budget = int(budget * 0.7)
            words_per_article = self.config.max_article_summary_words
            
            max_articles_in_budget = max(1, article_content_budget // words_per_article)
            
            # Sort articles by relevance score (highest first)
            sorted_articles = sorted(articles, 
                                   key=lambda x: x.relevance_score, 
                                   reverse=True)
            
            # Select top articles that fit in budget
            selected_articles = sorted_articles[:max_articles_in_budget]
            
            optimized[section] = selected_articles
            
            print(f"   {section}: {len(articles)} -> {len(selected_articles)} articles "
                  f"(budget: {budget} words, max articles: {max_articles_in_budget})")
        
        return optimized
    
    def estimate_content_length(self, articles: List[AnalyzedArticle]) -> int:
        """Estimate total word count for a list of articles"""
        total_words = 0
        
        for article in articles:
            # Estimate based on summary length + title + formatting overhead
            summary_words = len(article.article.summary.split())
            title_words = len(article.article.title.split())
            
            # Add formatting overhead (bullets, links, etc.)
            formatting_overhead = 10
            
            article_total = min(summary_words, self.config.max_article_summary_words) + title_words + formatting_overhead
            total_words += article_total
        
        return total_words
    
    def validate_section_content(self, section_content: str, max_words: int) -> Dict[str, Any]:
        """Validate section content against word limits"""
        word_count = len(section_content.split())
        
        validation_result = {
            "word_count": word_count,
            "max_words": max_words,
            "within_limit": word_count <= max_words,
            "percentage_used": (word_count / max_words) * 100 if max_words > 0 else 0,
            "words_over": max(0, word_count - max_words)
        }
        
        if not validation_result["within_limit"]:
            print(f"⚠️ Section content exceeds limit: {word_count}/{max_words} words "
                  f"({validation_result['words_over']} words over)")
        
        return validation_result
    
    def create_content_summary(self, newsletter_sections: Dict[str, str]) -> Dict[str, Any]:
        """Create a summary of content word usage"""
        total_words = 0
        section_stats = {}
        
        for section_name, content in newsletter_sections.items():
            word_count = len(content.split())
            total_words += word_count
            
            section_stats[section_name] = {
                "word_count": word_count,
                "percentage_of_total": (word_count / total_words * 100) if total_words > 0 else 0
            }
        
        summary = {
            "total_words": total_words,
            "target_words": self.config.max_total_words,
            "within_limit": total_words <= self.config.max_total_words,
            "utilization_percentage": (total_words / self.config.max_total_words * 100) if self.config.max_total_words > 0 else 0,
            "words_remaining": max(0, self.config.max_total_words - total_words),
            "section_breakdown": section_stats
        }
        
        return summary
    
    def get_optimization_suggestions(self, current_stats: Dict[str, Any]) -> List[str]:
        """Get suggestions for optimizing content length"""
        suggestions = []
        
        if not current_stats["within_limit"]:
            over_by = current_stats["total_words"] - current_stats["target_words"]
            suggestions.append(f"Content is {over_by} words over limit. Consider reducing article summaries or removing less relevant articles.")
        
        if current_stats["utilization_percentage"] < 60:
            suggestions.append("Content is quite short. You could include more articles or expand summaries for better value.")
        
        # Check section balance
        section_stats = current_stats.get("section_breakdown", {})
        if section_stats:
            word_counts = [stats["word_count"] for stats in section_stats.values()]
            if word_counts:
                avg_words = sum(word_counts) / len(word_counts)
                
                for section, stats in section_stats.items():
                    if stats["word_count"] > avg_words * 1.5:
                        suggestions.append(f"Section '{section}' is much longer than others. Consider balancing content.")
                    elif stats["word_count"] < avg_words * 0.5:
                        suggestions.append(f"Section '{section}' is quite short. Consider adding more content.")
        
        return suggestions
    
    @staticmethod
    def count_words(text: str) -> int:
        """Accurately count words in text"""
        if not text:
            return 0
        
        # Remove markdown formatting and HTML tags for accurate count
        clean_text = re.sub(r'[#*`\[\]()]+', '', text)
        clean_text = re.sub(r'<[^>]+>', '', clean_text)
        
        return len(clean_text.split())