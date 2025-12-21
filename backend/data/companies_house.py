"""
Companies House API Client

Provides access to UK Companies House data for EIS company monitoring.
API Documentation: https://developer.company-information.service.gov.uk/
"""

import os
import logging
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# API Configuration
COMPANIES_HOUSE_API_KEY = os.getenv("COMPANIES_HOUSE_API_KEY", "")
BASE_URL = "https://api.company-information.service.gov.uk"


@dataclass
class CompanyProfile:
    """Represents a company profile from Companies House."""
    company_number: str
    company_name: str
    company_status: str
    company_type: str
    date_of_creation: Optional[str]
    jurisdiction: str
    registered_office_address: Dict[str, str]
    sic_codes: List[str]
    has_charges: bool
    has_insolvency_history: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "company_number": self.company_number,
            "company_name": self.company_name,
            "company_status": self.company_status,
            "company_type": self.company_type,
            "date_of_creation": self.date_of_creation,
            "jurisdiction": self.jurisdiction,
            "registered_office_address": self.registered_office_address,
            "sic_codes": self.sic_codes,
            "has_charges": self.has_charges,
            "has_insolvency_history": self.has_insolvency_history
        }


@dataclass
class CompanyOfficer:
    """Represents a company officer (director, secretary, etc.)."""
    name: str
    officer_role: str
    appointed_on: Optional[str]
    nationality: Optional[str]
    occupation: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "officer_role": self.officer_role,
            "appointed_on": self.appointed_on,
            "nationality": self.nationality,
            "occupation": self.occupation
        }


class CompaniesHouseClient:
    """
    Client for Companies House API.
    
    Usage:
        client = CompaniesHouseClient()
        company = client.get_company("00000006")
        officers = client.get_officers("00000006")
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or COMPANIES_HOUSE_API_KEY
        if not self.api_key:
            logger.warning("Companies House API key not configured")
        self.session = requests.Session()
        # Companies House uses Basic Auth with API key as username, no password
        self.session.auth = (self.api_key, "")
        self.session.headers.update({
            "Accept": "application/json"
        })
    
    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated request to Companies House API."""
        if not self.is_configured():
            logger.error("API key not configured")
            return None
        
        url = f"{BASE_URL}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Resource not found: {endpoint}")
                return None
            elif response.status_code == 401:
                logger.error("Authentication failed - check API key")
                return None
            elif response.status_code == 429:
                logger.warning("Rate limit exceeded")
                return None
            else:
                logger.error(f"API error {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
    
    def get_company(self, company_number: str) -> Optional[CompanyProfile]:
        """
        Get company profile by company number.
        
        Args:
            company_number: 8-character company number (e.g., "00000006")
            
        Returns:
            CompanyProfile or None if not found
        """
        # Pad company number to 8 characters
        company_number = company_number.zfill(8)
        
        data = self._make_request(f"/company/{company_number}")
        if not data:
            return None
        
        return CompanyProfile(
            company_number=data.get("company_number", ""),
            company_name=data.get("company_name", ""),
            company_status=data.get("company_status", ""),
            company_type=data.get("type", ""),
            date_of_creation=data.get("date_of_creation"),
            jurisdiction=data.get("jurisdiction", ""),
            registered_office_address=data.get("registered_office_address", {}),
            sic_codes=data.get("sic_codes", []),
            has_charges=data.get("has_charges", False),
            has_insolvency_history=data.get("has_insolvency_history", False)
        )
    
    def get_officers(self, company_number: str, active_only: bool = True) -> List[CompanyOfficer]:
        """
        Get list of company officers.
        
        Args:
            company_number: 8-character company number
            active_only: If True, only return current officers
            
        Returns:
            List of CompanyOfficer objects
        """
        company_number = company_number.zfill(8)
        
        params = {}
        if active_only:
            params["register_view"] = "true"
        
        data = self._make_request(f"/company/{company_number}/officers", params)
        if not data:
            return []
        
        officers = []
        for item in data.get("items", []):
            # Skip resigned officers if active_only
            if active_only and item.get("resigned_on"):
                continue
                
            officers.append(CompanyOfficer(
                name=item.get("name", ""),
                officer_role=item.get("officer_role", ""),
                appointed_on=item.get("appointed_on"),
                nationality=item.get("nationality"),
                occupation=item.get("occupation")
            ))
        
        return officers
    
    def search_companies(self, query: str, items_per_page: int = 20) -> List[Dict[str, Any]]:
        """
        Search for companies by name or number.
        
        Args:
            query: Search term
            items_per_page: Number of results (max 100)
            
        Returns:
            List of company search results
        """
        params = {
            "q": query,
            "items_per_page": min(items_per_page, 100)
        }
        
        data = self._make_request("/search/companies", params)
        if not data:
            return []
        
        return data.get("items", [])
    
    def get_filing_history(self, company_number: str, items_per_page: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent filing history for a company.
        
        Args:
            company_number: 8-character company number
            items_per_page: Number of filings to return
            
        Returns:
            List of filing history items
        """
        company_number = company_number.zfill(8)
        
        params = {"items_per_page": min(items_per_page, 100)}
        
        data = self._make_request(f"/company/{company_number}/filing-history", params)
        if not data:
            return []
        
        return data.get("items", [])
    
    def get_company_with_details(self, company_number: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive company information including officers and filings.
        
        Returns combined data for EIS newsletter display.
        Gracefully handles cases where officers data is unavailable.
        """
        try:
            company = self.get_company(company_number)
            if not company:
                return None
            
            # Officers endpoint can fail - handle gracefully
            try:
                officers = self.get_officers(company_number, active_only=False)
            except Exception as e:
                logger.warning(f"Failed to get officers for {company_number}: {e}")
                officers = []
            
            # Filings endpoint can fail - handle gracefully  
            try:
                filings = self.get_filing_history(company_number, items_per_page=5)
            except Exception as e:
                logger.warning(f"Failed to get filings for {company_number}: {e}")
                filings = []
            
            # Get directors only
            directors = [o for o in officers if "director" in o.officer_role.lower()]
            
            return {
                "company": company.to_dict(),
                "directors": [d.to_dict() for d in directors],
                "recent_filings": filings[:5] if filings else [],
                "director_count": len(directors),
                "total_officers": len(officers)
            }
        except Exception as e:
            logger.error(f"Failed to get company details for {company_number}: {e}")
            return None
    
    def search_by_sector(self, sector_keyword: str, items_per_page: int = 20) -> List[Dict[str, Any]]:
        """
        Search for companies by sector/industry keyword.
        
        Args:
            sector_keyword: Industry keyword like 'technology', 'fintech', 'healthcare'
            items_per_page: Number of results
            
        Returns:
            List of company search results
        """
        return self.search_companies(sector_keyword, items_per_page)
    
    def get_pscs(self, company_number: str) -> List[Dict[str, Any]]:
        """
        Get Persons with Significant Control (PSCs) - shareholders with 25%+ ownership.
        
        Args:
            company_number: 8-character company number
            
        Returns:
            List of PSC records with ownership details
        """
        company_number = company_number.zfill(8)
        
        data = self._make_request(f"/company/{company_number}/persons-with-significant-control")
        if not data:
            return []
        
        items = data.get("items", [])
        
        # Parse into cleaner format
        pscs = []
        for item in items:
            psc = {
                "name": item.get("name", item.get("name_elements", {}).get("forename", "Unknown")),
                "kind": item.get("kind", "unknown"),
                "natures_of_control": item.get("natures_of_control", []),
                "notified_on": item.get("notified_on"),
                "ceased_on": item.get("ceased_on"),
                "nationality": item.get("nationality"),
                "country_of_residence": item.get("country_of_residence"),
                "is_active": item.get("ceased_on") is None
            }
            
            # Parse ownership thresholds
            control = item.get("natures_of_control", [])
            if any("75-to-100" in c for c in control):
                psc["ownership_level"] = "75-100%"
            elif any("50-to-75" in c for c in control):
                psc["ownership_level"] = "50-75%"
            elif any("25-to-50" in c for c in control):
                psc["ownership_level"] = "25-50%"
            else:
                psc["ownership_level"] = "Unknown"
            
            pscs.append(psc)
        
        return pscs
    
    def get_charges(self, company_number: str) -> List[Dict[str, Any]]:
        """
        Get charges (mortgages, security interests) registered against the company.
        
        Args:
            company_number: 8-character company number
            
        Returns:
            List of charge records
        """
        company_number = company_number.zfill(8)
        
        data = self._make_request(f"/company/{company_number}/charges")
        if not data:
            return []
        
        items = data.get("items", [])
        
        charges = []
        for item in items:
            charge = {
                "charge_code": item.get("charge_code"),
                "status": item.get("status", "unknown"),
                "created_on": item.get("created_on"),
                "delivered_on": item.get("delivered_on"),
                "satisfied_on": item.get("satisfied_on"),
                "description": item.get("particulars", {}).get("description", ""),
                "persons_entitled": [p.get("name", "") for p in item.get("persons_entitled", [])],
                "is_outstanding": item.get("status") in ["outstanding", "part-satisfied"]
            }
            charges.append(charge)
        
        return charges
    
    def get_filing_history_enhanced(self, company_number: str, items_per_page: int = 25) -> Dict[str, Any]:
        """
        Get enhanced filing history with analysis for EIS indicators.
        
        Returns filing history plus analysis of filing patterns.
        """
        company_number = company_number.zfill(8)
        
        params = {"items_per_page": min(items_per_page, 100)}
        data = self._make_request(f"/company/{company_number}/filing-history", params)
        
        if not data:
            return {"items": [], "analysis": {}}
        
        items = data.get("items", [])
        
        # Analyze filings for EIS indicators
        analysis = {
            "total_filings": data.get("total_count", len(items)),
            "has_share_allotments": False,
            "share_allotment_count": 0,
            "has_annual_accounts": False,
            "accounts_type": None,
            "last_accounts_date": None,
            "last_confirmation_statement": None,
            "has_charges_filings": False,
            "filing_types": {}
        }
        
        for item in items:
            filing_type = item.get("type", "unknown")
            category = item.get("category", "unknown")
            description = item.get("description", "")
            
            # Count filing types
            analysis["filing_types"][filing_type] = analysis["filing_types"].get(filing_type, 0) + 1
            
            # Check for share allotments (SH01 - indicates investment)
            if filing_type == "SH01" or "allotment" in description.lower():
                analysis["has_share_allotments"] = True
                analysis["share_allotment_count"] += 1
            
            # Check for accounts
            if category == "accounts":
                if not analysis["has_annual_accounts"]:
                    analysis["has_annual_accounts"] = True
                    analysis["last_accounts_date"] = item.get("date")
                    # Try to determine accounts type
                    if "micro" in description.lower():
                        analysis["accounts_type"] = "micro-entity"
                    elif "small" in description.lower():
                        analysis["accounts_type"] = "small"
                    elif "dormant" in description.lower():
                        analysis["accounts_type"] = "dormant"
                    elif "abbreviated" in description.lower():
                        analysis["accounts_type"] = "abbreviated"
                    elif "full" in description.lower():
                        analysis["accounts_type"] = "full"
                    else:
                        analysis["accounts_type"] = "unknown"
            
            # Check for confirmation statements
            if filing_type == "CS01" or "confirmation" in description.lower():
                if not analysis["last_confirmation_statement"]:
                    analysis["last_confirmation_statement"] = item.get("date")
            
            # Check for charges
            if "charge" in category or "mortgage" in category:
                analysis["has_charges_filings"] = True
        
        # Parse items for cleaner output
        parsed_items = []
        for item in items[:25]:
            parsed_items.append({
                "date": item.get("date"),
                "type": item.get("type"),
                "category": item.get("category"),
                "description": item.get("description"),
                "action_date": item.get("action_date"),
                "links": item.get("links", {})
            })
        
        return {
            "items": parsed_items,
            "analysis": analysis
        }
    
    def get_accounts_data(self, company_number: str) -> Dict[str, Any]:
        """
        Get financial accounts data for a company.
        
        Fetches the latest accounts filing and extracts key financial metrics
        for EIS eligibility assessment:
        - Gross assets (must be < £15m for EIS)
        - Net assets
        - Employee count (must be < 250 for EIS, < 500 for KIC)
        - Turnover (helps determine KIC status)
        
        Note: Not all companies file detailed accounts. Micro-entity and 
        small company exemptions mean some data may not be available.
        
        Returns:
            Dict with financial data and data availability flags
        """
        company_number = company_number.zfill(8)
        
        result = {
            "company_number": company_number,
            "data_available": False,
            "gross_assets": None,
            "net_assets": None,
            "current_assets": None,
            "fixed_assets": None,
            "employees": None,
            "turnover": None,
            "accounts_date": None,
            "accounts_type": None,
            "eis_checks": {
                "assets_eligible": None,  # < £15m
                "employees_eligible": None,  # < 250
                "employees_kic_eligible": None,  # < 500
            },
            "source": "companies_house_accounts",
            "notes": []
        }
        
        try:
            # First get filing history to find latest accounts
            filings_data = self._make_request(
                f"/company/{company_number}/filing-history",
                {"category": "accounts", "items_per_page": 5}
            )
            
            if not filings_data or not filings_data.get("items"):
                result["notes"].append("No accounts filings found")
                return result
            
            # Find the latest accounts filing
            accounts_items = filings_data.get("items", [])
            latest_accounts = None
            
            for item in accounts_items:
                if item.get("category") == "accounts":
                    latest_accounts = item
                    break
            
            if not latest_accounts:
                result["notes"].append("No accounts found in recent filings")
                return result
            
            result["accounts_date"] = latest_accounts.get("date")
            description = latest_accounts.get("description", "").lower()
            
            # Determine accounts type
            if "micro" in description:
                result["accounts_type"] = "micro-entity"
                result["notes"].append("Micro-entity accounts - limited data available")
            elif "small" in description:
                result["accounts_type"] = "small"
                result["notes"].append("Small company accounts - abbreviated data")
            elif "dormant" in description:
                result["accounts_type"] = "dormant"
                result["notes"].append("Dormant company - no trading activity")
            elif "total exempt" in description:
                result["accounts_type"] = "total-exemption"
                result["notes"].append("Total exemption from audit - limited disclosure")
            elif "full" in description or "group" in description:
                result["accounts_type"] = "full"
                result["notes"].append("Full accounts filed - comprehensive data")
            elif "abbreviated" in description:
                result["accounts_type"] = "abbreviated"
                result["notes"].append("Abbreviated accounts - limited balance sheet")
            else:
                result["accounts_type"] = "unknown"
            
            # Try to get the accounts document link
            links = latest_accounts.get("links", {})
            document_link = links.get("document_metadata") or links.get("self")
            
            if document_link:
                result["data_available"] = True
                result["filing_link"] = f"https://find-and-update.company-information.service.gov.uk{document_link}"
            
            # For UK companies, try to get accounts data from the company profile
            # The /company/{id}/uk-establishments endpoint might have more data
            # But the main data comes from parsing the actual accounts document
            
            # Try to infer size from accounts type
            if result["accounts_type"] in ["micro-entity"]:
                # Micro companies have assets < £316k and turnover < £632k
                result["notes"].append("Micro-entity: likely well within EIS asset limits")
                result["eis_checks"]["assets_eligible"] = True
                result["eis_checks"]["employees_eligible"] = True
            elif result["accounts_type"] in ["small"]:
                # Small companies have assets < £5.1m and turnover < £10.2m
                result["notes"].append("Small company: likely within EIS asset limits")
                result["eis_checks"]["assets_eligible"] = True
                result["eis_checks"]["employees_eligible"] = True
            elif result["accounts_type"] in ["dormant"]:
                result["notes"].append("Dormant: EIS requires trading company")
                result["eis_checks"]["assets_eligible"] = True
                result["eis_checks"]["employees_eligible"] = True
            elif result["accounts_type"] in ["full"]:
                result["notes"].append("Full accounts: may exceed EIS limits - verify manually")
                # Can't determine without parsing actual document
            
            # Try to get more data from extended company profile
            try:
                extended_data = self._make_request(f"/company/{company_number}")
                if extended_data:
                    # Some companies have account information in profile
                    accounts_info = extended_data.get("accounts", {})
                    if accounts_info:
                        result["next_accounts_due"] = accounts_info.get("next_due")
                        result["last_accounts_made_up_to"] = accounts_info.get("last_accounts", {}).get("made_up_to")
                    
                    # Annual return/confirmation data
                    annual_return = extended_data.get("annual_return", {}) or extended_data.get("confirmation_statement", {})
                    if annual_return:
                        result["last_confirmation_date"] = annual_return.get("last_made_up_to")
            except Exception:
                pass  # Non-critical
            
            return result
            
        except Exception as e:
            logger.warning(f"Failed to get accounts data for {company_number}: {e}")
            result["notes"].append(f"Error retrieving accounts: {str(e)}")
            return result
    
    def get_full_profile(self, company_number: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive company profile with ALL available data.
        
        Orchestrates calls to:
        - Company profile
        - Officers (directors/secretaries)
        - PSCs (shareholders)
        - Charges (mortgages/security)
        - Filing history (with analysis)
        
        Returns aggregated data suitable for EIS assessment.
        """
        company_number = company_number.zfill(8)
        
        try:
            # Get company profile (required)
            company = self.get_company(company_number)
            if not company:
                return None
            
            # Collect all data with graceful error handling
            officers = []
            pscs = []
            charges = []
            filings = {"items": [], "analysis": {}}
            
            try:
                officers = self.get_officers(company_number, active_only=False)
            except Exception as e:
                logger.warning(f"Failed to get officers for {company_number}: {e}")
            
            try:
                pscs = self.get_pscs(company_number)
            except Exception as e:
                logger.warning(f"Failed to get PSCs for {company_number}: {e}")
            
            try:
                charges = self.get_charges(company_number)
            except Exception as e:
                logger.warning(f"Failed to get charges for {company_number}: {e}")
            
            try:
                filings = self.get_filing_history_enhanced(company_number, items_per_page=25)
            except Exception as e:
                logger.warning(f"Failed to get filings for {company_number}: {e}")
            
            # NEW: Get accounts data for financial eligibility checks
            accounts_data = {}
            try:
                accounts_data = self.get_accounts_data(company_number)
            except Exception as e:
                logger.warning(f"Failed to get accounts data for {company_number}: {e}")
            
            # Separate active/resigned officers
            active_directors = [o for o in officers if "director" in o.officer_role.lower()]
            all_officers = [o.to_dict() for o in officers]
            
            # Separate active/inactive PSCs
            active_pscs = [p for p in pscs if p.get("is_active", True)]
            
            # Analyze charges
            outstanding_charges = [c for c in charges if c.get("is_outstanding", False)]
            
            return {
                "company": company.to_dict(),
                "officers": {
                    "items": all_officers,
                    "director_count": len(active_directors),
                    "total_count": len(officers),
                    "directors": [d.to_dict() for d in active_directors]
                },
                "pscs": {
                    "items": pscs,
                    "active_count": len(active_pscs),
                    "total_count": len(pscs)
                },
                "charges": {
                    "items": charges,
                    "outstanding_count": len(outstanding_charges),
                    "total_count": len(charges),
                    "has_outstanding": len(outstanding_charges) > 0
                },
                "filings": filings,
                "accounts": accounts_data,  # NEW: Financial data for EIS checks
                "data_sources": ["companies_house"],
                "retrieved_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get full profile for {company_number}: {e}")
            return None


# Sample EIS Companies for testing/demo
SAMPLE_EIS_COMPANIES = [
    {"company_number": "12345678", "name": "Tech Innovators Ltd", "sector": "Technology"},
    {"company_number": "87654321", "name": "Green Energy Solutions Ltd", "sector": "Clean Energy"},
    {"company_number": "11223344", "name": "MedTech Ventures Ltd", "sector": "Healthcare"},
    {"company_number": "44332211", "name": "FinTech Disruptors Ltd", "sector": "Financial Services"},
    {"company_number": "55667788", "name": "AI Research Labs Ltd", "sector": "Artificial Intelligence"},
]


def get_sample_eis_data() -> List[Dict[str, Any]]:
    """
    Get sample EIS company data for demo/testing.
    Returns mock data that resembles real EIS companies.
    """
    return [
        {
            "company_number": "14567890",
            "company_name": "Quantum Computing Innovations Ltd",
            "company_status": "active",
            "company_type": "ltd",
            "date_of_creation": "2023-03-15",
            "sector": "Technology",
            "sic_codes": ["62020", "72190"],
            "registered_office_address": {
                "address_line_1": "123 Innovation Park",
                "locality": "Belfast",
                "postal_code": "BT1 1AA",
                "country": "Northern Ireland"
            },
            "directors": [
                {"name": "Dr. Sarah Mitchell", "role": "CEO & Director"},
                {"name": "James O'Connor", "role": "Technical Director"}
            ],
            "eis_status": "Approved",
            "investment_stage": "Seed",
            "amount_raised": 250000,
            "risk_score": "Medium"
        },
        {
            "company_number": "14789012",
            "company_name": "GreenTech Energy Solutions Ltd",
            "company_status": "active",
            "company_type": "ltd",
            "date_of_creation": "2022-11-20",
            "sector": "Clean Energy",
            "sic_codes": ["35110", "43210"],
            "registered_office_address": {
                "address_line_1": "45 Eco Business Centre",
                "locality": "Dublin",
                "postal_code": "D02 Y123",
                "country": "Ireland"
            },
            "directors": [
                {"name": "Michael Green", "role": "Managing Director"},
                {"name": "Emma Wilson", "role": "Finance Director"}
            ],
            "eis_status": "Approved",
            "investment_stage": "Series A",
            "amount_raised": 1500000,
            "risk_score": "Low"
        },
        {
            "company_number": "15234567",
            "company_name": "MedAI Diagnostics Ltd",
            "company_status": "active",
            "company_type": "ltd",
            "date_of_creation": "2024-01-10",
            "sector": "Healthcare",
            "sic_codes": ["86900", "72110"],
            "registered_office_address": {
                "address_line_1": "Medical Innovation Hub",
                "locality": "Belfast",
                "postal_code": "BT9 5AA",
                "country": "Northern Ireland"
            },
            "directors": [
                {"name": "Dr. Aisha Patel", "role": "CEO"},
                {"name": "Prof. David Chen", "role": "Chief Scientific Officer"}
            ],
            "eis_status": "Pending",
            "investment_stage": "Pre-Seed",
            "amount_raised": 75000,
            "risk_score": "High"
        },
        {
            "company_number": "15678901",
            "company_name": "FinSecure Technologies Ltd",
            "company_status": "active",
            "company_type": "ltd",
            "date_of_creation": "2023-06-05",
            "sector": "Financial Services",
            "sic_codes": ["64999", "62012"],
            "registered_office_address": {
                "address_line_1": "FinTech Tower",
                "locality": "London",
                "postal_code": "EC2A 4BX",
                "country": "England"
            },
            "directors": [
                {"name": "Robert Thompson", "role": "CEO"},
                {"name": "Lisa Brown", "role": "CTO"}
            ],
            "eis_status": "Approved",
            "investment_stage": "Seed",
            "amount_raised": 500000,
            "risk_score": "Medium"
        },
        {
            "company_number": "15890123",
            "company_name": "AgriTech Innovations Ltd",
            "company_status": "active",
            "company_type": "ltd",
            "date_of_creation": "2023-09-01",
            "sector": "Agriculture",
            "sic_codes": ["01500", "72190"],
            "registered_office_address": {
                "address_line_1": "Rural Innovation Centre",
                "locality": "Antrim",
                "postal_code": "BT41 2AB",
                "country": "Northern Ireland"
            },
            "directors": [
                {"name": "Patrick Murphy", "role": "Managing Director"},
                {"name": "Siobhan Kelly", "role": "Operations Director"}
            ],
            "eis_status": "Approved",
            "investment_stage": "Seed",
            "amount_raised": 350000,
            "risk_score": "Medium"
        }
    ]


# Convenience function
def get_client() -> CompaniesHouseClient:
    """Get configured Companies House client."""
    return CompaniesHouseClient()
