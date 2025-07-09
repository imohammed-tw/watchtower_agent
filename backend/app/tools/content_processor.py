# File: app/tools/content_processor.py
"""
Content processing utilities
"""
from typing import List, Set
from urllib.parse import urlparse

from models import Article, UserPreferences


class ContentProcessor:
    """Content processing and validation utilities"""

    def __init__(self):
        self.seen_urls: Set[str] = set()
        self.seen_titles: Set[str] = set()

    async def initialize(self):
        """Initialize the processor"""
        pass

    async def remove_duplicates(self, articles: List[Article]) -> List[Article]:
        """Remove duplicate articles based on URL and title similarity"""
        unique_articles = []

        for article in articles:
            url_key = self._normalize_url(str(article.url))
            title_key = self._normalize_title(article.title)

            if url_key not in self.seen_urls and title_key not in self.seen_titles:
                unique_articles.append(article)
                self.seen_urls.add(url_key)
                self.seen_titles.add(title_key)

        return unique_articles

    async def validate_articles(
        self, articles: List[Article], preferences: UserPreferences
    ) -> List[Article]:
        """Validate articles based on user preferences and quality"""
        validated_articles = []

        for article in articles:
            # Skip excluded sources
            if article.source in preferences.excluded_sources:
                continue

            # Basic quality checks
            if not article.title or len(article.title) < 10:
                continue

            if not article.summary or len(article.summary) < 20:
                continue

            # Calculate basic quality score
            article.quality_score = self._calculate_quality_score(article)

            if article.quality_score >= 0.5:  # Minimum quality threshold
                validated_articles.append(article)

        return validated_articles

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for duplicate detection"""
        try:
            parsed = urlparse(url)
            # Remove query parameters and fragments
            normalized = f"{parsed.netloc}{parsed.path}".lower()
            return normalized
        except:
            return url.lower()

    def _normalize_title(self, title: str) -> str:
        """Normalize title for duplicate detection"""
        # Remove common punctuation and convert to lowercase
        import re

        normalized = re.sub(r"[^\w\s]", "", title.lower())
        # Remove extra whitespace
        normalized = " ".join(normalized.split())
        return normalized

    def _calculate_quality_score(self, article: Article) -> float:
        """Calculate basic quality score for an article"""
        score = 0.0

        # Title quality
        if len(article.title) > 20:
            score += 0.3

        # Summary quality
        if len(article.summary) > 50:
            score += 0.3

        # Source reliability (basic check)
        reliable_domains = [
            "techcrunch.com",
            "wired.com",
            "mit.edu",
            "arxiv.org",
            "openai.com",
            "anthropic.com",
            "ftc.gov",
            "europa.eu",
        ]

        if any(domain in article.source.lower() for domain in reliable_domains):
            score += 0.4
        else:
            score += 0.2  # Basic score for other sources

        return min(score, 1.0)
