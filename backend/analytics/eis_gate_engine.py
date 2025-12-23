"""
EIS Gate + Score Heuristic Engine

Two-stage EIS eligibility filter:
1. Gates (Binary Pass/Fail) - Hard rejections
2. Scoring (0-100 Points) - Likelihood assessment

Author: Sapphire Intelligence Platform
Version: 2.0
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Excluded SIC code prefixes (trades that cannot qualify for EIS)
EXCLUDED_SIC_PREFIXES = {
    "68": "Real Estate/Property",       # Property development, letting
    "64": "Financial Services",          # Banking, insurance, leasing
    "65": "Insurance",                   # Insurance activities
    "66": "Financial Auxiliaries",       # Fund management, broking
    "01": "Agriculture/Farming",         # Farming, agriculture
    "02": "Forestry",                    # Forestry and logging
    "03": "Fishing",                     # Fishing and aquaculture
    "69": "Legal/Accounting",            # Solicitors, accountants
    "70": "Management Consultancy",      # Holding companies
    "55": "Accommodation",               # Hotels (property-related)
}

# Qualifying SIC codes (preferred sectors for EIS)
QUALIFYING_SIC_PREFIXES = {
    "62": "Software/IT Services",
    "63": "Information Services",
    "72": "R&D",
    "58": "Publishing/Media",
    "26": "Electronics Manufacturing",
    "21": "Pharmaceuticals",
    "28": "Machinery Manufacturing",
}


@dataclass
class GateResult:
    """Result of a single gate check."""
    gate_name: str
    passed: bool
    reason: Optional[str] = None


@dataclass
class EISAssessment:
    """Complete EIS assessment result."""
    eis_status: str  # "LIKELY_ELIGIBLE", "GATED_OUT", "REVIEW_REQUIRED"
    eis_score: int
    gated_reason: Optional[str] = None
    gates_passed: List[str] = field(default_factory=list)
    gates_failed: List[str] = field(default_factory=list)
    score_breakdown: Dict[str, int] = field(default_factory=dict)
    flags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "eis_status": self.eis_status,
            "eis_score": self.eis_score,
            "gated_reason": self.gated_reason,
            "gates_passed": self.gates_passed,
            "gates_failed": self.gates_failed,
            "score_breakdown": self.score_breakdown,
            "flags": self.flags
        }


class EISGateEngine:
    """
    Two-stage EIS eligibility engine.
    
    Stage 1: Gates (Binary Pass/Fail)
    - Status Gate: Company must be 'active'
    - SIC Gate: No excluded trade sectors
    - Independence Gate: No corporate >50% control
    
    Stage 2: Scoring (0-100 Points)
    - Age, Equity Signal, Size, Governance, Jurisdiction, Penalties
    """
    
    def __init__(self):
        self.excluded_sic_prefixes = EXCLUDED_SIC_PREFIXES
        self.qualifying_sic_prefixes = QUALIFYING_SIC_PREFIXES
    
    # =========================================================================
    # MAIN ENTRY POINT
    # =========================================================================
    
    def assess(self, company_profile: Dict[str, Any]) -> EISAssessment:
        """
        Run full EIS assessment on a company profile.
        
        Args:
            company_profile: Full company profile with PSC data
            
        Returns:
            EISAssessment with status, score, and breakdown
        """
        assessment = EISAssessment(
            eis_status="REVIEW_REQUIRED",
            eis_score=0,
            score_breakdown={
                "age": 0,
                "equity_signal": 0,
                "size_proxy": 0,
                "governance": 0,
                "jurisdiction": 0,
                "penalties": 0
            }
        )
        
        # Stage 1: Run Gates
        gate_results = self._run_gates(company_profile)
        
        for result in gate_results:
            if result.passed:
                assessment.gates_passed.append(result.gate_name)
            else:
                assessment.gates_failed.append(result.gate_name)
                assessment.gated_reason = result.reason
                assessment.eis_status = "GATED_OUT"
                assessment.flags.append(f"GATE_FAILED: {result.gate_name}")
                logger.info(f"Company gated out: {result.reason}")
                return assessment  # Early exit on first gate failure
        
        # Stage 2: Calculate Score (only if all gates passed)
        score, breakdown, flags = self._calculate_score(company_profile)
        
        assessment.eis_score = score
        assessment.score_breakdown = breakdown
        assessment.flags.extend(flags)
        
        # Determine final status based on score
        if score >= 60:
            assessment.eis_status = "LIKELY_ELIGIBLE"
        elif score >= 40:
            assessment.eis_status = "REVIEW_REQUIRED"
        else:
            assessment.eis_status = "UNLIKELY_ELIGIBLE"
        
        logger.info(f"EIS Assessment: {assessment.eis_status} (Score: {score})")
        return assessment
    
    # =========================================================================
    # STAGE 1: GATES (Binary Pass/Fail)
    # =========================================================================
    
    def _run_gates(self, profile: Dict[str, Any]) -> List[GateResult]:
        """Run all binary gates."""
        return [
            self._status_gate(profile),
            self._sic_gate(profile),
            self._independence_gate(profile),
        ]
    
    def _status_gate(self, profile: Dict[str, Any]) -> GateResult:
        """
        Status Gate: Company must be 'active'.
        """
        company = profile.get("company", profile)
        status = company.get("company_status", "").lower()
        
        if status == "active":
            return GateResult(gate_name="status", passed=True)
        else:
            return GateResult(
                gate_name="status",
                passed=False,
                reason=f"Company not active (status: {status})"
            )
    
    def _sic_gate(self, profile: Dict[str, Any]) -> GateResult:
        """
        SIC Gate: Reject if SIC codes indicate excluded trades.
        Excluded: Property (68*), Finance (64*, 65*, 66*), Farming (01*, 02*, 03*)
        """
        company = profile.get("company", profile)
        sic_codes = company.get("sic_codes", [])
        
        if not sic_codes:
            # No SIC codes - pass with warning
            return GateResult(gate_name="sic_code", passed=True)
        
        for sic in sic_codes:
            sic_str = str(sic)
            for prefix, sector in self.excluded_sic_prefixes.items():
                if sic_str.startswith(prefix):
                    return GateResult(
                        gate_name="sic_code",
                        passed=False,
                        reason=f"Excluded trade sector: {sector} (SIC: {sic})"
                    )
        
        return GateResult(gate_name="sic_code", passed=True)
    
    def _independence_gate(self, profile: Dict[str, Any]) -> GateResult:
        """
        Independence Gate: Reject if a corporate entity holds >50% voting rights.
        EIS requires the company to be independent (not controlled by another company).
        """
        pscs = profile.get("persons_with_significant_control", [])
        
        if not pscs:
            # No PSC data available - pass with assumption
            return GateResult(gate_name="independence", passed=True)
        
        for psc in pscs:
            # Check if PSC is a corporate entity
            kind = psc.get("kind", "")
            is_corporate = "corporate" in kind.lower() or "legal-person" in kind.lower()
            
            if is_corporate:
                # Check voting rights
                natures = psc.get("natures_of_control", [])
                for nature in natures:
                    nature_lower = nature.lower()
                    # Check for >50% ownership indicators
                    if "ownership-of-shares-more-than-50" in nature_lower or \
                       "voting-rights-more-than-50" in nature_lower or \
                       "75-to-100" in nature_lower or \
                       "more-than-75" in nature_lower:
                        entity_name = psc.get("name", "Unknown corporate entity")
                        return GateResult(
                            gate_name="independence",
                            passed=False,
                            reason=f"Not independent: Corporate entity '{entity_name}' has >50% control"
                        )
        
        return GateResult(gate_name="independence", passed=True)
    
    # =========================================================================
    # STAGE 2: SCORING (0-100 Points)
    # =========================================================================
    
    def _calculate_score(self, profile: Dict[str, Any]) -> Tuple[int, Dict[str, int], List[str]]:
        """
        Calculate EIS likelihood score (0-100 points).
        
        Returns:
            (total_score, breakdown_dict, flags_list)
        """
        breakdown = {
            "age": 0,
            "equity_signal": 0,
            "size_proxy": 0,
            "governance": 0,
            "jurisdiction": 0,
            "penalties": 0
        }
        flags = []
        
        company = profile.get("company", profile)
        
        # 1. Age Score (max 30 points)
        breakdown["age"], age_flag = self._score_age(company)
        if age_flag:
            flags.append(age_flag)
        
        # 2. Equity Signal Score (max 20 points)
        breakdown["equity_signal"], equity_flag = self._score_equity_signal(profile)
        if equity_flag:
            flags.append(equity_flag)
        
        # 3. Size Proxy Score (max 15 points)
        breakdown["size_proxy"], size_flag = self._score_size_proxy(profile)
        if size_flag:
            flags.append(size_flag)
        
        # 4. Governance Score (max 10 points)
        breakdown["governance"], gov_flag = self._score_governance(profile)
        if gov_flag:
            flags.append(gov_flag)
        
        # 5. Jurisdiction Score (max 15 points)
        breakdown["jurisdiction"], jur_flag = self._score_jurisdiction(company)
        if jur_flag:
            flags.append(jur_flag)
        
        # 6. Penalties (negative points)
        breakdown["penalties"], penalty_flags = self._score_penalties(profile)
        flags.extend(penalty_flags)
        
        # Calculate total (ensure 0-100 range)
        total = sum(breakdown.values())
        total = max(0, min(100, total))
        
        return total, breakdown, flags
    
    def _score_age(self, company: Dict[str, Any]) -> Tuple[int, Optional[str]]:
        """
        Age scoring:
        - < 2 years: +30 points (SEIS eligible)
        - 2-7 years: +20 points (EIS sweet spot)
        - 7-10 years: +10 points (Still eligible)
        - > 10 years: +0 points
        """
        date_of_creation = company.get("date_of_creation")
        
        if not date_of_creation:
            return 10, "Age unknown - defaulting to neutral"
        
        try:
            if isinstance(date_of_creation, str):
                created = datetime.strptime(date_of_creation, "%Y-%m-%d")
            else:
                created = date_of_creation
            
            age_days = (datetime.now() - created).days
            age_years = age_days / 365.25
            
            if age_years < 2:
                return 30, f"Young company ({age_years:.1f}y) - SEIS eligible"
            elif age_years < 7:
                return 20, f"EIS eligible age ({age_years:.1f}y)"
            elif age_years < 10:
                return 10, f"Older but potentially eligible ({age_years:.1f}y)"
            else:
                return 0, f"Company too old for EIS ({age_years:.1f}y)"
        except Exception as e:
            logger.warning(f"Error parsing age: {e}")
            return 10, None
    
    def _score_equity_signal(self, profile: Dict[str, Any]) -> Tuple[int, Optional[str]]:
        """
        Equity Signal: +20 if SH01 filed in last 12 months.
        SH01 = Statement of Capital (new shares issued = investment activity)
        """
        filings = profile.get("filing_history", [])
        
        if not filings:
            return 5, None  # Neutral if no filing data
        
        twelve_months_ago = datetime.now() - timedelta(days=365)
        
        for filing in filings:
            filing_type = filing.get("type", "")
            filing_date_str = filing.get("date")
            
            if filing_type.upper() in ["SH01", "SH02", "SH03"]:
                try:
                    filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d")
                    if filing_date >= twelve_months_ago:
                        return 20, f"Recent equity activity (SH01 filed {filing_date_str})"
                except:
                    pass
        
        return 5, None  # No recent SH01
    
    def _score_size_proxy(self, profile: Dict[str, Any]) -> Tuple[int, Optional[str]]:
        """
        Size Proxy: +15 if accounts are Micro/Total Exemption (small company).
        Large companies (>£15m assets, >250 employees) are ineligible for EIS.
        """
        accounts = profile.get("accounts", {})
        accounts_type = accounts.get("accounts_type", "").lower()
        
        # Micro and Total Exemption indicate small company
        if "micro" in accounts_type or "total-exemption" in accounts_type:
            return 15, "Small company (Micro/Exemption accounts)"
        elif "small" in accounts_type:
            return 12, "Small company accounts"
        elif "dormant" in accounts_type:
            return 5, "Dormant company"
        elif "full" in accounts_type or "group" in accounts_type:
            return 0, "Large company (Full/Group accounts) - may exceed EIS limits"
        else:
            return 8, None  # Unknown - neutral
    
    def _score_governance(self, profile: Dict[str, Any]) -> Tuple[int, Optional[str]]:
        """
        Governance: +10 if company has more than 1 director.
        Multiple directors suggests better governance.
        """
        officers = profile.get("officers", [])
        
        if not officers:
            return 5, None
        
        directors = [o for o in officers if o.get("officer_role", "").lower() == "director"]
        active_directors = [d for d in directors if not d.get("resigned_on")]
        
        if len(active_directors) > 1:
            return 10, f"Good governance ({len(active_directors)} active directors)"
        elif len(active_directors) == 1:
            return 5, "Single director"
        else:
            return 0, "No active directors found"
    
    def _score_jurisdiction(self, company: Dict[str, Any]) -> Tuple[int, Optional[str]]:
        """
        Jurisdiction: +15 if UK registered.
        EIS requires UK permanent establishment.
        """
        jurisdiction = company.get("jurisdiction", "").lower()
        country = company.get("registered_office_address", {}).get("country", "").lower()
        
        if jurisdiction in ["england-wales", "scotland", "northern-ireland", "united-kingdom"]:
            return 15, "UK registered"
        elif "uk" in country or "united kingdom" in country or "england" in country:
            return 15, "UK registered"
        else:
            return 5, f"Non-UK or unclear jurisdiction ({jurisdiction})"
    
    def _score_penalties(self, profile: Dict[str, Any]) -> Tuple[int, List[str]]:
        """
        Penalties (negative points):
        - Confirmation Statement overdue: -20
        - Accounts overdue: -15
        - Has charges: -5
        - Has insolvency history: -30
        """
        penalties = 0
        flags = []
        
        company = profile.get("company", profile)
        
        # Check for overdue filings
        if company.get("confirmation_statement_overdue"):
            penalties -= 20
            flags.append("Confirmation Statement overdue (-20)")
        
        if company.get("accounts_overdue"):
            penalties -= 15
            flags.append("Accounts overdue (-15)")
        
        # Check for charges (secured debt)
        if company.get("has_charges"):
            penalties -= 5
            flags.append("Has charges/secured debt (-5)")
        
        # Check for insolvency
        if company.get("has_insolvency_history"):
            penalties -= 30
            flags.append("Insolvency history (-30)")
        
        return penalties, flags


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def assess_eis_eligibility(company_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to assess EIS eligibility.
    
    Args:
        company_profile: Full company profile with all available data
        
    Returns:
        Dict with eis_status, eis_score, gated_reason, score_breakdown, flags
    """
    engine = EISGateEngine()
    assessment = engine.assess(company_profile)
    return assessment.to_dict()
