# File: backend/app/utils/newsletter_exporter.py - IMPROVED VERSION

"""
Newsletter export utilities with enhanced formatting and word count display
"""

import os
from datetime import datetime
from typing import Dict, Any
import re

from models import Newsletter


class NewsletterExporter:
    """Export newsletters to various formats with improved formatting"""

    def __init__(self, export_dir: str = "exports"):
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)

    def export_to_markdown(self, newsletter: Newsletter) -> str:
        """Export newsletter to markdown file with word count info"""
        # Clean filename
        safe_title = re.sub(r"[^\w\s-]", "", newsletter.title).strip()
        safe_title = re.sub(r"[-\s]+", "-", safe_title)

        filename = f"{safe_title}-{newsletter.generated_at.strftime('%Y-%m-%d')}.md"
        filepath = os.path.join(self.export_dir, filename)

        # Add word count information to markdown
        word_analysis = newsletter.get_detailed_word_analysis()
        enhanced_content = self._add_word_count_to_markdown(newsletter.content, word_analysis)

        # Write to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(enhanced_content)

        print(f"✅ Newsletter exported to: {filepath}")
        return filepath

    def export_to_html(self, newsletter: Newsletter) -> str:
        """Export newsletter to HTML file with proper formatting and word counts"""
        
        # Get word analysis
        word_analysis = newsletter.get_detailed_word_analysis()
        
        # Clean and convert newsletter content to HTML
        clean_content = self._clean_and_convert_content(newsletter)
        
        # Generate filename
        safe_title = re.sub(r"[^\w\s-]", "", newsletter.title).strip()
        safe_title = re.sub(r"[-\s]+", "-", safe_title)
        filename = f"{safe_title}-{newsletter.generated_at.strftime('%Y-%m-%d')}.html"
        filepath = os.path.join(self.export_dir, filename)

        # Create comprehensive HTML template
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{newsletter.title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
        }}
        
        .container {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 2.2em;
            font-weight: 700;
        }}
        
        .header .subtitle {{
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #e8f5e8;
            border-bottom: 1px solid #ddd;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
            display: block;
        }}
        
        .stat-label {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        
        .word-analysis {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 30px;
        }}
        
        .word-analysis h3 {{
            margin-top: 0;
            color: #856404;
        }}
        
        .progress-bar {{
            background: #e9ecef;
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
            margin: 10px 0;
        }}
        
        .progress-fill {{
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
        }}
        
        .progress-success {{ background: #28a745; }}
        .progress-warning {{ background: #ffc107; }}
        .progress-danger {{ background: #dc3545; }}
        
        .content {{
            padding: 30px;
        }}
        
        .section {{
            margin-bottom: 40px;
            border-left: 4px solid #3498db;
            padding-left: 20px;
        }}
        
        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .section h2 {{
            color: #2c3e50;
            margin: 0;
            font-size: 1.5em;
        }}
        
        .word-count {{
            background: #e9ecef;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            color: #6c757d;
        }}
        
        .section-content {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-top: 15px;
        }}
        
        a {{
            color: #3498db;
            text-decoration: none;
            font-weight: 500;
        }}
        
        a:hover {{
            text-decoration: underline;
            color: #2980b9;
        }}
        
        .highlight {{
            background: #fff3cd;
            padding: 2px 6px;
            border-radius: 4px;
        }}
        
        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr 1fr;
            }}
            .container {{
                margin: 10px;
            }}
            body {{
                padding: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{newsletter.title}</h1>
            <div class="subtitle">Generated: {newsletter.generated_at.strftime('%B %d, %Y at %I:%M %p UTC')}</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-number">{newsletter.total_articles}</span>
                <div class="stat-label">Articles</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">{len(newsletter.sections)}</span>
                <div class="stat-label">Sections</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">{word_analysis['total_analysis']['actual_words']}</span>
                <div class="stat-label">Words</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">{word_analysis['total_analysis']['utilization']}</span>
                <div class="stat-label">Word Usage</div>
            </div>
        </div>
        
        <div class="word-analysis">
            <h3>📊 Word Usage Analysis</h3>
            <div>
                <strong>Target:</strong> {word_analysis['total_analysis']['target_words']} words | 
                <strong>Actual:</strong> {word_analysis['total_analysis']['actual_words']} words | 
                <strong>Status:</strong> {'✅ Within Limit' if word_analysis['total_analysis']['within_limit'] else '⚠️ Over Limit'}
            </div>
            <div class="progress-bar">
                <div class="progress-fill {'progress-success' if word_analysis['total_analysis']['within_limit'] else 'progress-danger'}" 
                     style="width: {min(100, float(word_analysis['total_analysis']['utilization'].rstrip('%')))}%"></div>
            </div>
        </div>
        
        <div class="content">
            {clean_content}
        </div>
        
        <div class="footer">
            <p>Generated by AI Watchtower • {datetime.utcnow().year}</p>
            <p>Newsletter Format: {newsletter.config.format.value.title()} | Template: {newsletter.config.template.value.title()}</p>
        </div>
    </div>
</body>
</html>"""

        # Write to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_template)

        print(f"✅ Enhanced HTML newsletter exported to: {filepath}")
        print(f"📊 Word usage: {word_analysis['total_analysis']['actual_words']}/{word_analysis['total_analysis']['target_words']} words ({word_analysis['total_analysis']['utilization']})")
        
        return filepath

    def _clean_and_convert_content(self, newsletter: Newsletter) -> str:
        """Clean newsletter content and convert to proper HTML sections"""
        html_sections = []
        
        # Get word analysis for section-level word counts
        word_analysis = newsletter.get_detailed_word_analysis()
        
        # Process each section separately
        for section_name, section_content in newsletter.sections.items():
            section_word_count = word_analysis['section_analysis'].get(section_name, {}).get('word_count', 0)
            section_utilization = word_analysis['section_analysis'].get(section_name, {}).get('utilization', 'N/A')
            
            # Clean the section content
            cleaned_content = self._clean_section_content(section_content)
            
            # Convert to HTML
            html_content = self._markdown_to_html(cleaned_content)
            
            # Create section HTML
            section_html = f'''
            <div class="section">
                <div class="section-header">
                    <h2>{section_name}</h2>
                    <div class="word-count">{section_word_count} words ({section_utilization})</div>
                </div>
                <div class="section-content">
                    {html_content}
                </div>
            </div>
            '''
            
            html_sections.append(section_html)
        
        return '\n'.join(html_sections)

    def _clean_section_content(self, content: str) -> str:
        """Clean section content of redundant headers and formatting issues"""
        lines = content.split('\n')
        cleaned_lines = []
        
        skip_next = False
        for i, line in enumerate(lines):
            if skip_next:
                skip_next = False
                continue
                
            line = line.strip()
            
            # Skip redundant section headers (markdown style)
            if line.startswith('### ') or line.startswith('## '):
                continue
            
            # Skip standalone bold section names
            if line.startswith('**') and line.endswith('**') and len(line.split()) <= 3:
                continue
                
            # Skip word count lines
            if '(word count:' in line.lower() or '(words)' in line.lower():
                continue
                
            # Skip empty lines at start/end
            if not line and (not cleaned_lines or i == len(lines) - 1):
                continue
                
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)

    def _markdown_to_html(self, markdown_content: str) -> str:
        """Enhanced markdown to HTML conversion"""
        if not markdown_content.strip():
            return "<p>No content available for this section.</p>"
        
        html = markdown_content
        
        # Convert headers (but skip h1 and h2 since we handle them separately)
        html = re.sub(r'^#### (.*$)', r'<h4>\1</h4>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.*$)', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        
        # Convert links
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', html)
        
        # Convert bold text
        html = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', html)
        
        # Convert italic text
        html = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', html)
        
        # Split into paragraphs and process
        paragraphs = html.split('\n\n')
        html_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # Skip if already converted to HTML element
            if para.startswith('<h') or para.startswith('<ul') or para.startswith('<ol'):
                html_paragraphs.append(para)
                continue
            
            # Handle bullet points
            if '•' in para or para.startswith('- '):
                items = [item.strip() for item in para.split('\n') if item.strip()]
                ul_content = ""
                for item in items:
                    # Clean bullet point markers
                    clean_item = re.sub(r'^[•\-\*]\s*', '', item.strip())
                    if clean_item:
                        ul_content += f'<li>{clean_item}</li>'
                
                if ul_content:
                    html_paragraphs.append(f'<ul>{ul_content}</ul>')
            else:
                # Regular paragraph
                # Handle line breaks within paragraphs
                para = para.replace('\n', '<br>')
                html_paragraphs.append(f'<p>{para}</p>')
        
        return '\n'.join(html_paragraphs)

    def _add_word_count_to_markdown(self, content: str, word_analysis: Dict[str, Any]) -> str:
        """Add word count information to markdown content"""
        
        word_summary = f"""
---
# Word Usage Summary

**Total Words:** {word_analysis['total_analysis']['actual_words']}/{word_analysis['total_analysis']['target_words']} ({word_analysis['total_analysis']['utilization']})
**Status:** {'✅ Within Limit' if word_analysis['total_analysis']['within_limit'] else '⚠️ Over Limit'}
**Words Remaining:** {word_analysis['total_analysis']['words_remaining']}

## Section Breakdown:
"""
        
        for section_name, section_stats in word_analysis['section_analysis'].items():
            status_icon = "✅" if section_stats['within_limit'] else "⚠️"
            word_summary += f"- **{section_name}:** {section_stats['word_count']} words ({section_stats['utilization']}) {status_icon}\n"
        
        word_summary += "\n---\n\n"
        
        return word_summary + content

    def get_export_stats(self, newsletter: Newsletter) -> Dict[str, Any]:
        """Get export statistics for the newsletter"""
        word_analysis = newsletter.get_detailed_word_analysis()
        
        return {
            "title": newsletter.title,
            "format": newsletter.config.format.value,
            "template": newsletter.config.template.value,
            "total_articles": newsletter.total_articles,
            "sections_count": len(newsletter.sections),
            "generated_at": newsletter.generated_at.isoformat(),
            "word_statistics": word_analysis,
            "file_info": {
                "export_formats": ["html", "markdown"],
                "estimated_file_size": len(newsletter.content) + 2000,  # Rough estimate
            }
        }