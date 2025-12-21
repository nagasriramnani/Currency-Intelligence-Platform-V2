"""
EIS Newsletter Automation Module

This module transforms the EIS system from a manual tool to an automated newsletter.

Components:
- scanner.py: Detects SH01 filings (investment signals)
- writer.py: Generates narrative content
- mailer.py: Sends emails via Gmail SMTP
- run_newsletter.py: Orchestrates the full pipeline

Usage:
    # Run full pipeline
    python run_newsletter.py
    
    # Individual components
    python scanner.py --days 7
    python writer.py scan_results.json
    python mailer.py newsletter.json --test email@example.com
"""

from .scanner import EISScanner
from .writer import EISWriter
from .mailer import EISMailer

__all__ = ['EISScanner', 'EISWriter', 'EISMailer']
