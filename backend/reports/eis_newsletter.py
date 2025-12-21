"""
EIS Newsletter PDF Generator

Creates professional PDF newsletters for EIS (Enterprise Investment Scheme) companies.
Designed for investor-ready reporting on portfolio company updates.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from io import BytesIO

logger = logging.getLogger(__name__)

# Try to import reportlab
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, ListFlowable, ListItem
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab not installed for EIS newsletter generation")


class EISNewsletterGenerator:
    """
    Generates professional EIS investment newsletters.
    
    Features:
    - Company profiles with key metrics
    - Sector analysis
    - Risk indicators
    - Investment stage breakdown
    - Director highlights
    """
    
    # Sapphire brand colors
    PRIMARY_COLOR = colors.HexColor('#1a365d')  # Dark blue
    ACCENT_COLOR = colors.HexColor('#3182ce')   # Bright blue
    SUCCESS_COLOR = colors.HexColor('#38a169')  # Green
    WARNING_COLOR = colors.HexColor('#dd6b20')  # Orange
    DANGER_COLOR = colors.HexColor('#e53e3e')   # Red
    
    def __init__(self):
        if REPORTLAB_AVAILABLE:
            self._styles = getSampleStyleSheet()
            self._add_custom_styles()
    
    def _add_custom_styles(self):
        """Add custom styles for EIS newsletter."""
        def safe_add(name, **kwargs):
            if name not in self._styles.byName:
                self._styles.add(ParagraphStyle(name=name, **kwargs))
        
        safe_add(
            'NewsletterTitle',
            parent=self._styles['Heading1'],
            fontSize=28,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=self.PRIMARY_COLOR
        )
        
        safe_add(
            'NewsletterSubtitle',
            parent=self._styles['Normal'],
            fontSize=12,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#718096')
        )
        
        safe_add(
            'SectionHeader',
            parent=self._styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=self.PRIMARY_COLOR
        )
        
        safe_add(
            'CompanyName',
            parent=self._styles['Heading3'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=5,
            textColor=self.ACCENT_COLOR
        )
        
        safe_add(
            'NewsletterBody',
            parent=self._styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            textColor=colors.HexColor('#2d3748')
        )
        
        safe_add(
            'MetricLabel',
            parent=self._styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#718096')
        )
        
        safe_add(
            'MetricValue',
            parent=self._styles['Normal'],
            fontSize=11,
            textColor=self.PRIMARY_COLOR,
            fontName='Helvetica-Bold'
        )
    
    def generate_newsletter(
        self,
        companies: List[Dict[str, Any]],
        newsletter_date: Optional[date] = None,
        title: str = "EIS Investment Newsletter"
    ) -> bytes:
        """
        Generate EIS newsletter PDF.
        
        Args:
            companies: List of EIS company data dictionaries
            newsletter_date: Date for the newsletter (defaults to today)
            title: Newsletter title
            
        Returns:
            PDF as bytes
        """
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("ReportLab not available")
        
        newsletter_date = newsletter_date or date.today()
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        
        # Header
        story.append(Paragraph("SAPPHIRE CAPITAL PARTNERS", self._styles['NewsletterSubtitle']))
        story.append(Paragraph(title, self._styles['NewsletterTitle']))
        story.append(Paragraph(
            f"Issue Date: {newsletter_date.strftime('%B %d, %Y')} | Companies Featured: {len(companies)}",
            self._styles['NewsletterSubtitle']
        ))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self._styles['SectionHeader']))
        story.append(self._create_summary_table(companies))
        story.append(Spacer(1, 20))
        
        # Sector Breakdown
        story.append(Paragraph("Sector Analysis", self._styles['SectionHeader']))
        story.append(self._create_sector_table(companies))
        story.append(Spacer(1, 20))
        
        # Company Profiles
        story.append(Paragraph("Featured Companies", self._styles['SectionHeader']))
        for company in companies:
            story.extend(self._create_company_section(company))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            "This newsletter is for informational purposes only and does not constitute investment advice. "
            "EIS investments carry significant risk and may not be suitable for all investors.",
            ParagraphStyle(
                name='Disclaimer',
                fontSize=8,
                textColor=colors.HexColor('#a0aec0'),
                alignment=TA_CENTER
            )
        ))
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            f"Generated by Sapphire Intelligence Platform | {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            ParagraphStyle(
                name='Footer',
                fontSize=8,
                textColor=colors.HexColor('#a0aec0'),
                alignment=TA_CENTER
            )
        ))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _create_summary_table(self, companies: List[Dict]) -> Table:
        """Create executive summary table."""
        # Aggregate stats
        total_companies = len(companies)
        approved = sum(1 for c in companies if c.get('eis_status') == 'Approved')
        total_raised = sum(c.get('amount_raised', 0) for c in companies)
        sectors = len(set(c.get('sector', 'Unknown') for c in companies))
        
        data = [
            ["Total Companies", "EIS Approved", "Total Raised", "Sectors"],
            [str(total_companies), str(approved), f"£{total_raised:,.0f}", str(sectors)]
        ]
        
        table = Table(data, colWidths=[1.5*inch]*4)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#ebf8ff')),
            ('TEXTCOLOR', (0, 1), (-1, 1), self.PRIMARY_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, 1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0'))
        ]))
        return table
    
    def _create_sector_table(self, companies: List[Dict]) -> Table:
        """Create sector breakdown table."""
        # Count by sector
        sector_counts = {}
        sector_amounts = {}
        for c in companies:
            sector = c.get('sector', 'Unknown')
            sector_counts[sector] = sector_counts.get(sector, 0) + 1
            sector_amounts[sector] = sector_amounts.get(sector, 0) + c.get('amount_raised', 0)
        
        data = [["Sector", "Companies", "Total Raised"]]
        for sector in sorted(sector_counts.keys()):
            data.append([
                sector,
                str(sector_counts[sector]),
                f"£{sector_amounts[sector]:,.0f}"
            ])
        
        table = Table(data, colWidths=[2.5*inch, 1.2*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.ACCENT_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
        ]))
        return table
    
    def _create_company_section(self, company: Dict) -> List:
        """Create company profile section."""
        elements = []
        
        # Company name
        elements.append(Paragraph(
            company.get('company_name', 'Unknown Company'),
            self._styles['CompanyName']
        ))
        
        # Key metrics row
        risk_color = {
            'Low': self.SUCCESS_COLOR,
            'Medium': self.WARNING_COLOR,
            'High': self.DANGER_COLOR
        }.get(company.get('risk_score', 'Medium'), self.WARNING_COLOR)
        
        metrics_data = [[
            f"Status: {company.get('eis_status', 'N/A')}",
            f"Stage: {company.get('investment_stage', 'N/A')}",
            f"Raised: £{company.get('amount_raised', 0):,.0f}",
            f"Risk: {company.get('risk_score', 'N/A')}"
        ]]
        
        metrics_table = Table(metrics_data, colWidths=[1.4*inch]*4)
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#4a5568')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0'))
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 5))
        
        # Company details
        address = company.get('registered_office_address', {})
        location = f"{address.get('locality', 'N/A')}, {address.get('country', 'UK')}"
        
        details = f"""
        <b>Sector:</b> {company.get('sector', 'N/A')} | 
        <b>Location:</b> {location} | 
        <b>Founded:</b> {company.get('date_of_creation', 'N/A')}
        """
        elements.append(Paragraph(details.strip(), self._styles['NewsletterBody']))
        
        # Directors
        directors = company.get('directors', [])
        if directors:
            director_names = ", ".join([d.get('name', 'Unknown') for d in directors[:3]])
            elements.append(Paragraph(
                f"<b>Key Directors:</b> {director_names}",
                self._styles['NewsletterBody']
            ))
        
        elements.append(Spacer(1, 10))
        
        return elements


def generate_eis_newsletter(companies: List[Dict], title: str = "EIS Investment Newsletter") -> bytes:
    """Convenience function to generate EIS newsletter."""
    generator = EISNewsletterGenerator()
    return generator.generate_newsletter(companies, title=title)


def is_available() -> bool:
    """Check if EIS newsletter generation is available."""
    return REPORTLAB_AVAILABLE
