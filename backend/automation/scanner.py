"""
EIS Newsletter Scanner

Automatically scans Companies House for companies that filed SH01 (Statement of Capital)
in the last 24 hours. SH01 filings indicate a company has issued new shares, which is
a strong signal of investment activity and potential EIS eligibility.

This script transforms the system from a "Human Analyst Tool" to an "Automated Newsletter."

Usage:
    python scanner.py                    # Scan last 24 hours
    python scanner.py --days 7           # Scan last 7 days
    python scanner.py --output results   # Custom output directory

Author: Sapphire Intelligence Platform
Version: 1.0 (Stage 1 MVP)
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.companies_house import CompaniesHouseClient
from analytics.eis_heuristics import calculate_eis_likelihood

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SH01_FILING_TYPES = [
    "SH01",  # Statement of capital
    "SH02",  # Return of allotment of shares
    "SH03",  # Return of purchase of own shares
]

CAPITAL_CATEGORY = "capital"


class EISScanner:
    """
    Scans Companies House for investment signals (SH01 filings)
    and filters for EIS-likely companies.
    """
    
    def __init__(self, output_dir: str = "scans"):
        self.client = CompaniesHouseClient()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def get_recent_capital_filings(self, days: int = 1, limit: int = 100) -> List[Dict]:
        """
        Search for companies with recent capital-related filings.
        
        SH01 filings indicate share allotments (new investment).
        This is the primary signal for EIS-relevant companies.
        """
        logger.info(f"Scanning for SH01 filings in the last {days} day(s)...")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Companies House advanced search API allows filtering by filing date
        # However, the free API doesn't support date-range searches directly
        # So we use an alternative approach: search for common company types
        # and then filter by their filing history
        
        # Strategy: Search for recently active companies and check their filings
        # This is a workaround for the limited free API capabilities
        
        candidates = []
        
        # Search for recently incorporated companies (high EIS likelihood)
        search_terms = [
            "technology",
            "software",
            "digital",
            "fintech",
            "biotech",
            "health tech",
            "AI",
            "platform",
            "innovations",
            "solutions",
        ]
        
        seen_companies = set()
        
        for term in search_terms:
            try:
                results = self.client.search_companies(term, items_per_page=20)
                for company in results:
                    company_number = company.get('company_number')
                    if company_number and company_number not in seen_companies:
                        seen_companies.add(company_number)
                        
                        # Check for recent SH01 filings
                        if self._has_recent_sh01(company_number, days):
                            candidates.append(company)
                            logger.info(f"Found SH01 signal: {company.get('title', 'Unknown')}")
                            
                            if len(candidates) >= limit:
                                break
                                
            except Exception as e:
                logger.warning(f"Error searching for '{term}': {e}")
                continue
                
            if len(candidates) >= limit:
                break
        
        logger.info(f"Found {len(candidates)} companies with recent SH01 filings")
        return candidates
    
    def _has_recent_sh01(self, company_number: str, days: int) -> bool:
        """Check if a company has filed SH01 in the given time period."""
        try:
            filings = self.client.get_filing_history(company_number, items_per_page=10)
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for filing in filings:
                # Check if it's a capital-related filing
                category = filing.get('category', '').lower()
                filing_type = filing.get('type', '').upper()
                
                if category == CAPITAL_CATEGORY or filing_type in SH01_FILING_TYPES:
                    # Check the date
                    date_str = filing.get('date', '')
                    if date_str:
                        try:
                            filing_date = datetime.strptime(date_str, '%Y-%m-%d')
                            if filing_date >= cutoff_date:
                                return True
                        except ValueError:
                            continue
                            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking filings for {company_number}: {e}")
            return False
    
    def enrich_with_eis_assessment(self, companies: List[Dict]) -> List[Dict]:
        """
        For each company, fetch full profile and calculate EIS likelihood.
        """
        enriched = []
        
        for i, company in enumerate(companies):
            company_number = company.get('company_number')
            company_name = company.get('title', 'Unknown')
            
            logger.info(f"Enriching {i+1}/{len(companies)}: {company_name}")
            
            try:
                # Get full profile
                full_profile = self.client.get_full_profile(company_number)
                
                if full_profile:
                    # Calculate EIS likelihood
                    eis_assessment = calculate_eis_likelihood(full_profile)
                    
                    enriched.append({
                        'company_number': company_number,
                        'company_name': company_name,
                        'search_result': company,
                        'full_profile': full_profile,
                        'eis_assessment': eis_assessment,
                        'scanned_at': datetime.now().isoformat()
                    })
                    
            except Exception as e:
                logger.warning(f"Error enriching {company_name}: {e}")
                continue
        
        return enriched
    
    def filter_likely_eligible(self, companies: List[Dict], min_score: int = 50) -> List[Dict]:
        """Filter to only companies with EIS score above threshold."""
        eligible = []
        
        for company in companies:
            score = company.get('eis_assessment', {}).get('score', 0)
            if score >= min_score:
                eligible.append(company)
        
        # Sort by score descending
        eligible.sort(key=lambda x: x.get('eis_assessment', {}).get('score', 0), reverse=True)
        
        return eligible
    
    def save_results(self, companies: List[Dict], filename: str = None) -> str:
        """Save scan results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"eis_scan_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        results = {
            'scan_timestamp': datetime.now().isoformat(),
            'total_found': len(companies),
            'companies': companies
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results saved to {output_path}")
        return str(output_path)
    
    def run_scan(self, days: int = 1, min_score: int = 50, limit: int = 50) -> Dict[str, Any]:
        """
        Run complete scan pipeline:
        1. Find companies with recent SH01 filings
        2. Enrich with full profile and EIS assessment
        3. Filter to likely eligible
        4. Save results
        """
        logger.info("=" * 60)
        logger.info("EIS NEWSLETTER SCANNER")
        logger.info(f"Scanning for SH01 filings in the last {days} day(s)")
        logger.info(f"Minimum EIS score: {min_score}")
        logger.info("=" * 60)
        
        # Step 1: Find companies with SH01 filings
        candidates = self.get_recent_capital_filings(days=days, limit=limit)
        
        if not candidates:
            logger.info("No companies found with recent SH01 filings")
            return {'found': 0, 'eligible': 0, 'companies': []}
        
        # Step 2: Enrich with EIS assessment
        enriched = self.enrich_with_eis_assessment(candidates)
        
        # Step 3: Filter to likely eligible
        eligible = self.filter_likely_eligible(enriched, min_score=min_score)
        
        # Step 4: Save results
        output_path = self.save_results(eligible)
        
        # Summary
        summary = {
            'scan_timestamp': datetime.now().isoformat(),
            'days_scanned': days,
            'min_score': min_score,
            'total_candidates': len(candidates),
            'enriched': len(enriched),
            'likely_eligible': len(eligible),
            'output_file': output_path,
            'companies': eligible
        }
        
        logger.info("=" * 60)
        logger.info("SCAN COMPLETE")
        logger.info(f"Candidates found: {len(candidates)}")
        logger.info(f"Enriched with EIS assessment: {len(enriched)}")
        logger.info(f"Likely eligible (score >= {min_score}): {len(eligible)}")
        logger.info(f"Results saved to: {output_path}")
        logger.info("=" * 60)
        
        return summary


def main():
    """Command-line interface for the scanner."""
    parser = argparse.ArgumentParser(
        description='Scan Companies House for EIS-eligible companies with recent investment activity'
    )
    parser.add_argument(
        '--days', type=int, default=7,
        help='Number of days to look back for SH01 filings (default: 7)'
    )
    parser.add_argument(
        '--min-score', type=int, default=50,
        help='Minimum EIS score to include (default: 50)'
    )
    parser.add_argument(
        '--limit', type=int, default=50,
        help='Maximum number of companies to scan (default: 50)'
    )
    parser.add_argument(
        '--output', type=str, default='scans',
        help='Output directory for results (default: scans)'
    )
    
    args = parser.parse_args()
    
    scanner = EISScanner(output_dir=args.output)
    results = scanner.run_scan(
        days=args.days,
        min_score=args.min_score,
        limit=args.limit
    )
    
    # Print top companies
    if results.get('companies'):
        print("\n🎯 TOP EIS-LIKELY COMPANIES:")
        print("-" * 60)
        for i, company in enumerate(results['companies'][:10], 1):
            name = company.get('company_name', 'Unknown')
            score = company.get('eis_assessment', {}).get('score', 0)
            status = company.get('eis_assessment', {}).get('status', 'Unknown')
            print(f"{i}. {name}")
            print(f"   Score: {score}/100 | Status: {status}")
        print()
    
    return results


if __name__ == "__main__":
    main()
