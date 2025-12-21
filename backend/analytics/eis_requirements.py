"""
EIS Requirements Configuration

Comprehensive EIS/SEIS qualification rules based on HMRC guidance.
Reference: https://www.gov.uk/guidance/venture-capital-schemes-apply-to-use-the-enterprise-investment-scheme

This module provides:
- Complete excluded trades list
- EIS/SEIS thresholds
- KIC (Knowledge Intensive Company) criteria
- Qualification rules

Author: Sapphire Intelligence Platform
Version: 1.0
"""

from typing import Dict, List, Set

# ==============================================================================
# EIS THRESHOLDS AND LIMITS
# ==============================================================================

EIS_RULES = {
    # Age limits
    "max_age_years": 7,
    "max_age_years_kic": 10,
    "max_age_years_seis": 3,
    
    # Employee limits
    "max_employees": 250,
    "max_employees_kic": 500,
    "max_employees_seis": 25,
    
    # Financial limits (GBP)
    "max_gross_assets_before": 15_000_000,
    "max_gross_assets_after": 16_000_000,
    "max_gross_assets_seis": 350_000,
    
    # Investment limits (GBP per year)
    "max_annual_investment": 5_000_000,
    "max_annual_investment_kic": 10_000_000,
    "max_annual_investment_seis": 250_000,
    
    # Lifetime limits (GBP)
    "max_lifetime_investment": 12_000_000,
    "max_lifetime_investment_kic": 20_000_000,
    
    # Investor limits (GBP per tax year)
    "max_investor_limit": 1_000_000,
    "max_investor_limit_kic": 2_000_000,
    
    # Holding period (years)
    "min_holding_period": 3,
}

# ==============================================================================
# EXCLUDED TRADES (COMPREHENSIVE)
# Per HMRC VCS guidance - companies with these activities are NOT eligible
# ==============================================================================

EXCLUDED_TRADES = [
    # Property/Land dealing
    "dealing_in_land",
    "dealing_in_commodities",
    "dealing_in_futures",
    "dealing_in_shares_securities",
    
    # Financial activities
    "banking",
    "insurance",
    "money_lending",
    "debt_factoring",
    "hire_purchase_financing",
    "finance_leasing",
    "activities_of_investment_trusts",
    "activities_of_unit_trusts",
    
    # Legal and accountancy
    "legal_services",
    "accountancy_services",
    
    # Property-backed
    "property_development",
    "letting_of_property",
    "operating_hotels_guest_houses",
    "nursing_homes_residential_care",
    
    # Primary production
    "farming_market_gardening",
    "woodlands",
    "forestry",
    "ship_building",
    "coal_production",
    "steel_production",
    
    # Energy (certain types)
    "operating_wind_farms",  # May be excluded
    "operating_solar_farms",  # May be excluded
    "energy_generation_feed_in_tariff",
    
    # Other
    "leasing_assets",
    "receiving_royalties_licence_fees",  # Unless technology IP
    "providing_services_to_another_trade",
]

# ==============================================================================
# EXCLUDED SIC CODES (COMPREHENSIVE)
# Two-digit prefixes that indicate likely exclusion
# ==============================================================================

EXCLUDED_SIC_PREFIXES = {
    "01": "Agriculture/Farming",
    "02": "Forestry",
    "06": "Oil/Gas extraction",
    "55": "Hotels/Accommodation",
    "64": "Financial services",
    "65": "Insurance",
    "66": "Auxiliary financial",
    "68": "Real estate",
    "69": "Legal/Accounting",
    "92": "Gambling",
}

EXCLUDED_SIC_CODES_FULL = {
    # Property/Real Estate
    "41100": "Development of building projects",
    "41201": "Construction of commercial buildings",
    "41202": "Construction of domestic buildings",
    "68100": "Buying and selling of own real estate",
    "68201": "Renting Housing Association real estate",
    "68202": "Conference/exhibition centres",
    "68209": "Other letting of real estate",
    "68310": "Real estate agencies",
    "68320": "Management of real estate",
    
    # Financial Services (complete list)
    "64110": "Central banking",
    "64191": "Banks",
    "64192": "Building societies",
    "64201": "Financial holding companies",
    "64202": "Other holding companies",
    "64205": "Activities of head offices",
    "64301": "Investment trusts",
    "64302": "Unit trusts",
    "64303": "Venture capital trusts",
    "64304": "Open-ended investment companies",
    "64305": "Property unit trusts",
    "64306": "REITs",
    "64910": "Financial leasing",
    "64921": "Credit granting by non-deposit taking finance houses",
    "64922": "Mortgage finance companies",
    "64929": "Other credit granting",
    "64991": "Security dealing on own account",
    "64992": "Factoring",
    "64999": "Other financial service activities",
    
    # Insurance
    "65110": "Life insurance",
    "65120": "Non-life insurance",
    "65201": "Life reinsurance",
    "65202": "Non-life reinsurance",
    "65300": "Pension funding",
    
    # Legal and Accounting
    "69101": "Barristers at law",
    "69102": "Solicitors",
    "69109": "Patent and copyright agents",
    "69201": "Accounting and auditing",
    "69202": "Bookkeeping activities",
    "69203": "Tax consultancy",
    
    # Agriculture and Farming
    "01110": "Growing cereals",
    "01120": "Growing rice",
    "01130": "Growing vegetables",
    "01140": "Growing sugar cane",
    "01150": "Growing tobacco",
    "01160": "Growing fibre crops",
    "01190": "Growing other non-perennial crops",
    "01210": "Growing grapes",
    "01220": "Growing tropical fruits",
    "01230": "Growing citrus fruits",
    "01240": "Growing pome fruits",
    "01250": "Growing other tree fruits",
    "01260": "Growing oleaginous fruits",
    "01270": "Growing beverage crops",
    "01280": "Growing spices",
    "01290": "Growing other perennial crops",
    "01410": "Raising dairy cattle",
    "01420": "Raising other cattle",
    "01430": "Raising horses",
    "01440": "Raising camels",
    "01450": "Raising sheep and goats",
    "01460": "Raising pigs",
    "01470": "Raising poultry",
    "01490": "Raising other animals",
    
    # Forestry
    "02100": "Silviculture and forestry",
    "02200": "Logging",
    "02300": "Gathering wild products",
    "02400": "Support services to forestry",
    
    # Hotels and Accommodation
    "55100": "Hotels and similar",
    "55201": "Holiday centres and villages",
    "55202": "Youth hostels",
    "55209": "Other collective accommodation",
    "55300": "Camping grounds",
    "55900": "Other accommodation",
    
    # Gambling
    "92000": "Gambling and betting activities",
    
    # Oil and Gas
    "06100": "Extraction of crude petroleum",
    "06200": "Extraction of natural gas",
    
    # Coal and Steel (State Aid excluded)
    "05101": "Deep coal mines",
    "05102": "Open cast coal",
    "24100": "Manufacture of basic iron and steel",
}

# ==============================================================================
# KNOWLEDGE INTENSIVE COMPANY (KIC) INDICATORS
# ==============================================================================

KIC_SIC_CODES = {
    # R&D
    "72110": "R&D on biotechnology",
    "72190": "R&D in natural sciences",
    "72200": "R&D in social sciences",
    
    # Technology
    "62011": "Interactive software development",
    "62012": "Business software development",
    
    # Pharmaceuticals
    "21100": "Manufacture of basic pharmaceuticals",
    "21200": "Manufacture of pharmaceutical preparations",
    
    # Medical devices
    "26600": "Manufacture of medical equipment",
    "32500": "Medical and dental instruments",
}

KIC_CRITERIA = {
    "min_rd_spend_revenue_pct": 15,  # At least 15% of revenue on R&D
    "min_rd_spend_costs_pct": 10,    # Or 10% of operating costs
    "min_skilled_employees_pct": 20, # 20% with Masters/PhD
    "requires_ip_creation": True,
}

# ==============================================================================
# POSITIVE INDICATORS
# SIC codes that indicate strong EIS suitability
# ==============================================================================

POSITIVE_SIC_CODES = {
    # Technology
    "62011": "Interactive software development",
    "62012": "Business software development",
    "62020": "Computer consultancy",
    "62030": "Computer facilities management",
    "62090": "Other IT services",
    "63110": "Data processing and hosting",
    "63120": "Web portals",
    
    # R&D and Science
    "72110": "Biotechnology R&D",
    "72190": "Natural sciences R&D",
    
    # Healthcare/MedTech
    "86101": "Hospital activities",
    "86102": "Medical nursing home",
    "86210": "General medical practice",
    "86220": "Specialist medical practice",
    "86900": "Other human health",
    
    # Manufacturing (high-tech)
    "21200": "Pharmaceutical preparations",
    "26110": "Electronic components",
    "26200": "Computers and peripheral",
    "26301": "Telegraph and telephone",
    "26511": "Electronic instruments",
    
    # Creative/Digital
    "58210": "Publishing of computer games",
    "58290": "Other software publishing",
    "59111": "Motion picture production",
    "59120": "Post-production of films",
    "59131": "Motion picture distribution",
    
    # Clean Tech
    "71121": "Engineering design activities",
    "71122": "Engineering related consultancy",
}

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def is_excluded_sic(sic_code: str) -> bool:
    """Check if a SIC code is in the excluded list."""
    sic = str(sic_code).strip()
    
    # Check full code match
    if sic in EXCLUDED_SIC_CODES_FULL:
        return True
    
    # Check 2-digit prefix
    prefix = sic[:2] if len(sic) >= 2 else sic
    if prefix in EXCLUDED_SIC_PREFIXES:
        return True
    
    return False


def is_kic_sic(sic_code: str) -> bool:
    """Check if a SIC code indicates Knowledge Intensive Company."""
    return str(sic_code).strip() in KIC_SIC_CODES


def is_positive_sic(sic_code: str) -> bool:
    """Check if a SIC code indicates positive EIS suitability."""
    return str(sic_code).strip() in POSITIVE_SIC_CODES


def check_employee_eligibility(employee_count: int, is_kic: bool = False) -> Dict:
    """Check if employee count meets EIS requirements."""
    max_allowed = EIS_RULES["max_employees_kic"] if is_kic else EIS_RULES["max_employees"]
    
    eligible = employee_count <= max_allowed
    
    return {
        "eligible": eligible,
        "employee_count": employee_count,
        "max_allowed": max_allowed,
        "is_kic": is_kic,
        "message": f"{'✅' if eligible else '❌'} {employee_count} employees (max: {max_allowed})"
    }


def check_asset_eligibility(gross_assets: float) -> Dict:
    """Check if gross assets meet EIS requirements."""
    max_before = EIS_RULES["max_gross_assets_before"]
    max_after = EIS_RULES["max_gross_assets_after"]
    
    eligible = gross_assets <= max_before
    
    return {
        "eligible": eligible,
        "gross_assets": gross_assets,
        "max_before_investment": max_before,
        "max_after_investment": max_after,
        "message": f"{'✅' if eligible else '❌'} £{gross_assets:,.0f} assets (max: £{max_before:,.0f})"
    }


def check_age_eligibility(age_years: int, is_kic: bool = False) -> Dict:
    """Check if company age meets EIS requirements."""
    max_age = EIS_RULES["max_age_years_kic"] if is_kic else EIS_RULES["max_age_years"]
    
    eligible = age_years <= max_age
    seis_eligible = age_years <= EIS_RULES["max_age_years_seis"]
    
    return {
        "eis_eligible": eligible,
        "seis_eligible": seis_eligible,
        "age_years": age_years,
        "max_age_eis": max_age,
        "max_age_seis": EIS_RULES["max_age_years_seis"],
        "is_kic": is_kic,
        "message": f"{'✅' if eligible else '❌'} {age_years} years (max: {max_age})"
    }


def get_hmrc_advance_assurance_url() -> str:
    """Get URL for HMRC Advance Assurance application."""
    return "https://www.gov.uk/guidance/venture-capital-schemes-apply-to-use-the-enterprise-investment-scheme"


def get_requirement_summary() -> Dict:
    """Get a summary of all EIS requirements for display."""
    return {
        "company_age": {
            "eis": f"< {EIS_RULES['max_age_years']} years",
            "eis_kic": f"< {EIS_RULES['max_age_years_kic']} years",
            "seis": f"< {EIS_RULES['max_age_years_seis']} years",
        },
        "employees": {
            "eis": f"< {EIS_RULES['max_employees']}",
            "eis_kic": f"< {EIS_RULES['max_employees_kic']}",
            "seis": f"< {EIS_RULES['max_employees_seis']}",
        },
        "gross_assets": {
            "eis": f"< £{EIS_RULES['max_gross_assets_before']:,}",
            "seis": f"< £{EIS_RULES['max_gross_assets_seis']:,}",
        },
        "investment_limits": {
            "eis_annual": f"£{EIS_RULES['max_annual_investment']:,}/year",
            "eis_lifetime": f"£{EIS_RULES['max_lifetime_investment']:,} total",
            "seis_annual": f"£{EIS_RULES['max_annual_investment_seis']:,}/year",
        },
        "holding_period": f"{EIS_RULES['min_holding_period']} years minimum",
        "hmrc_url": get_hmrc_advance_assurance_url(),
    }
