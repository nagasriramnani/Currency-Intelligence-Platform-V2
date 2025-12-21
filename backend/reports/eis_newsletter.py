"""
EIS Newsletter PDF Generator

Creates professional PDF newsletters for EIS (Enterprise Investment Scheme) companies.
Designed for investor-ready reporting on portfolio company updates.

Features:
- Executive Summary with real KPIs
- Sector Analysis
- Company Due Diligence Profiles
- Risk Assessment Matrix
- Director/Officer Analysis
- All data from UK Companies House (no fake estimates)
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


def get_company_age(date_of_creation: str) -> int:
    """Calculate company age in years."""
    if not date_of_creation:
        return 0
    try:
        if '-' in date_of_creation:
            created_year = int(date_of_creation.split('-')[0])
        else:
            created_year = int(date_of_creation[:4])
        return datetime.now().year - created_year
    except:
        return 0


def calculate_risk_level(company: Dict) -> Dict[str, Any]:
    """
    Calculate risk level based on REAL data from Companies House.
    
    Risk factors:
    - Insolvency history: High risk
    - Outstanding charges: Medium risk
    - Non-active status: High risk
    - Young company (<2 yrs): Higher risk
    - Mature company (>5 yrs): Lower risk
    """
    has_insolvency = company.get('has_insolvency_history', False)
    has_charges = company.get('has_charges', False)
    status = company.get('company_status', 'active')
    age = get_company_age(company.get('date_of_creation', ''))
    
    if has_insolvency:
        return {'level': 'High', 'score': 8, 'reason': 'Insolvency history'}
    if status != 'active':
        return {'level': 'High', 'score': 7, 'reason': f'Status: {status}'}
    if has_charges:
        return {'level': 'Medium', 'score': 5, 'reason': 'Outstanding charges'}
    if age < 2:
        return {'level': 'High', 'score': 6, 'reason': 'Very young company'}
    if age < 5:
        return {'level': 'Medium', 'score': 4, 'reason': 'Young company'}
    return {'level': 'Low', 'score': 2, 'reason': 'Established company'}


def calculate_eis_eligibility(company: Dict) -> Dict[str, str]:
    """
    Estimate EIS eligibility based on Companies House data.
    
    EIS requirements (simplified):
    - Company must be UK based
    - Less than 7 years old (for SEIS: <2 years)
    - Must be active/trading
    - No insolvency
    """
    age = get_company_age(company.get('date_of_creation', ''))
    status = company.get('company_status', 'active')
    has_insolvency = company.get('has_insolvency_history', False)
    
    if status != 'active':
        return {'status': 'Ineligible', 'reason': 'Company not active'}
    if has_insolvency:
        return {'status': 'Ineligible', 'reason': 'Insolvency history'}
    if age > 7:
        return {'status': 'Review Required', 'reason': 'Company over 7 years old'}
    if age <= 2:
        return {'status': 'SEIS Eligible', 'reason': 'Young company (<2 yrs)'}
    return {'status': 'EIS Eligible', 'reason': f'Company {age} years old'}


class EISNewsletterGenerator:
    """
    Generates professional EIS investment newsletters for investor due diligence.
    Uses only REAL data from UK Companies House - no fake estimates.
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
        All data comes from UK Companies House - no estimates.
        
        Companies may include:
        - eis_assessment: Pre-calculated from backend (if using full-profile endpoint)
        - pscs, charges, filings: Detailed data from Companies House
        """
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("ReportLab not available")
        
        newsletter_date = newsletter_date or date.today()
        
        # Enrich companies with calculated/provided metrics
        enriched_companies = []
        for company in companies:
            enriched = dict(company)
            enriched['sector'] = get_sector_from_sic(company.get('sic_codes', []))
            enriched['company_age'] = get_company_age(company.get('date_of_creation', ''))
            
            # Use pre-calculated EIS assessment if available, otherwise calculate
            if 'eis_assessment' in company and company['eis_assessment']:
                assessment = company['eis_assessment']
                enriched['eis'] = {
                    'status': assessment.get('status', 'Unknown'),
                    'reason': assessment.get('status_description', ''),
                    'score': assessment.get('score', 0)
                }
                enriched['eis_score'] = assessment.get('score', 0)
                enriched['eis_factors'] = assessment.get('factors', [])
                enriched['eis_flags'] = assessment.get('flags', [])
            else:
                enriched['eis'] = calculate_eis_eligibility(company)
                enriched['eis_score'] = None
            
            enriched['risk'] = calculate_risk_level(company)
            
            # Include PSCs, charges if available
            enriched['pscs_data'] = company.get('pscs', [])
            enriched['charges_data'] = company.get('charges', [])
            enriched['filings_data'] = company.get('filings', [])
            enriched['filing_analysis'] = company.get('filing_analysis', {})
            
            enriched_companies.append(enriched)
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                topMargin=0.5*inch, bottomMargin=0.5*inch,
                                leftMargin=0.75*inch, rightMargin=0.75*inch)
        story = []
        
        # Cover Page
        story.extend(self._create_cover_page(enriched_companies, newsletter_date, title))
        story.append(PageBreak())
        
        # Executive Summary
        story.extend(self._create_executive_summary(enriched_companies))
        
        # Sector Analysis
        story.extend(self._create_sector_analysis(enriched_companies))
        
        # Company Profiles
        story.append(Paragraph("Company Due Diligence Profiles", self._styles['SectionHeader']))
        for i, company in enumerate(enriched_companies):
            story.extend(self._create_company_profile(company, i + 1))
        
        # Risk Matrix
        story.append(PageBreak())
        story.extend(self._create_risk_matrix(enriched_companies))
        
        # Footer
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
        
        # Portfolio Stats
        total = len(companies)
        eis_eligible = sum(1 for c in companies if 'Eligible' in c['eis'].get('status', ''))
        sectors = len(set(c['sector'] for c in companies))
        active = sum(1 for c in companies if c.get('company_status') == 'active')
        
        cover_data = [
            ["Portfolio Overview"],
            [f"{total} Companies | {eis_eligible} Likely EIS Eligible* | {sectors} Sectors | {active} Active"],
            [f"Data Source: UK Companies House Registry"],
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
        
        return elements
    
    def _create_executive_summary(self, companies: List[Dict]) -> List:
        """Create executive summary with REAL data only."""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self._styles['SectionHeader']))
        
        total = len(companies)
        
        # EIS breakdown - use flexible matching for both old and new status formats
        # New format: "Likely Eligible", "Review Required", "Likely Ineligible"
        # Old format: "EIS Eligible", "SEIS Eligible", "Ineligible"
        likely_eligible = sum(1 for c in companies if 'Eligible' in c['eis'].get('status', '') and 'Ineligible' not in c['eis'].get('status', ''))
        review_required = sum(1 for c in companies if 'Review' in c['eis'].get('status', ''))
        likely_ineligible = sum(1 for c in companies if 'Ineligible' in c['eis'].get('status', ''))
        
        # Risk breakdown
        low_risk = sum(1 for c in companies if c['risk']['level'] == 'Low')
        med_risk = sum(1 for c in companies if c['risk']['level'] == 'Medium')
        high_risk = sum(1 for c in companies if c['risk']['level'] == 'High')
        
        # Age stats
        ages = [c['company_age'] for c in companies]
        avg_age = sum(ages) / max(len(ages), 1)
        
        # Director count
        total_directors = sum(len(c.get('directors', [])) for c in companies)
        
        summary_data = [
            ["Metric", "Value", "Notes"],
            ["Total Companies", str(total), "Companies in this report"],
            ["Likely EIS Eligible*", str(likely_eligible), f"{likely_eligible/max(total,1)*100:.0f}% of portfolio (heuristic assessment)"],
            ["Review Required", str(review_required), "Needs manual verification"],
            ["Likely Ineligible", str(likely_ineligible), "Exclusion factors identified"],
            ["Low Risk", str(low_risk), "Established, no flags"],
            ["Medium Risk", str(med_risk), "Young or has charges"],
            ["High Risk", str(high_risk), "Insolvency or non-active"],
            ["Average Age", f"{avg_age:.1f} years", "Company maturity"],
            ["Total Directors", str(total_directors), "Named officers"],
        ]
        
        table = Table(summary_data, colWidths=[1.8*inch, 1.2*inch, 2.5*inch])
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
    
    def _create_sector_analysis(self, companies: List[Dict]) -> List:
        """Create sector breakdown."""
        elements = []
        
        elements.append(Paragraph("Sector Analysis", self._styles['SectionHeader']))
        
        # Count by sector
        sector_data = {}
        for c in companies:
            sector = c['sector']
            if sector not in sector_data:
                sector_data[sector] = {'count': 0, 'eis': 0, 'companies': []}
            sector_data[sector]['count'] += 1
            if 'Eligible' in c['eis'].get('status', ''):
                sector_data[sector]['eis'] += 1
            sector_data[sector]['companies'].append(c.get('company_name', 'Unknown'))
        
        table_data = [["Sector", "Companies", "Likely Eligible*", "% of Portfolio"]]
        total = len(companies)
        
        for sector in sorted(sector_data.keys()):
            data = sector_data[sector]
            pct = (data['count'] / max(total, 1)) * 100
            table_data.append([
                sector,
                str(data['count']),
                str(data['eis']),
                f"{pct:.1f}%"
            ])
        
        table = Table(table_data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        table.setStyle(TableStyle([
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
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_company_profile(self, company: Dict, index: int) -> List:
        """Create detailed company profile with REAL data."""
        elements = []
        
        company_name = company.get('company_name', 'Unknown Company')
        elements.append(Paragraph(f"{index}. {company_name}", self._styles['CompanyName']))
        
        # Basic info row with EIS score if available
        company_num = company.get('company_number', 'N/A')
        status = company.get('company_status', 'Unknown').title()
        eis_status = company['eis']['status']
        risk_level = company['risk']['level']
        eis_score = company.get('eis_score')
        
        if eis_score is not None:
            eis_display = f"EIS: {eis_status} ({eis_score}/100)"
        else:
            eis_display = f"EIS: {eis_status}"
        
        metrics_data = [[
            f"Company #: {company_num}",
            f"Status: {status}",
            eis_display,
            f"Risk: {risk_level}"
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
        
        # Details row
        details_data = [[
            f"Sector: {company['sector']}",
            f"Age: {company['company_age']} years",
            f"Jurisdiction: {company.get('jurisdiction', 'UK')}",
        ]]
        
        details_table = Table(details_data, colWidths=[1.87*inch]*3)
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ebf8ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.ACCENT_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 0.5, self.ACCENT_COLOR)
        ]))
        elements.append(details_table)
        elements.append(Spacer(1, 5))
        
        # Address
        address = company.get('registered_office_address', {})
        location_parts = []
        if address.get('address_line_1'):
            location_parts.append(address['address_line_1'])
        if address.get('address_line_2'):
            location_parts.append(address['address_line_2'])
        if address.get('locality'):
            location_parts.append(address['locality'])
        if address.get('postal_code'):
            location_parts.append(address['postal_code'])
        location = ", ".join(location_parts) if location_parts else "N/A"
        
        elements.append(Paragraph(f"<b>Registered Office:</b> {location}", self._styles['NewsletterBody']))
        
        # Incorporation date
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
        
        # Risk explanation
        elements.append(Paragraph(
            f"<b>Risk Assessment:</b> {company['risk']['level']} - {company['risk']['reason']}",
            self._styles['NewsletterBody']
        ))
        
        # EIS explanation
        elements.append(Paragraph(
            f"<b>EIS Status:</b> {company['eis']['status']} - {company['eis']['reason']}",
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
        
        elements.append(Paragraph(f"<b>Flags:</b> {' | '.join(flags)}", self._styles['NewsletterBody']))
        
        elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_risk_matrix(self, companies: List[Dict]) -> List:
        """Create risk assessment matrix."""
        elements = []
        
        elements.append(Paragraph("Risk Assessment Matrix", self._styles['SectionHeader']))
        
        risk_data = [["Company", "Sector", "Age", "Risk", "EIS Status", "Flags"]]
        
        for c in companies:
            name = c.get('company_name', 'Unknown')[:25]
            if len(c.get('company_name', '')) > 25:
                name += "..."
            
            flags = []
            if c.get('has_insolvency_history'):
                flags.append("INS")
            if c.get('has_charges'):
                flags.append("CHG")
            flag_str = ", ".join(flags) if flags else "None"
            
            risk_data.append([
                name,
                c['sector'][:12],
                f"{c['company_age']}y",
                c['risk']['level'],
                c['eis']['status'][:10],
                flag_str
            ])
        
        table = Table(risk_data, colWidths=[1.8*inch, 1*inch, 0.5*inch, 0.7*inch, 0.9*inch, 0.6*inch])
        table.setStyle(TableStyle([
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
        elements.append(table)
        elements.append(Spacer(1, 15))
        
        elements.append(Paragraph(
            "<b>Legend:</b> INS = Insolvency History | CHG = Outstanding Charges",
            self._styles['SmallText']
        ))
        
        return elements
    
    def _create_footer(self) -> List:
        """Create professional footer with explicit EIS-status disclaimer."""
        elements = []
        
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("─" * 80, self._styles['SmallText']))
        elements.append(Spacer(1, 10))
        
        # EIS-STATUS DISCLAIMER (prominent)
        elements.append(Paragraph(
            "<b>⚠️ EIS STATUS DISCLAIMER</b>",
            ParagraphStyle(name='DisclaimerHeader', fontSize=9, textColor=self.WARNING_COLOR, alignment=TA_CENTER)
        ))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(
            "The EIS eligibility indicators in this report are HEURISTIC-BASED ASSESSMENTS derived from UK Companies House data. "
            "HMRC does not provide a public API for EIS registration verification. "
            "<b>EIS registration status cannot be programmatically verified.</b> "
            "Terms such as 'Likely Eligible' indicate heuristic likelihood only, NOT official HMRC confirmation. "
            "Actual EIS eligibility requires formal HMRC Advance Assurance application.",
            ParagraphStyle(name='EISDisclaimer', fontSize=8, textColor=colors.HexColor('#dd6b20'), alignment=TA_CENTER)
        ))
        elements.append(Spacer(1, 10))
        
        # Data source note
        elements.append(Paragraph(
            "<b>Data Source:</b> All company information is sourced directly from the UK Companies House Registry. "
            "EIS-likelihood scores are calculated using 10 heuristic factors including: company age, status, "
            "SIC codes, insolvency history, charges, and filing patterns.",
            ParagraphStyle(name='DataNote', fontSize=8, textColor=colors.HexColor('#718096'), alignment=TA_CENTER)
        ))
        elements.append(Spacer(1, 10))
        
        elements.append(Paragraph(
            "IMPORTANT: This report is for informational purposes only and does not constitute investment advice. "
            "EIS investments carry significant risk including potential loss of capital. "
            "Investors must verify EIS status directly with HMRC or the company before investing. "
            "Do not rely solely on this assessment for investment decisions.",
            ParagraphStyle(name='Disclaimer', fontSize=7, textColor=colors.HexColor('#a0aec0'), alignment=TA_CENTER)
        ))
        elements.append(Spacer(1, 15))
        elements.append(Paragraph(
            f"Generated by Sapphire Intelligence Platform | {datetime.now().strftime('%Y-%m-%d %H:%M')}",
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
