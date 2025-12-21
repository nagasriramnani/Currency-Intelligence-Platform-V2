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
