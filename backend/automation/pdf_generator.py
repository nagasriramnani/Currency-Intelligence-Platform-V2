"""
PDF Generator for Company Research Reports

Uses WeasyPrint to generate professional PDF reports from HTML templates.

Author: Sapphire Intelligence Platform
Version: 1.0
"""

import os
import logging
from typing import Dict, Any
from datetime import datetime
import tempfile

logger = logging.getLogger(__name__)


def generate_report_html(report: Dict) -> str:
    """Generate HTML for the research report."""
    
    company_name = report.get("company_name", "Company")
    company_overview = report.get("company_overview", {})
    industry_overview = report.get("industry_overview", {})
    financial_overview = report.get("financial_overview", {})
    news = report.get("news", [])
    references = report.get("references", [])
    generated_at = report.get("generated_at", datetime.now().isoformat())
    
    # Format news items
    news_html = ""
    for item in news[:10]:
        news_html += f"""
        <div class="news-item">
            <h4>{item.get('title', 'News')}</h4>
            <p>{item.get('content', '')[:300]}...</p>
        </div>
        """
    
    # Format references
    refs_html = "<ul class='references'>"
    for ref in references[:15]:
        refs_html += f"""<li><a href="{ref.get('url', '#')}">{ref.get('title', 'Source')}</a></li>"""
    refs_html += "</ul>"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{company_name} Research Report</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}
            
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.6;
                color: #1e293b;
                background: white;
            }}
            
            .header {{
                background: linear-gradient(135deg, #1e3a5f 0%, #4f46e5 100%);
                color: white;
                padding: 30px;
                margin: -2cm -2cm 30px -2cm;
                text-align: center;
            }}
            
            .header h1 {{
                margin: 0;
                font-size: 28pt;
                font-weight: 700;
            }}
            
            .header .subtitle {{
                margin-top: 10px;
                font-size: 12pt;
                opacity: 0.9;
            }}
            
            .header .meta {{
                margin-top: 15px;
                font-size: 10pt;
                opacity: 0.7;
            }}
            
            h2 {{
                color: #1e3a5f;
                font-size: 16pt;
                border-bottom: 2px solid #1e3a5f;
                padding-bottom: 8px;
                margin-top: 30px;
            }}
            
            h3 {{
                color: #4f46e5;
                font-size: 13pt;
                margin-top: 20px;
            }}
            
            h4 {{
                color: #334155;
                font-size: 11pt;
                margin: 15px 0 8px 0;
            }}
            
            p {{
                margin: 10px 0;
                text-align: justify;
            }}
            
            .section {{
                margin-bottom: 25px;
                page-break-inside: avoid;
            }}
            
            .highlight-box {{
                background: #f1f5f9;
                border-left: 4px solid #4f46e5;
                padding: 15px;
                margin: 15px 0;
            }}
            
            .news-item {{
                background: #fafafa;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
            }}
            
            .news-item h4 {{
                margin: 0 0 8px 0;
                color: #1e293b;
            }}
            
            .news-item p {{
                margin: 0;
                font-size: 10pt;
                color: #64748b;
            }}
            
            .references {{
                font-size: 9pt;
                color: #64748b;
            }}
            
            .references li {{
                margin: 5px 0;
            }}
            
            .references a {{
                color: #4f46e5;
                text-decoration: none;
            }}
            
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #e2e8f0;
                font-size: 9pt;
                color: #94a3b8;
                text-align: center;
            }}
            
            .badge {{
                display: inline-block;
                background: #4f46e5;
                color: white;
                padding: 3px 10px;
                border-radius: 12px;
                font-size: 9pt;
                margin-right: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{company_name} Research Report</h1>
            <div class="subtitle">Comprehensive Company Analysis</div>
            <div class="meta">
                Generated: {datetime.fromisoformat(generated_at).strftime('%B %d, %Y')} | 
                Powered by Sapphire Intelligence Platform
            </div>
        </div>
        
        <div class="section">
            <h2>Company Overview</h2>
            
            <h3>Business Description</h3>
            <p>{company_overview.get('business_description', 'No data available.')}</p>
            
            <h3>Leadership Team</h3>
            <p>{company_overview.get('leadership_team', 'Leadership information not available.')}</p>
            
            <h3>Target Market</h3>
            <p>{company_overview.get('target_market', 'Market information not available.')}</p>
            
            <h3>Key Differentiators</h3>
            <p>{company_overview.get('key_differentiators', 'Differentiator information not available.')}</p>
            
            <h3>Business Model</h3>
            <p>{company_overview.get('business_model', 'Business model information not available.')}</p>
        </div>
        
        <div class="section">
            <h2>Industry Overview</h2>
            
            <h3>Market Landscape</h3>
            <p>{industry_overview.get('market_landscape', 'Industry analysis pending.')}</p>
            
            <h3>Competition</h3>
            <p>{industry_overview.get('competition', 'Competition analysis not available.')}</p>
            
            <h3>Competitive Advantages</h3>
            <p>{industry_overview.get('competitive_advantages', 'Competitive advantages not identified.')}</p>
            
            <h3>Market Challenges</h3>
            <p>{industry_overview.get('market_challenges', 'Market challenges not identified.')}</p>
        </div>
        
        <div class="section">
            <h2>Financial Overview</h2>
            
            <h3>Funding & Investment</h3>
            <p>{financial_overview.get('funding_investment', 'Funding information not available.')}</p>
            
            <h3>Revenue Model</h3>
            <p>{financial_overview.get('revenue_model', 'Revenue model not identified.')}</p>
            
            <h3>Financial Milestones</h3>
            <p>{financial_overview.get('financial_milestones', 'Financial milestones not available.')}</p>
        </div>
        
        <div class="section">
            <h2>Recent News</h2>
            {news_html if news_html else "<p>No recent news available.</p>"}
        </div>
        
        <div class="section">
            <h2>References</h2>
            {refs_html}
        </div>
        
        <div class="footer">
            <p>This report was generated by Sapphire Intelligence Platform using Tavily AI research.</p>
            <p>For EIS investment analysis, please use the dedicated EIS Investment Scanner.</p>
        </div>
    </body>
    </html>
    """
    
    return html


def generate_pdf(report: Dict) -> bytes:
    """
    Generate PDF from research report.
    
    Returns PDF as bytes.
    """
    try:
        from weasyprint import HTML
        
        html_content = generate_report_html(report)
        
        # Generate PDF
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        logger.info(f"PDF generated: {len(pdf_bytes)} bytes")
        return pdf_bytes
        
    except ImportError:
        logger.error("WeasyPrint not installed. Run: pip install weasyprint")
        raise ImportError("WeasyPrint is required for PDF generation. Install with: pip install weasyprint")
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise


def save_pdf(report: Dict, output_path: str) -> str:
    """
    Generate and save PDF to file.
    
    Returns the output path.
    """
    pdf_bytes = generate_pdf(report)
    
    with open(output_path, 'wb') as f:
        f.write(pdf_bytes)
    
    logger.info(f"PDF saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    # Test PDF generation
    test_report = {
        "company_name": "Test Company Ltd",
        "generated_at": datetime.now().isoformat(),
        "company_overview": {
            "business_description": "A leading technology company specializing in AI solutions.",
            "leadership_team": "CEO: John Smith, CTO: Jane Doe",
            "target_market": "Enterprise software customers",
            "key_differentiators": "Proprietary AI algorithms",
            "business_model": "SaaS subscription model"
        },
        "industry_overview": {
            "market_landscape": "The AI market is rapidly growing.",
            "competition": "Major competitors include Company A and Company B.",
            "competitive_advantages": "First mover advantage in niche market.",
            "market_challenges": "Regulatory uncertainty in AI governance."
        },
        "financial_overview": {
            "funding_investment": "Series B: $50M raised in 2024",
            "revenue_model": "Monthly recurring revenue from subscriptions",
            "financial_milestones": "Reached $10M ARR in 2024"
        },
        "news": [
            {"title": "Company announces new product", "content": "Exciting launch..."},
            {"title": "Partnership with major firm", "content": "Strategic alliance..."}
        ],
        "references": [
            {"title": "Company Website", "url": "https://example.com"},
            {"title": "Crunchbase Profile", "url": "https://crunchbase.com/example"}
        ]
    }
    
    try:
        pdf = generate_pdf(test_report)
        print(f"PDF generated successfully: {len(pdf)} bytes")
    except ImportError as e:
        print(f"Error: {e}")
