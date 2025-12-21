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


# ==============================================================================
# INVESTOR QUALIFYING CONDITIONS
# ==============================================================================

INVESTOR_CONDITIONS = {
    "must_be_uk_taxpayer": True,
    "max_investment_per_year": 1_000_000,  # £1M standard
    "max_investment_per_year_kic": 2_000_000,  # £2M for KICs
    "min_holding_period_years": 3,
    "connection_rules": {
        "cannot_be_employee": True,
        "cannot_be_paid_director": True,  # Exception: business angel unpaid→paid
        "max_share_ownership_pct": 30,  # Cannot own >30% shares or voting rights
        "associates_count": ["spouse", "parents", "grandparents", "children", "grandchildren"],
        "excluded_associates": ["siblings"],  # Siblings NOT counted as associates
    },
}

# ==============================================================================
# COMPANY CORE CONDITIONS
# ==============================================================================

COMPANY_CONDITIONS = {
    # Age
    "max_age_from_first_commercial_sale_years": 7,
    "max_age_from_first_commercial_sale_years_kic": 10,
    
    # Size
    "max_employees": 250,
    "max_employees_kic": 500,
    "max_gross_assets_before_investment": 15_000_000,
    "max_gross_assets_after_investment": 16_000_000,
    
    # Independence
    "max_ownership_by_another_company_pct": 49,  # No company can own >49%
    "cannot_be_listed_on_recognised_exchange": True,
    "aim_allowed": True,  # AIM is explicitly allowed
    
    # UK presence
    "requires_uk_permanent_establishment": True,
    "uk_establishment_options": [
        "branch",
        "management_location",
        "qualifying_uk_agent",
        "companies_house_registration"
    ],
    
    # Risk finance limits
    "max_risk_finance_per_year": 5_000_000,
    "max_risk_finance_per_year_kic": 10_000_000,
    "max_risk_finance_lifetime": 12_000_000,
    "max_risk_finance_lifetime_kic": 20_000_000,
    
    # Share requirements
    "shares_must_be": [
        "full_risk_ordinary_shares",
        "fully_paid_in_cash_before_issue",
        "no_capital_preservation_arrangements",
        "no_pre_arranged_exit"
    ],
    
    # Other
    "must_meet_risk_to_capital_condition": True,
    "cannot_be_in_financial_difficulty": True,
    "must_maintain_conditions_for_years": 3,
    "non_qualifying_activities_max_pct": 20,  # HMRC "substantial" benchmark
}

# ==============================================================================
# KIC (KNOWLEDGE INTENSIVE COMPANY) CONDITIONS
# ==============================================================================

KIC_CONDITIONS = {
    # Two alternative qualification routes
    "ip_condition": {
        "description": "Developing IP to be exploited in its trade within 10 years",
    },
    "skilled_employee_condition": {
        "min_masters_or_higher_pct": 20,  # At least 20% with relevant Masters/PhD
        "research_experience_years": 3,  # Have been conducting research for 3+ years
    },
    # Additional requirements
    "max_employees": 500,
    "rd_innovation_min_pct_of_operating_costs_3_years": 10,  # 10% over 3 years
    "rd_innovation_min_pct_of_operating_costs_1_year": 15,  # OR 15% in any 1 of last 3 years
    # Age
    "max_age_from_first_commercial_sale_years": 10,
    "max_age_from_turnover_threshold_years": 10,  # From when annual turnover exceeded £200k
    "turnover_threshold": 200_000,
    # Investment limits
    "max_annual_investment": 10_000_000,
    "max_lifetime_investment": 20_000_000,
}

# ==============================================================================
# TAX BENEFITS (for investor reference)
# ==============================================================================

EIS_TAX_BENEFITS = {
    "income_tax_relief_pct": 30,  # 30% of investment against income tax
    "cgt_relief_on_disposal_pct": 100,  # 100% CGT free on qualifying disposal
    "cgt_deferral": True,  # Can defer CGT on other gains
    "inheritance_tax_relief_pct": 100,  # Within £1M allowance from 6 April 2026
    "loss_relief": True,  # Relief if company fails
}

SEIS_TAX_BENEFITS = {
    "income_tax_relief_pct": 50,  # 50% of investment
    "cgt_relief_on_disposal_pct": 100,
    "cgt_exemption_on_reinvested_gains_pct": 50,
    "inheritance_tax_relief_pct": 100,
    "loss_relief": True,
}

# ==============================================================================
# HMRC APPLICATION PROCESS
# ==============================================================================

HMRC_PROCESS = {
    "stages": [
        {
            "stage": 1,
            "name": "Advance Assurance",
            "description": "Optional but recommended pre-approval from HMRC",
            "required_documents": [
                "UTR (Unique Taxpayer Reference)",
                "CRN (Company Registration Number)",
                "Company accounts",
                "Business plan and financial forecasts",
                "Use of funds explanation",
                "Risk-to-capital explanation",
                "Schedule of previous tax-advantaged investments",
                "M&A and shareholder agreements",
                "Any prospectus or investment documentation",
                "State aid details",
                "Evidence of non-speculative interest (e.g., 6 potential investors or letter of intent)"
            ],
            "notes": "HMRC will confirm if the company is likely to qualify"
        },
        {
            "stage": 2,
            "name": "EIS1 - Compliance Statement",
            "description": "Submitted after shares are issued",
            "deadline": "Within 2 years of share issue",
            "required_documents": [
                "All Advance Assurance documents",
                "Bank statement showing shares fully paid in cash"
            ]
        },
        {
            "stage": 3,
            "name": "EIS2 - HMRC Approval",
            "description": "HMRC confirms share issue qualifies for EIS",
            "outcome": "Company can issue EIS3 certificates"
        },
        {
            "stage": 4,
            "name": "EIS3 - Investor Certificates",
            "description": "Individual certificates for each investor",
            "includes": [
                "Unique Investment Reference",
                "Termination date",
                "Company and investor signatures"
            ],
            "investor_action": "Claim tax relief using EIS3 details on tax return"
        }
    ],
    "urls": {
        "advance_assurance": "https://www.gov.uk/guidance/venture-capital-schemes-apply-to-use-the-enterprise-investment-scheme",
        "eis1_form": "https://www.gov.uk/government/publications/enterprise-investment-scheme-compliance-statement-eis1",
        "hmrc_contact": "https://www.gov.uk/government/organisations/hm-revenue-customs/contact"
    }
}

# ==============================================================================
# ADDITIONAL HELPER FUNCTIONS
# ==============================================================================

def check_company_independence(ownership_by_other_company_pct: float) -> Dict:
    """Check if company is sufficiently independent for EIS."""
    max_allowed = COMPANY_CONDITIONS["max_ownership_by_another_company_pct"]
    eligible = ownership_by_other_company_pct <= max_allowed
    
    return {
        "eligible": eligible,
        "ownership_pct": ownership_by_other_company_pct,
        "max_allowed_pct": max_allowed,
        "message": f"{'✅' if eligible else '❌'} {ownership_by_other_company_pct}% owned by other company (max: {max_allowed}%)"
    }


def check_investor_eligibility(
    share_ownership_pct: float,
    is_employee: bool = False,
    is_paid_director: bool = False
) -> Dict:
    """Check if an investor meets connection rules."""
    issues = []
    eligible = True
    
    max_ownership = INVESTOR_CONDITIONS["connection_rules"]["max_share_ownership_pct"]
    
    if share_ownership_pct > max_ownership:
        issues.append(f"Owns {share_ownership_pct}% shares (max: {max_ownership}%)")
        eligible = False
    
    if is_employee:
        issues.append("Cannot be employee of the company")
        eligible = False
    
    if is_paid_director:
        issues.append("Cannot be paid director (unless business angel exception applies)")
        eligible = False
    
    return {
        "eligible": eligible,
        "share_ownership_pct": share_ownership_pct,
        "is_employee": is_employee,
        "is_paid_director": is_paid_director,
        "issues": issues,
        "message": f"{'✅' if eligible else '❌'} Investor connection check: {len(issues)} issues"
    }


def check_kic_eligibility(
    employee_count: int,
    rd_spend_pct: float = None,
    masters_employees_pct: float = None,
    has_ip_development: bool = False
) -> Dict:
    """Check if company qualifies as Knowledge Intensive Company."""
    eligible = False
    reasons = []
    
    # Employee check
    if employee_count >= KIC_CONDITIONS["max_employees"]:
        return {
            "eligible": False,
            "reason": f"Too many employees ({employee_count} >= {KIC_CONDITIONS['max_employees']})",
            "reasons": []
        }
    
    # IP condition
    if has_ip_development:
        eligible = True
        reasons.append("Developing IP to be exploited in trade")
    
    # Skilled employee condition
    if masters_employees_pct and masters_employees_pct >= KIC_CONDITIONS["skilled_employee_condition"]["min_masters_or_higher_pct"]:
        eligible = True
        reasons.append(f"{masters_employees_pct}% employees with Masters/PhD (≥20%)")
    
    # R&D spend
    if rd_spend_pct:
        if rd_spend_pct >= KIC_CONDITIONS["rd_innovation_min_pct_of_operating_costs_1_year"]:
            eligible = True
            reasons.append(f"R&D spend: {rd_spend_pct}% of operating costs (≥15% in 1 year)")
        elif rd_spend_pct >= KIC_CONDITIONS["rd_innovation_min_pct_of_operating_costs_3_years"]:
            reasons.append(f"R&D spend: {rd_spend_pct}% (needs 10%+ for 3 consecutive years)")
    
    return {
        "eligible": eligible,
        "employee_count": employee_count,
        "rd_spend_pct": rd_spend_pct,
        "masters_employees_pct": masters_employees_pct,
        "has_ip_development": has_ip_development,
        "reasons": reasons,
        "message": f"{'✅ KIC Qualified' if eligible else '❌ Not KIC'}: {', '.join(reasons) if reasons else 'No qualifying conditions met'}"
    }


def get_complete_eligibility_checklist() -> Dict:
    """Get complete EIS eligibility checklist for display."""
    return {
        "company_conditions": {
            "age": "First commercial sale within 7 years (10 for KIC)",
            "employees": "< 250 full-time employees (< 500 for KIC)",
            "assets": "< £15M gross assets before investment",
            "trade": "Carrying out qualifying trade",
            "non_qualifying_activities": "< 20% in non-qualifying activities",
            "independence": "No company owns > 49% of shares",
            "listing": "Not listed on recognised exchange (AIM allowed)",
            "uk_presence": "Has UK permanent establishment",
            "risk_finance_annual": "< £5M risk finance per year (£10M KIC)",
            "risk_finance_lifetime": "< £12M total risk finance (£20M KIC)",
            "shares": "Full-risk ordinary shares, fully paid in cash",
            "risk_to_capital": "Genuine growth objective with loss risk",
            "financial_health": "Not in financial difficulty",
        },
        "investor_conditions": {
            "uk_taxpayer": "Must be UK taxpayer",
            "max_investment": "Up to £1M per year (£2M for KIC investments)",
            "holding_period": "Must hold shares for 3+ years",
            "not_employee": "Cannot be employee of the company",
            "not_paid_director": "Cannot be paid director (with exceptions)",
            "max_ownership": "Cannot own > 30% of shares/voting rights",
        },
        "excluded_trades": [
            "Property/land dealing",
            "Financial activities (banking, insurance, lending)",
            "Legal/accountancy services",
            "Leasing",
            "Farming/forestry",
            "Hotels/care homes",
            "Energy generation/export",
            "Coal/steel production",
            "Royalty-based models (except self-generated IP)",
        ],
        "tax_benefits": {
            "income_tax_relief": "30% of investment",
            "cgt_exemption": "100% on qualifying disposal",
            "cgt_deferral": "Defer gains reinvested",
            "iht_relief": "100% after 2 years (within £1M allowance)",
            "loss_relief": "Available if company fails",
        },
        "hmrc_process": [
            "1. Advance Assurance (recommended)",
            "2. EIS1 Compliance Statement (after shares issued)",
            "3. EIS2 HMRC Approval",
            "4. EIS3 Investor Certificates → Claim relief",
        ]
    }

