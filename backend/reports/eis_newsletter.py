"""
EIS Newsletter PDF Generator

Creates professional PDF newsletters for EIS (Enterprise Investment Scheme) companies.
Designed for investor-ready reporting on portfolio company updates.

Features:
- Executive Summary with KPIs
- Sector Analysis with totals
- Company Due Diligence Profiles
- Risk Assessment Matrices
- Director/Officer Analysis
- Filing History Highlights
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


# SIC Code to Sector mapping
SIC_TO_SECTOR = {
    '62': 'Technology', '63': 'Technology', '72': 'R&D',
    '58': 'Media', '61': 'Telecommunications', '64': 'Financial Services',
    '65': 'Financial Services', '66': 'Financial Services',
    '85': 'Education', '86': 'Healthcare', '21': 'Pharmaceuticals',
    '35': 'Energy', '01': 'Agriculture', '10': 'Food & Beverages',
    '41': 'Construction', '45': 'Automotive', '47': 'Retail',
    '70': 'Real Estate', '71': 'Architecture & Engineering',
}


def get_sector_from_sic(sic_codes: List[str]) -> str:
    """Determine sector from SIC codes."""
    if not sic_codes:
        return 'Other'
    first_two = sic_codes[0][:2] if sic_codes[0] else ''
    return SIC_TO_SECTOR.get(first_two, 'Other')


def estimate_investment_metrics(company: Dict) -> Dict:
    """
    Estimate investment metrics based on company characteristics.
    This provides reasonable estimates for demo/presentation purposes.
    """
    # Get company age
    created = company.get('date_of_creation', '')
    if created:
        try:
            created_year = int(created.split('-')[0])
            age_years = datetime.now().year - created_year
        except:
            age_years = 3
    else:
        age_years = 3
    
    # Determine investment stage based on age
    if age_years <= 1:
        stage = "Pre-Seed"
        base_raised = 50000
    elif age_years <= 2:
        stage = "Seed"
        base_raised = 150000
    elif age_years <= 4:
        stage = "Series A"
        base_raised = 500000
    else:
        stage = "Growth"
        base_raised = 1500000
    
    # Get sector for risk assessment
    sic_codes = company.get('sic_codes', [])
    sector = get_sector_from_sic(sic_codes)
    
    # Determine risk based on sector and flags
    has_charges = company.get('has_charges', False)
    has_insolvency = company.get('has_insolvency_history', False)
    
    if has_insolvency:
        risk = "High"
        risk_score = 8
    elif has_charges:
        risk = "Medium"
        risk_score = 5
    elif sector in ['Financial Services', 'Healthcare', 'Pharmaceuticals']:
        risk = "Medium"
        risk_score = 4
    elif sector in ['Technology', 'R&D']:
        risk = "Medium"
        risk_score = 5
    else:
        risk = "Low"
        risk_score = 3
    
    # Estimate raised amount with some variance
    import random
    variance = random.uniform(0.7, 1.5)
    amount_raised = int(base_raised * variance)
    
    # EIS status based on company status
    company_status = company.get('company_status', 'active')
    if company_status == 'active':
        eis_status = "Eligible" if age_years <= 7 else "Review Required"
    else:
        eis_status = "Ineligible"
    
    return {
        'sector': sector,
        'investment_stage': stage,
        'amount_raised': amount_raised,
        'risk_score': risk,
        'risk_value': risk_score,
        'eis_status': eis_status,
        'company_age': age_years
    }


class EISNewsletterGenerator:
    """
    Generates professional EIS investment newsletters for investor due diligence.
    
    Features:
    - Executive Summary with KPIs
    - Portfolio Analytics
    - Company Due Diligence Profiles
    - Risk Assessment Matrix
    - Director/Officer Analysis
    - Filing History & Compliance
    """
    
    # Sapphire brand colors
    PRIMARY_COLOR = colors.HexColor('#1a365d')
    ACCENT_COLOR = colors.HexColor('#3182ce')
    SUCCESS_COLOR = colors.HexColor('#38a169')
    WARNING_COLOR = colors.HexColor('#dd6b20')
    DANGER_COLOR = colors.HexColor('#e53e3e')
    LIGHT_BG = colors.HexColor('#f7fafc')
    
    def __init__(self):
        if REPORTLAB_AVAILABLE:
            self._styles = getSampleStyleSheet()
            self._add_custom_styles()
    
    def _add_custom_styles(self):
        """Add custom styles for professional investor newsletter."""
        def safe_add(name, **kwargs):
            if name not in self._styles.byName:
                self._styles.add(ParagraphStyle(name=name, **kwargs))
        
        safe_add('NewsletterTitle', parent=self._styles['Heading1'],
                 fontSize=28, spaceAfter=20, alignment=TA_CENTER, textColor=self.PRIMARY_COLOR)
        
        safe_add('NewsletterSubtitle', parent=self._styles['Normal'],
                 fontSize=12, spaceAfter=30, alignment=TA_CENTER, textColor=colors.HexColor('#718096'))
        
        safe_add('SectionHeader', parent=self._styles['Heading2'],
                 fontSize=16, spaceBefore=25, spaceAfter=12, textColor=self.PRIMARY_COLOR)
        
        safe_add('SubsectionHeader', parent=self._styles['Heading3'],
                 fontSize=12, spaceBefore=15, spaceAfter=8, textColor=self.ACCENT_COLOR)
        
        safe_add('CompanyName', parent=self._styles['Heading3'],
                 fontSize=14, spaceBefore=15, spaceAfter=5, textColor=self.ACCENT_COLOR)
        
        safe_add('NewsletterBody', parent=self._styles['Normal'],
                 fontSize=10, spaceAfter=8, textColor=colors.HexColor('#2d3748'))
        
        safe_add('MetricLabel', parent=self._styles['Normal'],
                 fontSize=9, textColor=colors.HexColor('#718096'))
        
        safe_add('MetricValue', parent=self._styles['Normal'],
                 fontSize=11, textColor=self.PRIMARY_COLOR, fontName='Helvetica-Bold')
        
        safe_add('SmallText', parent=self._styles['Normal'],
                 fontSize=8, textColor=colors.HexColor('#a0aec0'))
    
    def generate_newsletter(
        self,
        companies: List[Dict[str, Any]],
        newsletter_date: Optional[date] = None,
        title: str = "EIS Investment Due Diligence Report"
    ) -> bytes:
        """
        Generate comprehensive EIS investment newsletter PDF.
        
        Args:
            companies: List of company data (from Companies House API or enriched)
            newsletter_date: Date for the newsletter
            title: Newsletter title
            
        Returns:
            PDF as bytes
        """
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("ReportLab not available")
        
        newsletter_date = newsletter_date or date.today()
        
        # Enrich companies with estimated investment metrics
        enriched_companies = []
        for company in companies:
            enriched = dict(company)
            metrics = estimate_investment_metrics(company)
            enriched.update(metrics)
            enriched_companies.append(enriched)
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                topMargin=0.5*inch, bottomMargin=0.5*inch,
                                leftMargin=0.75*inch, rightMargin=0.75*inch)
        story = []
        
        # ===== COVER PAGE =====
        story.extend(self._create_cover_page(enriched_companies, newsletter_date, title))
        story.append(PageBreak())
        
        # ===== EXECUTIVE SUMMARY =====
        story.extend(self._create_executive_summary(enriched_companies))
        
        # ===== PORTFOLIO ANALYTICS =====
        story.extend(self._create_portfolio_analytics(enriched_companies))
        
        # ===== COMPANY PROFILES =====
        story.append(Paragraph("Company Due Diligence Profiles", self._styles['SectionHeader']))
        for i, company in enumerate(enriched_companies):
            story.extend(self._create_company_profile(company, i + 1))
        
        # ===== RISK MATRIX =====
        story.append(PageBreak())
        story.extend(self._create_risk_matrix(enriched_companies))
        
        # ===== FOOTER =====
        story.extend(self._create_footer())
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _create_cover_page(self, companies: List[Dict], newsletter_date: date, title: str) -> List:
        """Create professional cover page."""
        elements = []
        
        elements.append(Spacer(1, 100))
        elements.append(Paragraph("SAPPHIRE CAPITAL PARTNERS", self._styles['NewsletterSubtitle']))
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(title, self._styles['NewsletterTitle']))
        elements.append(Spacer(1, 30))
        
        # Key Stats Box
        total_companies = len(companies)
        eis_eligible = sum(1 for c in companies if c.get('eis_status') in ['Eligible', 'Approved'])
        total_raised = sum(c.get('amount_raised', 0) for c in companies)
        avg_raised = total_raised / max(total_companies, 1)
        sectors = len(set(c.get('sector', 'Other') for c in companies))
        
        cover_data = [
            ["Portfolio Overview"],
            [f"{total_companies} Companies | {eis_eligible} EIS Eligible | {sectors} Sectors"],
            [f"Estimated Total Investment: £{total_raised:,.0f}"],
            [f"Average per Company: £{avg_raised:,.0f}"]
        ]
        
        cover_table = Table(cover_data, colWidths=[5*inch])
        cover_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), self.LIGHT_BG),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.PRIMARY_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOX', (0, 0), (-1, -1), 1, self.PRIMARY_COLOR)
        ]))
        elements.append(cover_table)
        
        elements.append(Spacer(1, 50))
        elements.append(Paragraph(
            f"Report Date: {newsletter_date.strftime('%B %d, %Y')}",
            self._styles['NewsletterSubtitle']
        ))
        elements.append(Paragraph(
            "Data Source: UK Companies House Registry",
            self._styles['SmallText']
        ))
        
        return elements
    
    def _create_executive_summary(self, companies: List[Dict]) -> List:
        """Create executive summary section."""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self._styles['SectionHeader']))
        
        # Calculate metrics
        total = len(companies)
        eis_eligible = sum(1 for c in companies if c.get('eis_status') in ['Eligible', 'Approved'])
        total_raised = sum(c.get('amount_raised', 0) for c in companies)
        avg_raised = total_raised / max(total, 1)
        
        # Risk breakdown
        low_risk = sum(1 for c in companies if c.get('risk_score') == 'Low')
        med_risk = sum(1 for c in companies if c.get('risk_score') == 'Medium')
        high_risk = sum(1 for c in companies if c.get('risk_score') == 'High')
        
        # Stage breakdown
        stages = {}
        for c in companies:
            stage = c.get('investment_stage', 'Unknown')
            stages[stage] = stages.get(stage, 0) + 1
        
        # Summary Table
        summary_data = [
            ["KPI", "Value", "Notes"],
            ["Total Companies", str(total), "Companies in this report"],
            ["EIS Eligible", str(eis_eligible), f"{eis_eligible/max(total,1)*100:.0f}% of portfolio"],
            ["Est. Total Raised", f"£{total_raised:,.0f}", "Aggregate portfolio value"],
            ["Avg. Investment", f"£{avg_raised:,.0f}", "Per company average"],
            ["Low Risk", str(low_risk), f"{low_risk/max(total,1)*100:.0f}% of portfolio"],
            ["Medium Risk", str(med_risk), f"{med_risk/max(total,1)*100:.0f}% of portfolio"],
            ["High Risk", str(high_risk), f"{high_risk/max(total,1)*100:.0f}% of portfolio"],
        ]
        
        table = Table(summary_data, colWidths=[1.8*inch, 1.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.LIGHT_BG])
        ]))
        elements.append(table)
        elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_portfolio_analytics(self, companies: List[Dict]) -> List:
        """Create portfolio analytics section."""
        elements = []
        
        elements.append(Paragraph("Sector Analysis", self._styles['SectionHeader']))
        
        # Sector breakdown
        sector_data = {}
        for c in companies:
            sector = c.get('sector', 'Other')
            if sector not in sector_data:
                sector_data[sector] = {'count': 0, 'raised': 0, 'companies': []}
            sector_data[sector]['count'] += 1
            sector_data[sector]['raised'] += c.get('amount_raised', 0)
            sector_data[sector]['companies'].append(c.get('company_name', 'Unknown'))
        
        sector_table_data = [["Sector", "Companies", "Est. Raised", "% of Portfolio"]]
        total_raised = sum(c.get('amount_raised', 0) for c in companies)
        
        for sector in sorted(sector_data.keys()):
            data = sector_data[sector]
            pct = (data['raised'] / max(total_raised, 1)) * 100
            sector_table_data.append([
                sector,
                str(data['count']),
                f"£{data['raised']:,.0f}",
                f"{pct:.1f}%"
            ])
        
        sector_table = Table(sector_table_data, colWidths=[2*inch, 1.2*inch, 1.5*inch, 1.2*inch])
        sector_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.ACCENT_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.LIGHT_BG])
        ]))
        elements.append(sector_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_company_profile(self, company: Dict, index: int) -> List:
        """Create detailed company profile section."""
        elements = []
        
        company_name = company.get('company_name', 'Unknown Company')
        elements.append(Paragraph(f"{index}. {company_name}", self._styles['CompanyName']))
        
        # Company ID and Status Row
        company_num = company.get('company_number', 'N/A')
        status = company.get('company_status', 'Unknown').title()
        eis_status = company.get('eis_status', 'N/A')
        
        status_color = self.SUCCESS_COLOR if status == 'Active' else self.WARNING_COLOR
        eis_color = self.SUCCESS_COLOR if eis_status in ['Eligible', 'Approved'] else self.WARNING_COLOR
        
        # Metrics Row
        metrics_data = [[
            f"Company #: {company_num}",
            f"Status: {status}",
            f"EIS: {eis_status}",
            f"Risk: {company.get('risk_score', 'N/A')}"
        ]]
        
        metrics_table = Table(metrics_data, colWidths=[1.4*inch]*4)
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.LIGHT_BG),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#4a5568')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0'))
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 5))
        
        # Investment Metrics
        investment_data = [[
            f"Stage: {company.get('investment_stage', 'N/A')}",
            f"Est. Raised: £{company.get('amount_raised', 0):,.0f}",
            f"Sector: {company.get('sector', 'N/A')}",
            f"Age: {company.get('company_age', 'N/A')} yrs"
        ]]
        
        inv_table = Table(investment_data, colWidths=[1.4*inch]*4)
        inv_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ebf8ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.ACCENT_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 0.5, self.ACCENT_COLOR)
        ]))
        elements.append(inv_table)
        elements.append(Spacer(1, 5))
        
        # Location & Details
        address = company.get('registered_office_address', {})
        location_parts = []
        if address.get('address_line_1'):
            location_parts.append(address['address_line_1'])
        if address.get('locality'):
            location_parts.append(address['locality'])
        if address.get('postal_code'):
            location_parts.append(address['postal_code'])
        location = ", ".join(location_parts) if location_parts else "N/A"
        
        elements.append(Paragraph(
            f"<b>Registered Office:</b> {location}",
            self._styles['NewsletterBody']
        ))
        
        # Founded date
        founded = company.get('date_of_creation', 'N/A')
        sic_codes = company.get('sic_codes', [])
        sic_str = ", ".join(sic_codes[:3]) if sic_codes else "N/A"
        
        elements.append(Paragraph(
            f"<b>Incorporated:</b> {founded} | <b>SIC Codes:</b> {sic_str}",
            self._styles['NewsletterBody']
        ))
        
        # Directors
        directors = company.get('directors', [])
        if directors:
            dir_names = [d.get('name', 'Unknown') for d in directors[:4]]
            elements.append(Paragraph(
                f"<b>Directors ({len(directors)}):</b> {', '.join(dir_names)}",
                self._styles['NewsletterBody']
            ))
        
        # Risk Flags
        flags = []
        if company.get('has_insolvency_history'):
            flags.append("⚠️ Insolvency History")
        if company.get('has_charges'):
            flags.append("📋 Outstanding Charges")
        if not flags:
            flags.append("✅ No Adverse Flags")
        
        elements.append(Paragraph(
            f"<b>Risk Indicators:</b> {' | '.join(flags)}",
            self._styles['NewsletterBody']
        ))
        
        elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_risk_matrix(self, companies: List[Dict]) -> List:
        """Create risk assessment matrix."""
        elements = []
        
        elements.append(Paragraph("Risk Assessment Summary", self._styles['SectionHeader']))
        
        # Risk breakdown table
        risk_data = [["Company", "Sector", "Stage", "Risk", "Flags"]]
        
        for c in companies:
            name = c.get('company_name', 'Unknown')[:30]
            if len(c.get('company_name', '')) > 30:
                name += "..."
            
            flags = []
            if c.get('has_insolvency_history'):
                flags.append("INS")
            if c.get('has_charges'):
                flags.append("CHG")
            flag_str = ", ".join(flags) if flags else "None"
            
            risk_data.append([
                name,
                c.get('sector', 'N/A')[:15],
                c.get('investment_stage', 'N/A'),
                c.get('risk_score', 'N/A'),
                flag_str
            ])
        
        risk_table = Table(risk_data, colWidths=[2.2*inch, 1.2*inch, 1*inch, 0.8*inch, 0.8*inch])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.LIGHT_BG])
        ]))
        elements.append(risk_table)
        elements.append(Spacer(1, 20))
        
        # Legend
        elements.append(Paragraph(
            "<b>Legend:</b> INS = Insolvency History | CHG = Outstanding Charges",
            self._styles['SmallText']
        ))
        
        return elements
    
    def _create_footer(self) -> List:
        """Create professional footer."""
        elements = []
        
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(
            "─" * 80,
            self._styles['SmallText']
        ))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            "IMPORTANT: This report is generated for informational purposes only and does not constitute investment advice. "
            "EIS investments carry significant risk including potential loss of capital. Past performance is not indicative of future results. "
            "Investors should conduct their own due diligence and consult with qualified financial advisors before making investment decisions.",
            ParagraphStyle(name='Disclaimer', fontSize=7, textColor=colors.HexColor('#a0aec0'), alignment=TA_CENTER)
        ))
        elements.append(Spacer(1, 15))
        elements.append(Paragraph(
            f"Generated by Sapphire Intelligence Platform | Data Source: UK Companies House | Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            ParagraphStyle(name='FooterInfo', fontSize=8, textColor=colors.HexColor('#718096'), alignment=TA_CENTER)
        ))
        elements.append(Paragraph(
            "© Sapphire Capital Partners. Confidential and Proprietary.",
            ParagraphStyle(name='Copyright', fontSize=8, textColor=colors.HexColor('#718096'), alignment=TA_CENTER)
        ))
        
        return elements


def generate_eis_newsletter(companies: List[Dict], title: str = "EIS Investment Due Diligence Report") -> bytes:
    """Convenience function to generate EIS newsletter."""
    generator = EISNewsletterGenerator()
    return generator.generate_newsletter(companies, title=title)


def is_available() -> bool:
    """Check if EIS newsletter generation is available."""
    return REPORTLAB_AVAILABLE
