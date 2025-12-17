"""
PDF Report Generator

Creates professional PDF reports for Currency Intelligence Platform.
Uses ReportLab for PDF generation.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, date
from io import BytesIO
import os

logger = logging.getLogger(__name__)

# Try to import reportlab
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
    logger.info("ReportLab loaded - PDF export available")
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab not installed. Run: pip install reportlab")


class PDFReportGenerator:
    """
    Generates professional PDF reports for FX analytics.
    
    Report types:
    - Executive Summary: High-level KPIs and recommendations
    - Risk Report: VaR, stress tests, hedging recommendations
    - Full Analysis: Complete analytics with charts
    """
    
    def __init__(self, title: str = "Currency Intelligence Report"):
        self.title = title
        self._styles = None
        
        if REPORTLAB_AVAILABLE:
            self._styles = getSampleStyleSheet()
            self._add_custom_styles()
    
    def _add_custom_styles(self):
        """Add custom paragraph styles."""
        # Helper to safely add styles
        def safe_add_style(name, **kwargs):
            if name not in self._styles.byName:
                self._styles.add(ParagraphStyle(name=name, **kwargs))
        
        safe_add_style(
            'ReportTitle',
            parent=self._styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1a365d')
        )
        
        safe_add_style(
            'SectionTitle',
            parent=self._styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#2c5282')
        )
        
        safe_add_style(
            'SubSection',
            parent=self._styles['Heading3'],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=5,
            textColor=colors.HexColor('#4a5568')
        )
        
        safe_add_style(
            'ReportBody',  # Renamed from BodyText to avoid collision
            parent=self._styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            textColor=colors.HexColor('#2d3748')
        )
        
        safe_add_style(
            'Highlight',
            parent=self._styles['Normal'],
            fontSize=10,
            backColor=colors.HexColor('#ebf8ff'),
            textColor=colors.HexColor('#2b6cb0'),
            borderPadding=5
        )
    
    def generate_executive_summary(
        self,
        kpis: Dict,
        recommendations: Dict,
        regime: Dict,
        generated_at: Optional[datetime] = None
    ) -> bytes:
        """
        Generate executive summary PDF.
        
        Args:
            kpis: Key performance indicators
            recommendations: Hedging recommendations
            regime: Current market regime
            generated_at: Report timestamp
            
        Returns:
            PDF as bytes
        """
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("ReportLab not available")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Title
        story.append(Paragraph(self.title, self._styles['ReportTitle']))
        story.append(Paragraph(
            f"Executive Summary | {(generated_at or datetime.now()).strftime('%B %d, %Y')}",
            self._styles['ReportBody']
        ))
        story.append(Spacer(1, 20))
        
        # Market Regime
        story.append(Paragraph("Market Regime", self._styles['SectionTitle']))
        if regime:
            regime_table = [
                ["Current Regime", regime.get('regime', 'Unknown')],
                ["Confidence", f"{regime.get('confidence', 0):.0%}"],
                ["Volatility", regime.get('characteristics', {}).get('volatility', 'N/A')],
                ["Trend", regime.get('characteristics', {}).get('trend', 'N/A')],
            ]
            t = Table(regime_table, colWidths=[2*inch, 3*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#edf2f7')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2d3748')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0'))
            ]))
            story.append(t)
            story.append(Spacer(1, 5))
            story.append(Paragraph(
                f"<b>Strategy:</b> {regime.get('strategy', 'N/A')}",
                self._styles['Highlight']
            ))
        story.append(Spacer(1, 20))
        
        # Recommendations
        story.append(Paragraph("Hedging Recommendations", self._styles['SectionTitle']))
        if recommendations:
            story.append(Paragraph(
                f"<b>Overall Risk Level:</b> {recommendations.get('overall_risk_level', 'N/A').upper()}",
                self._styles['ReportBody']
            ))
            story.append(Paragraph(
                recommendations.get('overall_recommendation', ''),
                self._styles['ReportBody']
            ))
            
            # Currency recommendations table
            currency_recs = recommendations.get('currency_recommendations', [])
            if currency_recs:
                story.append(Spacer(1, 10))
                story.append(Paragraph("Currency-Specific Actions", self._styles['SubSection']))
                
                rec_data = [["Currency", "Action", "Urgency", "Coverage"]]
                for rec in currency_recs:
                    rec_data.append([
                        rec.get('currency', ''),
                        rec.get('action', '').upper(),
                        rec.get('urgency', ''),
                        f"{rec.get('suggested_coverage', 0):.0%}"
                    ])
                
                t = Table(rec_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
                ]))
                story.append(t)
        
        story.append(Spacer(1, 30))
        
        # Footer
        story.append(Paragraph(
            f"Generated by Sapphire Intelligence | {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}",
            ParagraphStyle(
                name='Footer',
                fontSize=8,
                textColor=colors.HexColor('#a0aec0'),
                alignment=TA_CENTER
            )
        ))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_risk_report(
        self,
        var_data: Dict,
        stress_tests: List[Dict],
        recommendations: Dict,
        generated_at: Optional[datetime] = None
    ) -> bytes:
        """
        Generate detailed risk report PDF.
        
        Args:
            var_data: VaR analysis results
            stress_tests: Stress test scenarios
            recommendations: Hedging recommendations
            generated_at: Report timestamp
            
        Returns:
            PDF as bytes
        """
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("ReportLab not available")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Title
        story.append(Paragraph("Risk Analytics Report", self._styles['ReportTitle']))
        story.append(Paragraph(
            f"Generated: {(generated_at or datetime.now()).strftime('%B %d, %Y %H:%M UTC')}",
            self._styles['ReportBody']
        ))
        story.append(Spacer(1, 20))
        
        # VaR Analysis
        story.append(Paragraph("Value-at-Risk Analysis", self._styles['SectionTitle']))
        
        if var_data and 'currencies' in var_data:
            var_table = [["Currency", "VaR (95%)", "CVaR", "Volatility"]]
            for currency, data in var_data['currencies'].items():
                var_vals = data.get('var', {})
                var_table.append([
                    f"USD/{currency}",
                    f"{var_vals.get('parametric', 0):.2f}%",
                    f"{data.get('cvar', 0):.2f}%",
                    f"{data.get('volatility', 0):.1f}%"
                ])
            
            t = Table(var_table, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c53030')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0'))
            ]))
            story.append(t)
        story.append(Spacer(1, 20))
        
        # Stress Tests
        story.append(Paragraph("Stress Test Scenarios", self._styles['SectionTitle']))
        
        if stress_tests:
            stress_table = [["Scenario", "EUR Impact", "GBP Impact", "CAD Impact"]]
            for scenario in stress_tests:
                impacts = scenario.get('impacts', {})
                stress_table.append([
                    scenario.get('name', ''),
                    f"{impacts.get('EUR', 0):.1f}%",
                    f"{impacts.get('GBP', 0):.1f}%",
                    f"{impacts.get('CAD', 0):.1f}%"
                ])
            
            t = Table(stress_table, colWidths=[2*inch, 1.3*inch, 1.3*inch, 1.3*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dd6b20')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0'))
            ]))
            story.append(t)
        
        story.append(PageBreak())
        
        # Recommendations
        story.append(Paragraph("Hedging Recommendations", self._styles['SectionTitle']))
        if recommendations:
            story.append(Paragraph(
                recommendations.get('overall_recommendation', ''),
                self._styles['Highlight']
            ))
            story.append(Spacer(1, 10))
            
            for rec in recommendations.get('currency_recommendations', []):
                story.append(Paragraph(
                    f"<b>{rec.get('currency', '')}:</b> {rec.get('action', '').upper()} - {rec.get('rationale', '')}",
                    self._styles['ReportBody']
                ))
                if rec.get('instruments'):
                    story.append(Paragraph(
                        f"Suggested instruments: {', '.join(rec.get('instruments', []))}",
                        self._styles['ReportBody']
                    ))
                story.append(Spacer(1, 5))
        
        # Disclaimer
        story.append(Spacer(1, 40))
        story.append(Paragraph(
            "<b>Disclaimer:</b> This report is for informational purposes only and does not constitute financial advice. "
            "Past performance does not guarantee future results. Consult with qualified professionals before making investment decisions.",
            ParagraphStyle(
                name='Disclaimer',
                fontSize=8,
                textColor=colors.HexColor('#718096')
            )
        ))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()


def is_available() -> bool:
    """Check if PDF generation is available."""
    return REPORTLAB_AVAILABLE
