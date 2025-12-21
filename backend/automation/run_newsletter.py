"""
EIS Newsletter Pipeline Orchestrator

Runs the complete newsletter pipeline:
1. Scanner - Find companies with SH01 filings
2. Writer - Generate narrative content
3. Mailer - Send to subscribers

This transforms the system from a manual tool to an automated newsletter.

Usage:
    python run_newsletter.py                # Run full pipeline
    python run_newsletter.py --scan-only    # Only scan, don't send
    python run_newsletter.py --days 7       # Look back 7 days
    python run_newsletter.py --dry-run      # Preview without sending

For scheduled execution, use GitHub Actions or Windows Task Scheduler.

Author: Sapphire Intelligence Platform
Version: 1.0 (Stage 1 MVP)
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from automation.scanner import EISScanner
from automation.writer import EISWriter
from automation.mailer import EISMailer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent / 'newsletter.log')
    ]
)
logger = logging.getLogger(__name__)


def run_pipeline(
    days: int = 7,
    min_score: int = 50,
    limit: int = 30,
    use_ai: bool = False,
    dry_run: bool = False,
    scan_only: bool = False,
    output_dir: str = "output"
) -> Dict[str, Any]:
    """
    Run the complete EIS newsletter pipeline.
    
    Args:
        days: Number of days to look back for SH01 filings
        min_score: Minimum EIS score to include
        limit: Maximum companies to scan
        use_ai: Use AI for narrative generation
        dry_run: Preview mode, don't actually send emails
        scan_only: Only run scanner, skip writer and mailer
        output_dir: Directory for output files
    
    Returns:
        Pipeline execution results
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    results = {
        'timestamp': timestamp,
        'status': 'starting',
        'phases': {}
    }
    
    try:
        # =====================================================================
        # PHASE 1: SCANNER
        # =====================================================================
        logger.info("=" * 70)
        logger.info("PHASE 1: SCANNING FOR EIS-ELIGIBLE COMPANIES")
        logger.info("=" * 70)
        
        scanner = EISScanner(output_dir=str(output_path / "scans"))
        scan_results = scanner.run_scan(
            days=days,
            min_score=min_score,
            limit=limit
        )
        
        results['phases']['scanner'] = {
            'status': 'success',
            'candidates': scan_results.get('total_candidates', 0),
            'eligible': scan_results.get('likely_eligible', 0),
            'output_file': scan_results.get('output_file')
        }
        
        companies = scan_results.get('companies', [])
        
        if not companies:
            logger.warning("No eligible companies found. Pipeline stopping.")
            results['status'] = 'completed_no_results'
            return results
        
        if scan_only:
            logger.info("Scan-only mode. Stopping after scanner.")
            results['status'] = 'completed_scan_only'
            return results
        
        # =====================================================================
        # PHASE 2: WRITER
        # =====================================================================
        logger.info("=" * 70)
        logger.info("PHASE 2: GENERATING NEWSLETTER CONTENT")
        logger.info("=" * 70)
        
        writer = EISWriter(use_ai=use_ai)
        newsletter = writer.generate_newsletter_content(companies)
        
        # Save newsletter
        newsletter_file = output_path / f"newsletter_{timestamp}.json"
        writer.save_newsletter(newsletter, str(newsletter_file))
        
        results['phases']['writer'] = {
            'status': 'success',
            'companies': len(newsletter.get('deal_highlights', [])),
            'output_file': str(newsletter_file)
        }
        
        # =====================================================================
        # PHASE 3: MAILER
        # =====================================================================
        logger.info("=" * 70)
        logger.info("PHASE 3: SENDING NEWSLETTER")
        logger.info("=" * 70)
        
        mailer = EISMailer()
        subscribers = mailer.load_subscribers()
        
        if not subscribers:
            logger.warning("No subscribers configured. Add subscribers with:")
            logger.warning("  python mailer.py --add-subscriber email@example.com")
            results['phases']['mailer'] = {
                'status': 'skipped',
                'reason': 'no_subscribers'
            }
        else:
            send_results = mailer.send_newsletter(
                newsletter,
                test_mode=dry_run
            )
            
            results['phases']['mailer'] = {
                'status': 'success' if not dry_run else 'dry_run',
                'sent': send_results.get('sent', 0),
                'failed': send_results.get('failed', 0)
            }
        
        results['status'] = 'completed'
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        results['status'] = 'failed'
        results['error'] = str(e)
    
    # Save pipeline results
    results_file = output_path / f"pipeline_results_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print_summary(results)
    
    return results


def print_summary(results: Dict):
    """Print execution summary."""
    print("\n" + "=" * 70)
    print("📊 EIS NEWSLETTER PIPELINE SUMMARY")
    print("=" * 70)
    print(f"Timestamp: {results.get('timestamp')}")
    print(f"Status: {results.get('status')}")
    print()
    
    phases = results.get('phases', {})
    
    if 'scanner' in phases:
        scanner = phases['scanner']
        print(f"📡 Scanner: {scanner.get('status')}")
        print(f"   Candidates found: {scanner.get('candidates', 0)}")
        print(f"   Likely eligible: {scanner.get('eligible', 0)}")
    
    if 'writer' in phases:
        writer = phases['writer']
        print(f"✍️  Writer: {writer.get('status')}")
        print(f"   Deal highlights: {writer.get('companies', 0)}")
    
    if 'mailer' in phases:
        mailer = phases['mailer']
        print(f"📧 Mailer: {mailer.get('status')}")
        if mailer.get('sent'):
            print(f"   Sent: {mailer.get('sent', 0)}")
            print(f"   Failed: {mailer.get('failed', 0)}")
    
    print("=" * 70)


def main():
    """Command-line interface for the pipeline."""
    parser = argparse.ArgumentParser(
        description='Run the complete EIS Newsletter pipeline'
    )
    parser.add_argument(
        '--days', type=int, default=7,
        help='Days to look back for SH01 filings (default: 7)'
    )
    parser.add_argument(
        '--min-score', type=int, default=50,
        help='Minimum EIS score to include (default: 50)'
    )
    parser.add_argument(
        '--limit', type=int, default=30,
        help='Maximum companies to scan (default: 30)'
    )
    parser.add_argument(
        '--ai', action='store_true',
        help='Use AI for narrative generation (requires HUGGINGFACE_API_KEY)'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Preview mode - do not actually send emails'
    )
    parser.add_argument(
        '--scan-only', action='store_true',
        help='Only run scanner, skip writer and mailer'
    )
    parser.add_argument(
        '--output', type=str, default='output',
        help='Output directory (default: output)'
    )
    
    args = parser.parse_args()
    
    results = run_pipeline(
        days=args.days,
        min_score=args.min_score,
        limit=args.limit,
        use_ai=args.ai,
        dry_run=args.dry_run,
        scan_only=args.scan_only,
        output_dir=args.output
    )
    
    # Exit with appropriate code
    if results.get('status') == 'failed':
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
