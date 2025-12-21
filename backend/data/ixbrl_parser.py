"""
iXBRL Parser for UK Companies House Accounts

Parses inline XBRL (iXBRL) documents filed with Companies House to extract
actual financial values like turnover, assets, and employee counts.

iXBRL files are XHTML documents with embedded XBRL facts tagged using
specific namespaces (uk-core, uk-gaap, frs-101, frs-102, etc.)

Author: Sapphire Intelligence Platform
Version: 1.0
"""

import os
import re
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from xml.etree import ElementTree as ET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Companies House base URL for document downloads
CH_DOCUMENT_API = "https://document-api.company-information.service.gov.uk"
CH_FILING_API = "https://api.company-information.service.gov.uk"

# XBRL Namespaces commonly used in UK accounts
XBRL_NAMESPACES = {
    'ix': 'http://www.xbrl.org/2013/inlineXBRL',
    'ixt': 'http://www.xbrl.org/inlineXBRL/transformation/2015-02-26',
    'link': 'http://www.xbrl.org/2003/linkbase',
    'xbrli': 'http://www.xbrl.org/2003/instance',
    'xlink': 'http://www.w3.org/1999/xlink',
    'uk-core': 'http://xbrl.frc.org.uk/fr/2021-01-01/core',
    'uk-bus': 'http://xbrl.frc.org.uk/cd/2021-01-01/business',
    'uk-gaap': 'http://www.xbrl.org/uk/gaap/core/2009-09-01',
    'frs-101': 'http://xbrl.frc.org.uk/FRS-101/2021-01-01',
    'frs-102': 'http://xbrl.frc.org.uk/FRS-102/2021-01-01',
    'html': 'http://www.w3.org/1999/xhtml',
}

# Key financial fact names to extract (various taxonomies)
FINANCIAL_FACTS = {
    # Turnover / Revenue
    'turnover': [
        'TurnoverRevenue',
        'Turnover',
        'TurnoverGrossRevenue', 
        'Revenue',
        'NetSales',
        'TurnoverRevenueNet',
    ],
    # Total Assets
    'total_assets': [
        'TotalAssets',
        'TotalAssetsNet',
        'FixedAssetsTotalCurrentAssets',
        'AssetsTotalLessCurrentLiabilities',
    ],
    # Net Assets / Shareholders' Funds
    'net_assets': [
        'NetAssetsLiabilities',
        'NetAssets',
        'TotalNetAssets',
        'ShareholdersEquity',
        'EquityAndLiabilities',
        'TotalEquity',
        'NetAssetsLiabilitiesIncludingPensionAssetLiability',
    ],
    # Current Assets
    'current_assets': [
        'CurrentAssets',
        'TotalCurrentAssets',
        'CurrentAssetsTotal',
    ],
    # Fixed Assets
    'fixed_assets': [
        'FixedAssets',
        'TotalFixedAssets',
        'FixedAssetsTangibleIntangible',
        'IntangibleAssets',
        'TangibleFixedAssets',
        'InvestmentProperty',
    ],
    # Employees
    'employees': [
        'AverageNumberEmployeesDuringPeriod',
        'AverageNumberEmployees',
        'EmployeesTotal',
        'NumberEmployees',
        'AverageNumberOfPersonsEmployed',
        'AverageNumberOfEmployees',
    ],
    # Profit
    'profit': [
        'ProfitLoss',
        'ProfitLossForPeriod',
        'NetProfitLoss',
        'OperatingProfitLoss',
        'ProfitLossOnOrdinaryActivitiesBeforeTax',
        'ProfitLossBeforeTax',
    ],
    # Cash
    'cash': [
        'CashBankOnHand',
        'CashAtBankInHand',
        'CashAndCashEquivalents',
        'Cash',
    ],
    # Creditors
    'creditors': [
        'Creditors',
        'CreditorsAmountsFallingDueWithinOneYear',
        'TotalCreditors',
    ],
}


class IXBRLParser:
    """
    Parses iXBRL documents from Companies House to extract financial facts.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('COMPANIES_HOUSE_API_KEY', '')
    
    def get_accounts_document_url(self, company_number: str) -> Optional[str]:
        """
        Get the URL of the latest accounts document for a company.
        
        Returns the document API URL if available.
        """
        company_number = company_number.zfill(8)
        
        # Get filing history filtered to accounts
        url = f"{CH_FILING_API}/company/{company_number}/filing-history"
        params = {"category": "accounts", "items_per_page": 5}
        
        try:
            response = requests.get(
                url,
                params=params,
                auth=(self.api_key, ''),
                timeout=30
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to get filing history: {response.status_code}")
                return None
            
            data = response.json()
            items = data.get('items', [])
            
            # Find the latest accounts with a document link
            for item in items:
                if item.get('category') == 'accounts':
                    links = item.get('links', {})
                    if 'document_metadata' in links:
                        return links['document_metadata']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting accounts document URL: {e}")
            return None
    
    def download_ixbrl_content(self, document_metadata_url: str) -> Optional[str]:
        """
        Download the iXBRL content from Companies House.
        
        The document metadata endpoint returns available resources.
        We specifically request XHTML/iXBRL format - returns None if not available.
        """
        try:
            # First, get the document metadata to find available formats
            if not document_metadata_url.startswith('http'):
                document_metadata_url = f"{CH_FILING_API}{document_metadata_url}"
            
            # Get document metadata
            meta_response = requests.get(
                document_metadata_url,
                auth=(self.api_key, ''),
                timeout=30,
                headers={'Accept': 'application/json'}
            )
            
            if meta_response.status_code != 200:
                logger.warning(f"Failed to get document metadata: {meta_response.status_code}")
                return None
            
            meta_data = meta_response.json()
            
            # Check available resources for XHTML/iXBRL
            resources = meta_data.get('resources', {})
            has_xhtml = False
            xhtml_content_type = None
            
            for resource_type, resource_info in resources.items():
                content_type = resource_info.get('content_type', '') if isinstance(resource_info, dict) else ''
                if 'xhtml' in resource_type.lower() or 'xhtml' in content_type.lower():
                    has_xhtml = True
                    xhtml_content_type = 'application/xhtml+xml'
                    break
                if 'html' in resource_type.lower() or 'html' in content_type.lower():
                    has_xhtml = True
                    xhtml_content_type = 'text/html'
            
            if not has_xhtml:
                # Check if it's PDF only
                if any('pdf' in str(v).lower() for v in resources.values()):
                    logger.info("Document only available as PDF - iXBRL parsing not possible")
                    return None
                logger.info("No XHTML/iXBRL resource found in document metadata")
            
            # Get the document URL
            links = meta_data.get('links', {})
            document_url = links.get('document')
            
            if not document_url:
                logger.warning("No document URL found in metadata")
                return None
            
            if not document_url.startswith('http'):
                document_url = f"{CH_DOCUMENT_API}{document_url}"
            
            # Download the document, requesting XHTML format specifically
            doc_response = requests.get(
                document_url,
                auth=(self.api_key, ''),
                timeout=60,
                headers={
                    'Accept': 'application/xhtml+xml, text/html;q=0.9',
                }
            )
            
            if doc_response.status_code != 200:
                logger.warning(f"Failed to download document: {doc_response.status_code}")
                return None
            
            # Check what we actually received
            content_type = doc_response.headers.get('Content-Type', '').lower()
            
            # If we got PDF, we can't parse it
            if 'pdf' in content_type:
                logger.info(f"Received PDF response (Content-Type: {content_type}) - cannot parse")
                return None
            
            # If we got something that's not HTML/XHTML, skip
            if 'html' not in content_type and 'xhtml' not in content_type and 'xml' not in content_type:
                logger.info(f"Received non-HTML content (Content-Type: {content_type}) - cannot parse")
                return None
            
            content = doc_response.text
            
            # Quick sanity check - does it look like HTML/XML?
            if not content.strip().startswith('<') and '<!DOCTYPE' not in content[:500]:
                logger.warning("Content doesn't appear to be HTML/XML")
                return None
            
            return content
            
        except Exception as e:
            logger.error(f"Error downloading iXBRL content: {e}")
            return None
    
    def parse_ixbrl(self, content: str) -> Dict[str, Any]:
        """
        Parse iXBRL content to extract financial facts.
        
        iXBRL uses <ix:nonFraction> and <ix:nonNumeric> tags to embed
        XBRL facts within HTML content.
        """
        result = {
            'turnover': None,
            'total_assets': None,
            'net_assets': None,
            'current_assets': None,
            'fixed_assets': None,
            'employees': None,
            'profit': None,
            'cash': None,
            'creditors': None,
            'raw_facts': {},
            'period_end': None,
            'currency': 'GBP',
            'parse_success': False,
        }
        
        try:
            # Try to parse as XML first
            # Clean up the content for XML parsing
            content = self._clean_html_for_xml(content)
            
            # Register namespaces
            for prefix, uri in XBRL_NAMESPACES.items():
                ET.register_namespace(prefix, uri)
            
            root = ET.fromstring(content.encode('utf-8'))
            
            # Find all ix:nonFraction elements (numeric facts)
            numeric_facts = self._find_all_with_namespace(root, 'nonFraction', 'ix')
            numeric_facts.extend(self._find_all_with_namespace(root, 'nonfraction', 'ix'))
            
            # Find all ix:nonNumeric elements (text facts like dates)
            text_facts = self._find_all_with_namespace(root, 'nonNumeric', 'ix')
            text_facts.extend(self._find_all_with_namespace(root, 'nonnumeric', 'ix'))
            
            # Extract numeric values
            for fact in numeric_facts:
                name = fact.get('name', '')
                value = self._extract_numeric_value(fact)
                
                if name and value is not None:
                    # Store raw fact
                    result['raw_facts'][name] = value
                    
                    # Match to known financial fields
                    for field, patterns in FINANCIAL_FACTS.items():
                        for pattern in patterns:
                            if pattern.lower() in name.lower():
                                if result[field] is None or abs(value) > abs(result[field] or 0):
                                    result[field] = value
                                break
            
            result['parse_success'] = True
            logger.info(f"Parsed iXBRL: found {len(result['raw_facts'])} facts")
            
        except ET.ParseError as e:
            logger.warning(f"XML parse error, trying regex fallback: {e}")
            result = self._parse_with_regex(content, result)
        except Exception as e:
            logger.error(f"Error parsing iXBRL: {e}")
            result = self._parse_with_regex(content, result)
        
        return result
    
    def _clean_html_for_xml(self, content: str) -> str:
        """Clean HTML content to make it parseable as XML."""
        # Remove DOCTYPE
        content = re.sub(r'<!DOCTYPE[^>]*>', '', content, flags=re.IGNORECASE)
        # Remove HTML comments
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        # Self-close common void elements
        for tag in ['br', 'hr', 'img', 'input', 'meta', 'link']:
            content = re.sub(rf'<{tag}([^>]*)(?<!/)>', rf'<{tag}\1/>', content, flags=re.IGNORECASE)
        return content
    
    def _find_all_with_namespace(self, root: ET.Element, tag: str, prefix: str) -> List[ET.Element]:
        """Find all elements with a specific namespace prefix."""
        elements = []
        ns_uri = XBRL_NAMESPACES.get(prefix, '')
        
        # Try with namespace
        for elem in root.iter(f'{{{ns_uri}}}{tag}'):
            elements.append(elem)
        
        # Also try without namespace (some documents use prefixes differently)
        for elem in root.iter():
            if elem.tag.endswith(tag) or elem.tag.endswith(f':{tag}'):
                elements.append(elem)
        
        return elements
    
    def _extract_numeric_value(self, element: ET.Element) -> Optional[float]:
        """Extract numeric value from an iXBRL element."""
        try:
            # Get the text content
            text = element.text or ''
            text = text.strip()
            
            # Check for scale attribute
            scale = element.get('scale', '0')
            sign = element.get('sign', '')
            
            # Remove currency symbols and commas
            text = re.sub(r'[£$€,\s]', '', text)
            
            # Handle brackets for negative
            if '(' in text and ')' in text:
                text = text.replace('(', '-').replace(')', '')
            
            if not text or text == '-':
                return None
            
            value = float(text)
            
            # Apply scale (e.g., scale="3" means thousands)
            if scale:
                value = value * (10 ** int(scale))
            
            # Apply sign
            if sign == '-':
                value = -value
            
            return value
            
        except (ValueError, TypeError):
            return None
    
    def _parse_with_regex(self, content: str, result: Dict) -> Dict:
        """Fallback regex parsing for when XML parsing fails."""
        logger.info("Using regex fallback for iXBRL parsing")
        
        # Pattern for ix:nonFraction elements
        pattern = r'<ix:nonFraction[^>]*name="([^"]*)"[^>]*>([^<]*)</ix:nonFraction>'
        matches = re.findall(pattern, content, re.IGNORECASE)
        
        for name, value in matches:
            # Clean and convert value
            value = re.sub(r'[£$€,\s]', '', value)
            try:
                num_value = float(value)
                result['raw_facts'][name] = num_value
                
                # Match to known fields
                for field, patterns in FINANCIAL_FACTS.items():
                    for pattern in patterns:
                        if pattern.lower() in name.lower():
                            if result[field] is None:
                                result[field] = num_value
                            break
            except ValueError:
                pass
        
        result['parse_success'] = len(result['raw_facts']) > 0
        return result
    
    def get_financial_data(self, company_number: str) -> Dict[str, Any]:
        """
        Main method: Get parsed financial data for a company.
        
        Returns dict with actual financial values extracted from iXBRL accounts.
        """
        company_number = company_number.zfill(8)
        
        result = {
            'company_number': company_number,
            'data_available': False,
            'turnover': None,
            'total_assets': None,
            'net_assets': None,
            'current_assets': None,
            'fixed_assets': None,
            'employees': None,
            'profit': None,
            'cash': None,
            'accounts_date': None,
            'currency': 'GBP',
            'source': 'ixbrl_parsing',
            'parse_success': False,
            'notes': [],
        }
        
        try:
            # Step 1: Get document URL
            logger.info(f"Getting accounts document URL for {company_number}")
            doc_url = self.get_accounts_document_url(company_number)
            
            if not doc_url:
                result['notes'].append("No accounts document URL found")
                return result
            
            # Step 2: Download iXBRL content
            logger.info(f"Downloading iXBRL content from {doc_url}")
            content = self.download_ixbrl_content(doc_url)
            
            if not content:
                result['notes'].append("Failed to download accounts document")
                return result
            
            # Step 3: Parse iXBRL
            logger.info("Parsing iXBRL content")
            parsed = self.parse_ixbrl(content)
            
            # Copy parsed values to result
            result['turnover'] = parsed.get('turnover')
            result['total_assets'] = parsed.get('total_assets')
            result['net_assets'] = parsed.get('net_assets')
            result['current_assets'] = parsed.get('current_assets')
            result['fixed_assets'] = parsed.get('fixed_assets')
            result['employees'] = parsed.get('employees')
            result['profit'] = parsed.get('profit')
            result['cash'] = parsed.get('cash')
            result['parse_success'] = parsed.get('parse_success', False)
            result['data_available'] = parsed.get('parse_success', False)
            
            # Add EIS eligibility checks
            result['eis_checks'] = {
                'assets_eligible': None,
                'employees_eligible': None,
            }
            
            if result['total_assets'] is not None:
                result['eis_checks']['assets_eligible'] = result['total_assets'] < 15_000_000
            elif result['net_assets'] is not None:
                result['eis_checks']['assets_eligible'] = result['net_assets'] < 15_000_000
            
            if result['employees'] is not None:
                result['eis_checks']['employees_eligible'] = result['employees'] < 250
            
            if result['parse_success']:
                result['notes'].append(f"Extracted {len(parsed.get('raw_facts', {}))} financial facts from iXBRL")
            else:
                result['notes'].append("iXBRL parsing returned no data")
            
        except Exception as e:
            logger.error(f"Error getting financial data: {e}")
            result['notes'].append(f"Error: {str(e)}")
        
        return result


def format_currency(value: Optional[float], currency: str = 'GBP') -> str:
    """Format a currency value for display."""
    if value is None:
        return 'N/A'
    
    symbol = '£' if currency == 'GBP' else '$' if currency == 'USD' else '€'
    
    if abs(value) >= 1_000_000:
        return f"{symbol}{value/1_000_000:.1f}m"
    elif abs(value) >= 1_000:
        return f"{symbol}{value/1_000:.0f}k"
    else:
        return f"{symbol}{value:.0f}"


# CLI for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ixbrl_parser.py <company_number>")
        sys.exit(1)
    
    company_number = sys.argv[1]
    parser = IXBRLParser()
    
    print(f"\nFetching financial data for {company_number}...")
    data = parser.get_financial_data(company_number)
    
    print(f"\n{'='*50}")
    print(f"Company: {data['company_number']}")
    print(f"Parse Success: {data['parse_success']}")
    print(f"{'='*50}")
    
    print(f"\nFinancial Data:")
    print(f"  Turnover:      {format_currency(data['turnover'])}")
    print(f"  Total Assets:  {format_currency(data['total_assets'])}")
    print(f"  Net Assets:    {format_currency(data['net_assets'])}")
    print(f"  Current Assets: {format_currency(data['current_assets'])}")
    print(f"  Fixed Assets:  {format_currency(data['fixed_assets'])}")
    print(f"  Employees:     {data['employees'] or 'N/A'}")
    print(f"  Profit:        {format_currency(data['profit'])}")
    print(f"  Cash:          {format_currency(data['cash'])}")
    
    print(f"\nEIS Eligibility:")
    checks = data.get('eis_checks', {})
    print(f"  Assets < £15m: {checks.get('assets_eligible')}")
    print(f"  Employees < 250: {checks.get('employees_eligible')}")
    
    print(f"\nNotes: {data['notes']}")
