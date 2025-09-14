# File: app/tools/openai_client.py - UPDATED with word limit support

"""
OpenAI client for content analysis and generation - Enhanced with word limits
"""

from openai import AsyncOpenAI
from typing import List, Dict, Any
import json

from config import settings
from models import Article, AnalyzedArticle, NewsletterConfig


class OpenAIClient:
    """Client for OpenAI API with better section assignment and word limit control"""

    def __init__(self):
        self.client = None

    async def initialize(self):
        """Initialize the OpenAI client"""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def analyze_article(
        self, article: Article, user_preferences, available_sections: List[str]
    ) -> Dict[str, Any]:
        """Analyze an article with BETTER section assignment logic"""
        try:
            # 🔧 FIX: Create a more detailed prompt that explains what each section should contain
            section_descriptions = {
                "Executive Highlights": "High-level business insights, market trends, investment news, executive decisions, company strategies",
                "Technical Breakthroughs": "New technologies, algorithms, research developments, technical innovations, engineering advances",
                "Compliance & Risk Watch": "Regulations, policies, legal updates, compliance requirements, risk management, governance",
                "Industry Applications": "Real-world use cases, industry implementations, sector-specific applications, practical deployments",
                "Forward Intelligence": "Future predictions, emerging trends, upcoming developments, strategic forecasts, roadmaps",
                "Weekly Highlights": "Important weekly updates, key developments, notable announcements across all areas",
                "Today's Highlights": "Daily important updates, breaking news, immediate developments",
                "Urgent Updates": "Time-sensitive information, critical alerts, immediate action items",
                "Tech Developments": "General technology progress, development updates, technical news",
                "Industry News": "General industry updates, company news, sector developments",
                "Compliance Updates": "Latest regulatory changes, compliance news, policy updates",
                "Market Analysis": "Financial analysis, market trends, investment insights",
                "AI Technology News": "AI-specific technical developments, new AI tools, AI research",
                "Market & Investment Updates": "Financial news, funding, market analysis, investment trends",
                "Regulatory & Compliance": "Laws, regulations, compliance requirements, policy updates",
                "Future Trends": "Predictions, forecasts, emerging technologies, future outlook"
            }

            # Create detailed section explanations
            sections_info = []
            for section in available_sections:
                description = section_descriptions.get(section, f"General content related to {section}")
                sections_info.append(f"- {section}: {description}")

            prompt = f"""
            You are an expert content analyst. Analyze this article and assign it to the MOST APPROPRIATE section.

            Article to analyze:
            Title: {article.title}
            Summary: {article.summary}
            Source: {article.source}

            Available sections and their purposes:
            {chr(10).join(sections_info)}

            IMPORTANT INSTRUCTIONS:
            1. Read the article carefully and understand its main focus
            2. Consider the article's primary topic, not just keywords
            3. Choose the section that BEST matches the article's core content
            4. Don't default to "Compliance & Risk Watch" unless it's truly about regulations/compliance
            5. Technical content should go to "Technical Breakthroughs"
            6. Business/market content should go to "Executive Highlights"
            7. Real-world usage should go to "Industry Applications"
            8. Future-looking content should go to "Forward Intelligence"

            Return ONLY a JSON object with this exact format:
            {{
                "relevance_score": 0.8,
                "sentiment": "positive",
                "impact_score": 7,
                "urgency_score": 6,
                "best_section": "Technical Breakthroughs",
                "reasoning": "This article focuses on new AI algorithm developments, making it a technical breakthrough rather than regulatory content",
                "section_confidence": 0.9
            }}

            - relevance_score: 0.0-1.0 (how relevant to AI/technology)
            - sentiment: "positive", "negative", or "neutral"
            - impact_score: 1-10 (potential business/industry impact)
            - urgency_score: 1-10 (how urgent/time-sensitive)
            - best_section: choose the MOST APPROPRIATE section (think carefully!)
            - reasoning: explain WHY you chose this section
            - section_confidence: 0.0-1.0 (how confident you are in the section choice)
            """

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content analyst. Analyze articles carefully and assign them to appropriate sections based on their PRIMARY content focus. Don't default to compliance unless it's truly about regulations."
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,  # Low temperature for consistent analysis
            )

            content = response.choices[0].message.content
            analysis = json.loads(content)
            
            # 🔧 DEBUG: Print analysis reasoning
            print(f"🔍 OpenAI Analysis for '{article.title[:50]}...':")
            print(f"   Assigned to: {analysis.get('best_section', 'Unknown')}")
            print(f"   Confidence: {analysis.get('section_confidence', 0):.2f}")
            print(f"   Reasoning: {analysis.get('reasoning', 'No reasoning provided')}")
            
            return analysis

        except Exception as e:
            print(f"❌ Error analyzing article: {e}")
            # 🔧 FIX: Better fallback logic - distribute articles across sections
            fallback_sections = [
                "Executive Highlights",
                "Technical Breakthroughs", 
                "Industry Applications",
                "Forward Intelligence"
            ]
            
            # Use hash of title to deterministically assign to different sections
            title_hash = hash(article.title) % len(fallback_sections)
            fallback_section = fallback_sections[title_hash]
            
            print(f"🔧 Fallback: Assigning '{article.title[:30]}...' to '{fallback_section}'")
            
            return {
                "relevance_score": 0.7,
                "sentiment": "neutral",
                "impact_score": 5,
                "urgency_score": 5,
                "best_section": fallback_section,
                "reasoning": "Analysis failed, using fallback assignment",
                "section_confidence": 0.5
            }

    async def generate_section_content(
        self,
        section_name: str,
        articles: List[AnalyzedArticle],
        config: NewsletterConfig,
    ) -> str:
        """Generate content for a newsletter section (backward compatibility)"""
        # Use the default section word limit
        return await self.generate_section_content_with_limits(
            section_name, articles, config, config.max_section_words
        )

    async def generate_section_content_with_limits(
        self,
        section_name: str,
        articles: List[AnalyzedArticle],
        config: NewsletterConfig,
        word_limit: int,
    ) -> str:
        """Generate content for a newsletter section with strict word limits"""
        try:
            print(f"🤖 OpenAI: Generating '{section_name}' with {len(articles)} articles, {word_limit} word limit")

            # Prepare articles data with word limit considerations
            articles_text = self._format_articles_for_prompt(articles, config.max_article_summary_words)

            # Calculate recommended items based on word budget
            words_per_item = word_limit // max(1, min(len(articles), 4))  # Assume 2-4 items per section
            
            prompt = f"""
            Generate content for the "{section_name}" section of an AI newsletter.
            
            Articles to include:
            {articles_text}
            
            STRICT REQUIREMENTS:
            - MAXIMUM {word_limit} words total for this entire section
            - Format: {config.template.value}
            - Include links: {config.include_links}
            - Each article summary should be ~{config.max_article_summary_words} words maximum
            - Aim for {min(len(articles), 3)} key highlights maximum
            
            Structure:
            1. Brief section introduction (20-30 words)
            2. 2-3 key highlights with:
               - Clear headline for each highlight
               - Concise summary (~{words_per_item} words each)
               - Include clickable links: [Article Title](URL)
            3. Professional, newsletter-appropriate tone
            
            CRITICAL: Stay within the {word_limit} word limit. Count your words carefully.
            Return only the formatted section content (no meta-commentary).
            """

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": f"You are a professional newsletter writer. ALWAYS stay within the specified word limit of {word_limit} words. Be concise and impactful. Count words carefully before responding."
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=min(1500, word_limit * 2),  # Prevent overly long responses
            )

            generated_content = response.choices[0].message.content
            
            # Validate word count
            actual_words = len(generated_content.split())
            
            if actual_words > word_limit:
                print(f"⚠️ OpenAI generated {actual_words} words, limit was {word_limit}. Content will be truncated.")
                # Don't truncate here - let the newsletter agent handle it with better logic
            else:
                print(f"✅ OpenAI generated {actual_words}/{word_limit} words for '{section_name}'")

            return generated_content

        except Exception as e:
            print(f"❌ Error generating section content for '{section_name}': {e}")
            return self._create_fallback_section_content(section_name, articles, word_limit)

    def _format_articles_for_prompt(self, articles: List[AnalyzedArticle], max_summary_words: int) -> str:
        """Format articles for the prompt with word limits"""
        formatted_articles = []
        
        for i, article in enumerate(articles[:5], 1):  # Limit to top 5 articles
            # Truncate summary if too long
            summary = article.article.summary
            if len(summary.split()) > max_summary_words:
                summary_words = summary.split()[:max_summary_words]
                summary = ' '.join(summary_words) + "..."
            
            formatted_article = f"""
Article {i}:
Title: {article.article.title}
Source: {article.article.source}
URL: {article.article.url}
Summary: {summary}
Relevance: {article.relevance_score:.2f}/1.0
Impact: {article.impact_score}/10
Sentiment: {article.sentiment}
"""
            formatted_articles.append(formatted_article)
        
        return "\n".join(formatted_articles)

    def _create_fallback_section_content(self, section_name: str, articles: List[AnalyzedArticle], word_limit: int) -> str:
        """Create fallback content when OpenAI generation fails"""
        print(f"🔧 Creating fallback content for '{section_name}' with {word_limit} word limit")
        
        content = f"**{section_name}**\n\n"
        content += "Recent developments in this area include:\n\n"
        
        words_used = len(content.split())
        remaining_words = word_limit - words_used
        
        # Add articles within word limit
        for i, article in enumerate(articles[:3], 1):
            if remaining_words < 30:  # Need at least 30 words for a meaningful entry
                break
                
            # Calculate words for this entry
            title_words = len(article.article.title.split())
            available_for_summary = min(50, remaining_words - title_words - 10)  # Reserve 10 for formatting
            
            if available_for_summary > 10:
                summary_words = article.article.summary.split()[:available_for_summary]
                summary = ' '.join(summary_words)
                if len(article.article.summary.split()) > available_for_summary:
                    summary += "..."
                
                entry = f"• **{article.article.title}** - {summary} [Read more]({article.article.url})\n\n"
                content += entry
                remaining_words -= len(entry.split())
            else:
                # Just add title if no room for summary
                entry = f"• **{article.article.title}** [Read more]({article.article.url})\n\n"
                content += entry
                remaining_words -= len(entry.split())
        
        return content

    async def optimize_content_for_word_limit(self, content: str, word_limit: int) -> str:
        """Use OpenAI to intelligently optimize content to fit word limit"""
        current_words = len(content.split())
        
        if current_words <= word_limit:
            return content
        
        try:
            prompt = f"""
            Please rewrite this newsletter section content to fit within {word_limit} words while preserving all key information and links.

            Current content ({current_words} words):
            {content}

            Requirements:
            - Maximum {word_limit} words
            - Preserve all important information
            - Keep all URLs and links
            - Maintain professional newsletter tone
            - Focus on the most impactful points
            
            Return only the optimized content.
            """

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an expert editor. Optimize content to exactly {word_limit} words while preserving key information and all links."
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )

            optimized_content = response.choices[0].message.content
            optimized_words = len(optimized_content.split())
            
            print(f"🤖 OpenAI optimized content: {current_words} -> {optimized_words} words")
            
            return optimized_content

        except Exception as e:
            print(f"❌ Error optimizing content: {e}")
            # Fallback to simple truncation
            words = content.split()
            return ' '.join(words[:word_limit]) + "..."