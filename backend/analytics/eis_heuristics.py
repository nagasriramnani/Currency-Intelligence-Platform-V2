"""
EIS Heuristics Module

Provides rule-based EIS (Enterprise Investment Scheme) eligibility assessment
using data from Companies House API.

This is a Stage 1 heuristic-based approach - NOT a definitive EIS determination.
Actual EIS eligibility requires HMRC advance assurance application.

Author: Sapphire Intelligence Platform
Version: 2.0 (Enhanced with comprehensive requirements)
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date

# Import comprehensive EIS requirements
from analytics.eis_requirements import (
    EIS_RULES,
    EXCLUDED_SIC_CODES_FULL,
    EXCLUDED_SIC_PREFIXES,
    POSITIVE_SIC_CODES as POSITIVE_SIC_CODES_NEW,
    KIC_SIC_CODES,
    is_excluded_sic,
    is_kic_sic,
    is_positive_sic,
    check_employee_eligibility,
    check_asset_eligibility,
    check_age_eligibility,
    get_requirement_summary,
    get_hmrc_advance_assurance_url,
)

logger = logging.getLogger(__name__)

# ============================================================================
# EXCLUDED SIC CODES (now imports from eis_requirements for comprehensive list)
# Companies with these SIC codes are typically NOT eligible for EIS
# Reference: https://www.gov.uk/guidance/venture-capital-schemes-apply-to-use-the-seed-enterprise-investment-scheme
# ============================================================================

# Use comprehensive list from eis_requirements
EXCLUDED_SIC_CODES = EXCLUDED_SIC_CODES_FULL

EXCLUDED_SIC_CODES = {
    # Property/Land dealing
    "41100": "Development of building projects",
    "41201": "Construction of commercial buildings",
    "41202": "Construction of domestic buildings",
    "68100": "Buying and selling of own real estate",
    "68201": "Renting and operating of Housing Association real estate",
    "68202": "Letting and operating of conference and exhibition centres",
    "68209": "Other letting and operating of own or leased real estate",
    "68310": "Real estate agencies",
    "68320": "Management of real estate on a fee or contract basis",
    
    # Financial activities (most)
    "64110": "Central banking",
    "64191": "Banks",
    "64192": "Building societies",
    "64201": "Activities of financial holding companies",
    "64202": "Activities of other holding companies",
    "64301": "Activities of investment trusts",
    "64302": "Activities of unit trusts",
    "64303": "Activities of venture capital trusts",
    "64910": "Financial leasing",
    "64921": "Credit granting by non-deposit taking finance houses",
    "64922": "Activities of mortgage finance companies",
    "64991": "Security dealing on own account",
    "64999": "Other financial service activities",
    
    # Legal/accounting activities
    "69101": "Barristers at law",
    "69102": "Solicitors",
    "69109": "Activities of patent and copyright agents",
    "69201": "Accounting and auditing activities",
    "69202": "Bookkeeping activities",
    "69203": "Tax consultancy",
    
    # Farming/agriculture (with land)
    "01110": "Growing of cereals (except rice)",
    "01120": "Growing of rice",
    "01130": "Growing of vegetables and melons",
    
    # Energy generation (with land exceptions)
    "35110": "Production of electricity",
    "35120": "Transmission of electricity",
    "35130": "Distribution of electricity",
    
    # Forestry
    "02100": "Silviculture and other forestry activities",
    "02200": "Logging",
    
    # Hotels/property-based hospitality
    "55100": "Hotels and similar accommodation",
    "55201": "Holiday centres and villages",
    "55202": "Youth hostels",
    "55209": "Other holiday and other collective accommodation",
    
    # Gambling
    "92000": "Gambling and betting activities",
}

# SIC codes that indicate positive EIS sectors
POSITIVE_SIC_CODES = {
    # Technology
    "62011": "Ready-made interactive leisure and entertainment software development",
    "62012": "Business and domestic software development",
    "62020": "Computer consultancy activities",
    "62030": "Computer facilities management activities",
    "62090": "Other information technology service activities",
    
    # R&D
    "72110": "Research and experimental development on biotechnology",
    "72190": "Other research and experimental development on natural sciences and engineering",
    
    # Healthcare/MedTech
    "86210": "General medical practice activities",
    "86220": "Specialist medical practice activities",
    
    # Creative/Digital
    "58210": "Publishing of computer games",
    "58290": "Other software publishing",
    "59111": "Motion picture production activities",
    
    # Clean tech
    "71121": "Engineering design activities for industrial process and production",
}


def get_company_age_years(date_of_creation: Optional[str]) -> int:
    """Calculate company age in years from incorporation date."""
    if not date_of_creation:
        return 0
    try:
        if '-' in date_of_creation:
            created = datetime.strptime(date_of_creation.split('T')[0], '%Y-%m-%d')
        else:
            created = datetime.strptime(date_of_creation[:10], '%Y-%m-%d')
        age = (datetime.now() - created).days / 365.25
        return int(age)
    except Exception as e:
        logger.warning(f"Could not parse date {date_of_creation}: {e}")
        return 0


def check_sic_exclusions(sic_codes: List[str]) -> Dict[str, Any]:
    """Check if any SIC codes are in the excluded list."""
    excluded = []
    positive = []
    
    for sic in sic_codes:
        sic = str(sic).strip()
        if sic in EXCLUDED_SIC_CODES:
            excluded.append({
                "code": sic,
                "description": EXCLUDED_SIC_CODES[sic],
                "impact": "negative"
            })
        elif sic in POSITIVE_SIC_CODES:
            positive.append({
                "code": sic,
                "description": POSITIVE_SIC_CODES[sic],
                "impact": "positive"
            })
    
    return {
        "has_exclusions": len(excluded) > 0,
        "excluded_codes": excluded,
        "positive_codes": positive,
        "all_codes": sic_codes
    }


def calculate_eis_likelihood(full_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate EIS likelihood score based on Companies House data.
    
    This is a HEURISTIC assessment, not a definitive EIS determination.
    Actual eligibility requires HMRC advance assurance.
    
    Args:
        full_profile: Output from CompaniesHouseClient.get_full_profile()
        
    Returns:
        EIS assessment with:
        - score (0-100)
        - status (Likely Eligible / Review Required / Likely Ineligible)
        - factors (list of scoring factors with explanations)
        - flags (risk indicators)
        - confidence level
        - recommendations
    """
    
    company = full_profile.get("company", {})
    officers = full_profile.get("officers", {})
    pscs = full_profile.get("pscs", {})
    charges = full_profile.get("charges", {})
    filings = full_profile.get("filings", {})
    accounts = full_profile.get("accounts", {})  # NEW: Financial data
    
    # =========================================================================
    # ZOMBIE COMPANY HARD GATE (Bug Fix #3)
    # Dissolved/liquidated companies get immediate 0 score - do not calculate
    # =========================================================================
    status = company.get("company_status", "").lower()
    zombie_statuses = ['dissolved', 'liquidation', 'closed', 'struck-off', 'converted-closed', 'receivership', 'administration']
    
    if status in zombie_statuses:
        logger.info(f"ZOMBIE COMPANY HARD GATE: Status is '{status}' - returning 0 score immediately")
        return {
            "score": 0,
            "max_score": 110,
            "percentage": 0,
            "status": "Likely Ineligible",
            "status_description": f"Company is {status} - cannot be eligible for EIS investment",
            "confidence": "High",
            "confidence_description": "Companies House status is definitive",
            "factors": [{
                "factor": "Company Status",
                "value": status.title(),
                "points": 0,
                "max_points": 110,
                "rationale": f"Company is {status} - this is an automatic disqualification for EIS",
                "impact": "negative"
            }],
            "flags": [f"⛔ DISQUALIFIED: Company status is '{status}' - legally dead companies cannot receive EIS investment"],
            "recommendations": ["This company is not eligible for EIS investment - it is no longer active"],
            "sic_analysis": {"has_exclusions": False, "excluded_codes": [], "positive_codes": [], "all_codes": []},
            "is_kic": False,
            "kic_sic_codes": [],
            "methodology": "Hard gate - dissolved companies are automatically ineligible",
            "disclaimer": "This is an automatic disqualification. Dissolved companies cannot receive EIS investment.",
            "assessed_at": datetime.now().isoformat()
        }
    
    # Initialize scoring
    score = 0
    max_score = 110  # Updated: includes new Financial Size factor (10 points)
    factors = []
    flags = []
    
    # NEW: Extract accounts-based EIS eligibility checks
    accounts_eis_checks = accounts.get("eis_checks", {}) if accounts else {}
    accounts_type = accounts.get("accounts_type") if accounts else None
    accounts_notes = accounts.get("notes", []) if accounts else []
    
    # =========================================================================
    # FACTOR 1: Company Age (max 20 points)
    # EIS: Company must be <7 years old at first share issue
    # SEIS: Company must be <2 years old
    # =========================================================================
    age = get_company_age_years(company.get("date_of_creation"))
    
    if age <= 2:
        score += 20
        factors.append({
            "factor": "Company Age",
            "value": f"{age} years",
            "points": 20,
            "max_points": 20,
            "rationale": "Under 2 years - eligible for SEIS and EIS",
            "impact": "positive"
        })
    elif age <= 7:
        score += 15
        factors.append({
            "factor": "Company Age",
            "value": f"{age} years",
            "points": 15,
            "max_points": 20,
            "rationale": "Under 7 years - eligible for EIS",
            "impact": "positive"
        })
    elif age <= 10:
        score += 5
        factors.append({
            "factor": "Company Age",
            "value": f"{age} years",
            "points": 5,
            "max_points": 20,
            "rationale": "Over 7 years - may still qualify with knowledge-intensive exception",
            "impact": "neutral"
        })
        flags.append("Company over 7 years old - requires knowledge-intensive status for EIS")
    else:
        factors.append({
            "factor": "Company Age",
            "value": f"{age} years",
            "points": 0,
            "max_points": 20,
            "rationale": "Over 10 years - unlikely to qualify for EIS",
            "impact": "negative"
        })
        flags.append("Company over 10 years old - EIS eligibility unlikely")
    
    # =========================================================================
    # FACTOR 2: Company Status (max 15 points)
    # Must be active/trading
    # =========================================================================
    status = company.get("company_status", "").lower()
    
    if status == "active":
        score += 15
        factors.append({
            "factor": "Company Status",
            "value": status.title(),
            "points": 15,
            "max_points": 15,
            "rationale": "Company is active and trading",
            "impact": "positive"
        })
    else:
        factors.append({
            "factor": "Company Status",
            "value": status.title(),
            "points": 0,
            "max_points": 15,
            "rationale": f"Company is {status} - not eligible for EIS",
            "impact": "negative"
        })
        flags.append(f"Company status is '{status}' - must be active for EIS")
    
    # =========================================================================
    # FACTOR 3: Insolvency History (max 15 points)
    # No insolvency history allowed
    # =========================================================================
    has_insolvency = company.get("has_insolvency_history", False)
    
    if not has_insolvency:
        score += 15
        factors.append({
            "factor": "Insolvency History",
            "value": "None",
            "points": 15,
            "max_points": 15,
            "rationale": "No insolvency proceedings recorded",
            "impact": "positive"
        })
    else:
        factors.append({
            "factor": "Insolvency History",
            "value": "Yes",
            "points": 0,
            "max_points": 15,
            "rationale": "Insolvency history makes EIS eligibility unlikely",
            "impact": "negative"
        })
        flags.append("⚠️ Insolvency history recorded - disqualifying for EIS")
    
    # =========================================================================
    # FACTOR 4: SIC Code Analysis (max 15 points)
    # Check for excluded trading activities
    # =========================================================================
    sic_codes = company.get("sic_codes", [])
    sic_analysis = check_sic_exclusions(sic_codes)
    
    if sic_analysis["has_exclusions"]:
        factors.append({
            "factor": "SIC Code Exclusions",
            "value": f"{len(sic_analysis['excluded_codes'])} excluded",
            "points": 0,
            "max_points": 15,
            "rationale": f"SIC codes indicate excluded activities: {', '.join([c['code'] for c in sic_analysis['excluded_codes']])}",
            "impact": "negative"
        })
        for exc in sic_analysis["excluded_codes"]:
            flags.append(f"Excluded SIC: {exc['code']} - {exc['description']}")
    elif sic_analysis["positive_codes"]:
        score += 15
        factors.append({
            "factor": "SIC Code Analysis",
            "value": f"Qualifying sector",
            "points": 15,
            "max_points": 15,
            "rationale": f"SIC codes indicate qualifying activities: {', '.join([c['code'] for c in sic_analysis['positive_codes']])}",
            "impact": "positive"
        })
    else:
        score += 10
        factors.append({
            "factor": "SIC Code Analysis",
            "value": f"No exclusions found",
            "points": 10,
            "max_points": 15,
            "rationale": f"SIC codes: {', '.join(sic_codes) if sic_codes else 'None recorded'}",
            "impact": "neutral"
        })
    
    # =========================================================================
    # FACTOR 5: Share Allotments (max 10 points)
    # SH01 filings indicate investment activity
    # =========================================================================
    filing_analysis = filings.get("analysis", {})
    has_share_allotments = filing_analysis.get("has_share_allotments", False)
    allotment_count = filing_analysis.get("share_allotment_count", 0)
    
    if has_share_allotments:
        score += 10
        factors.append({
            "factor": "Share Allotments",
            "value": f"{allotment_count} recorded",
            "points": 10,
            "max_points": 10,
            "rationale": "Share allotment returns (SH01) indicate investment activity",
            "impact": "positive"
        })
    else:
        score += 3
        factors.append({
            "factor": "Share Allotments",
            "value": "None recorded",
            "points": 3,
            "max_points": 10,
            "rationale": "No share allotments in recent filings - may indicate limited investment history",
            "impact": "neutral"
        })
    
    # =========================================================================
    # FACTOR 6: Outstanding Charges (max 5 points)
    # Lower risk if no outstanding charges
    # =========================================================================
    outstanding_charges = charges.get("outstanding_count", 0)
    
    if outstanding_charges == 0:
        score += 5
        factors.append({
            "factor": "Outstanding Charges",
            "value": "None",
            "points": 5,
            "max_points": 5,
            "rationale": "No outstanding charges or mortgages",
            "impact": "positive"
        })
    else:
        factors.append({
            "factor": "Outstanding Charges",
            "value": f"{outstanding_charges} outstanding",
            "points": 0,
            "max_points": 5,
            "rationale": f"{outstanding_charges} outstanding charge(s) may affect investment risk",
            "impact": "neutral"
        })
        flags.append(f"{outstanding_charges} outstanding charge(s) registered")
    
    # =========================================================================
    # FACTOR 7: Director Stability (max 5 points)
    # Stable director history is positive
    # =========================================================================
    director_count = officers.get("director_count", 0)
    
    if director_count >= 2:
        score += 5
        factors.append({
            "factor": "Director Structure",
            "value": f"{director_count} directors",
            "points": 5,
            "max_points": 5,
            "rationale": "Multiple directors indicates structured governance",
            "impact": "positive"
        })
    elif director_count == 1:
        score += 3
        factors.append({
            "factor": "Director Structure",
            "value": "1 director",
            "points": 3,
            "max_points": 5,
            "rationale": "Single director - typical for early-stage company",
            "impact": "neutral"
        })
    else:
        factors.append({
            "factor": "Director Structure",
            "value": "No directors found",
            "points": 0,
            "max_points": 5,
            "rationale": "No active directors found - unusual",
            "impact": "negative"
        })
        flags.append("No active directors found")
    
    # =========================================================================
    # FACTOR 8: UK Jurisdiction (max 5 points)
    # Must be UK company
    # =========================================================================
    jurisdiction = company.get("jurisdiction", "").lower()
    
    if jurisdiction in ["england-wales", "scotland", "northern-ireland", "england", "wales"]:
        score += 5
        factors.append({
            "factor": "Jurisdiction",
            "value": jurisdiction.title(),
            "points": 5,
            "max_points": 5,
            "rationale": "UK jurisdiction - required for EIS",
            "impact": "positive"
        })
    else:
        factors.append({
            "factor": "Jurisdiction",
            "value": jurisdiction.title() if jurisdiction else "Unknown",
            "points": 0,
            "max_points": 5,
            "rationale": f"Non-UK jurisdiction may affect eligibility",
            "impact": "neutral"
        })
    
    # =========================================================================
    # FACTOR 9: Filing Compliance (max 5 points)
    # Regular filing indicates healthy company
    # =========================================================================
    has_accounts = filing_analysis.get("has_annual_accounts", False)
    last_confirmation = filing_analysis.get("last_confirmation_statement")
    
    if has_accounts and last_confirmation:
        score += 5
        factors.append({
            "factor": "Filing Compliance",
            "value": "Up to date",
            "points": 5,
            "max_points": 5,
            "rationale": "Recent accounts and confirmation statement filed",
            "impact": "positive"
        })
    elif has_accounts or last_confirmation:
        score += 3
        factors.append({
            "factor": "Filing Compliance",
            "value": "Partial",
            "points": 3,
            "max_points": 5,
            "rationale": "Some recent filings found",
            "impact": "neutral"
        })
    else:
        factors.append({
            "factor": "Filing Compliance",
            "value": "Unknown",
            "points": 0,
            "max_points": 5,
            "rationale": "Could not verify recent filings",
            "impact": "neutral"
        })
    
    # =========================================================================
    # FACTOR 10: Accounts Type (max 5 points)
    # Micro/small accounts suggest eligible size
    # =========================================================================
    accounts_type = filing_analysis.get("accounts_type")
    
    if accounts_type in ["micro-entity", "small", "abbreviated"]:
        score += 5
        factors.append({
            "factor": "Accounts Type",
            "value": accounts_type.title(),
            "points": 5,
            "max_points": 5,
            "rationale": f"{accounts_type.title()} accounts suggest company is within EIS size limits",
            "impact": "positive"
        })
    elif accounts_type == "full":
        score += 2
        factors.append({
            "factor": "Accounts Type",
            "value": "Full accounts",
            "points": 2,
            "max_points": 5,
            "rationale": "Full accounts - may exceed EIS size limits, requires verification",
            "impact": "neutral"
        })
        flags.append("Full accounts filed - verify company meets EIS size requirements")
    elif accounts_type == "dormant":
        factors.append({
            "factor": "Accounts Type",
            "value": "Dormant",
            "points": 0,
            "max_points": 5,
            "rationale": "Dormant accounts - company may not be trading",
            "impact": "negative"
        })
        flags.append("Dormant accounts filed - EIS requires trading company")
    else:
        score += 2
        factors.append({
            "factor": "Accounts Type",
            "value": "Unknown",
            "points": 2,
            "max_points": 5,
            "rationale": "Could not determine accounts type",
            "impact": "neutral"
        })
    
    # =========================================================================
    # FACTOR 11: Financial Size Check (max 10 points) - NEW
    # Uses accounts data to verify EIS asset/employee limits
    # =========================================================================
    if accounts_eis_checks:
        assets_ok = accounts_eis_checks.get("assets_eligible")
        employees_ok = accounts_eis_checks.get("employees_eligible")
        
        if assets_ok is True and employees_ok is True:
            score += 10
            factors.append({
                "factor": "Financial Size (from Accounts)",
                "value": f"{accounts_type or 'filed'} accounts",
                "points": 10,
                "max_points": 10,
                "rationale": "Company size indicators suggest EIS eligibility (assets < £15m, employees < 250)",
                "impact": "positive"
            })
        elif assets_ok is True or employees_ok is True:
            score += 5
            factors.append({
                "factor": "Financial Size (from Accounts)",
                "value": f"{accounts_type or 'filed'} accounts",
                "points": 5,
                "max_points": 10,
                "rationale": "Partial EIS size criteria met - some limits need verification",
                "impact": "neutral"
            })
        elif assets_ok is False or employees_ok is False:
            factors.append({
                "factor": "Financial Size (from Accounts)",
                "value": "Exceeds limits",
                "points": 0,
                "max_points": 10,
                "rationale": "Company may exceed EIS size limits - verify gross assets < £15m and employees < 250",
                "impact": "negative"
            })
            flags.append("⚠️ Financial size may exceed EIS limits - manual verification required")
        else:
            score += 3
            factors.append({
                "factor": "Financial Size (from Accounts)",
                "value": "Unknown",
                "points": 3,
                "max_points": 10,
                "rationale": "Could not verify size from accounts - manual check recommended",
                "impact": "neutral"
            })
    else:
        score += 3
        factors.append({
            "factor": "Financial Size (from Accounts)",
            "value": "No data",
            "points": 3,
            "max_points": 10,
            "rationale": "Accounts data not available - size eligibility unknown",
            "impact": "neutral"
        })
    
    # Add any accounts notes as flags
    for note in accounts_notes[:3]:
        if note not in flags:
            flags.append(f"📊 {note}")
    
    # =========================================================================
    # DETERMINE STATUS AND CONFIDENCE
    # =========================================================================
    
    if score >= 75:
        status = "Likely Eligible"
        status_description = "High likelihood of EIS eligibility based on available data"
    elif score >= 50:
        status = "Review Required"
        status_description = "Moderate likelihood - some factors need verification"
    else:
        status = "Likely Ineligible"
        status_description = "Low likelihood based on identified exclusion factors"
    
    # Confidence based on data completeness
    data_points = sum([
        1 if company.get("date_of_creation") else 0,
        1 if company.get("sic_codes") else 0,
        1 if officers.get("director_count", 0) > 0 else 0,
        1 if pscs.get("total_count", 0) > 0 else 0,
        1 if filing_analysis.get("total_filings", 0) > 0 else 0,
    ])
    
    if data_points >= 4:
        confidence = "High"
        confidence_description = "Good data completeness from Companies House"
    elif data_points >= 2:
        confidence = "Medium"
        confidence_description = "Some data points missing"
    else:
        confidence = "Low"
        confidence_description = "Limited data available"
    
    # Generate recommendations
    recommendations = []
    if score >= 50:
        recommendations.append("Consider applying for HMRC Advance Assurance")
    if has_insolvency:
        recommendations.append("Investigate insolvency history before proceeding")
    if sic_analysis["has_exclusions"]:
        recommendations.append("Verify trading activities do not fall within excluded categories")
    if age > 7:
        recommendations.append("Assess if company qualifies as 'knowledge-intensive' for extended age limit")
    if outstanding_charges > 0:
        recommendations.append("Review outstanding charges for investment risk assessment")
    
    # =========================================================================
    # KIC (Knowledge Intensive Company) Detection
    # =========================================================================
    sic_codes = company.get("sic_codes", [])
    is_kic = any(is_kic_sic(sic) for sic in sic_codes)
    kic_sics = [sic for sic in sic_codes if is_kic_sic(sic)]
    
    if is_kic:
        flags.append(f"🧪 Knowledge Intensive Company indicators found (SIC: {', '.join(kic_sics)})")
        flags.append("KIC companies qualify for extended limits: 10 years age, 500 employees, £20m lifetime")
    
    # Get age eligibility with KIC consideration
    age = get_company_age_years(company.get("date_of_creation"))
    age_check = check_age_eligibility(age, is_kic=is_kic)
    
    return {
        "score": score,
        "max_score": max_score,
        "percentage": round(score / max_score * 100, 1),
        "status": status,
        "status_description": status_description,
        "confidence": confidence,
        "confidence_description": confidence_description,
        "factors": factors,
        "flags": flags,
        "recommendations": recommendations,
        "sic_analysis": sic_analysis,
        
        # New: KIC and requirements info
        "is_kic": is_kic,
        "kic_sic_codes": kic_sics,
        "official_requirements": get_requirement_summary(),
        "hmrc_advance_assurance_url": get_hmrc_advance_assurance_url(),
        "age_eligibility": age_check,
        
        "methodology": "Heuristic-based assessment using Companies House data",
        "disclaimer": "This is an indicative assessment only. Actual EIS eligibility requires HMRC Advance Assurance.",
        "assessed_at": datetime.now().isoformat()
    }


def get_eis_summary(assessment: Dict[str, Any]) -> str:
    """Generate a human-readable summary of EIS assessment."""
    score = assessment.get("score", 0)
    status = assessment.get("status", "Unknown")
    flags = assessment.get("flags", [])
    
    summary = f"EIS Assessment: {status} (Score: {score}/100)\n\n"
    
    # Top factors
    factors = assessment.get("factors", [])
    positive = [f for f in factors if f.get("impact") == "positive"]
    negative = [f for f in factors if f.get("impact") == "negative"]
    
    if positive:
        summary += "✅ Positive Factors:\n"
        for f in positive[:3]:
            summary += f"  • {f['factor']}: {f['value']}\n"
    
    if negative:
        summary += "\n❌ Negative Factors:\n"
        for f in negative[:3]:
            summary += f"  • {f['factor']}: {f['value']}\n"
    
    if flags:
        summary += "\n⚠️ Flags:\n"
        for flag in flags[:5]:
            summary += f"  • {flag}\n"
    
    return summary
