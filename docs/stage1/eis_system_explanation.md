# EIS Fact-Finding System - Complete Explanation

**Document Purpose:** Explain how the EIS assessment system works for both technical and non-technical stakeholders.

---

# Part 1: Non-Technical Explanation

## What is EIS?

The **Enterprise Investment Scheme (EIS)** is a UK government program that gives tax relief to investors who buy shares in small, high-risk companies. It encourages investment in startups and growing businesses.

### Tax Benefits for Investors

| Benefit | Amount |
|---------|--------|
| Income Tax Relief | 30% of investment |
| Capital Gains Tax | Exempt if held 3+ years |
| Loss Relief | Can offset against income tax |
| Inheritance Tax | Exempt after 2 years |

### EIS Requirements (Simplified)

For a company to be EIS-eligible:
- ✅ Less than 7 years old (or 10 years if "knowledge-intensive")
- ✅ Fewer than 250 employees
- ✅ Less than £15 million in assets
- ✅ Must be a UK company
- ✅ Must be trading (not dormant)
- ✅ Cannot be in excluded sectors (property, finance, legal)
- ✅ No insolvency history

---

## What Does Our System Do?

Our system helps investors **quickly assess** whether UK companies might be eligible for EIS. It does this by:

1. **Searching** for companies in the official UK Companies House registry
2. **Loading** all publicly available data about each company
3. **Scoring** each company against EIS criteria
4. **Generating** a professional PDF report

### What We CAN Tell You

| Information | Source | Reliability |
|-------------|--------|-------------|
| Company age | Companies House | 100% accurate |
| Active/dormant status | Companies House | 100% accurate |
| Industry sector (SIC codes) | Companies House | 100% accurate |
| Directors and owners | Companies House | 100% accurate |
| Insolvency history | Companies House | 100% accurate |
| Outstanding debts (charges) | Companies House | 100% accurate |

### What We CANNOT Tell You

| Information | Why Not |
|-------------|---------|
| **Official EIS registration** | HMRC doesn't share this publicly |
| Revenue/turnover | Not in Companies House (buried in accounts PDFs) |
| Number of employees | Not reliably available |
| Previous EIS investments | Private information |

---

## How Does the Scoring Work?

Think of it like a **health check** for EIS potential:

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│   COMPANY DATA                YOUR EIS SCORE                   │
│   ─────────────               ──────────────                   │
│                                                                │
│   Age: 3 years     ───────►   ██████████████████░░  85/100    │
│   Status: Active              "Likely Eligible"                │
│   No insolvency                                                │
│   Tech sector                  ✅ Worth investigating          │
│   2 directors                                                  │
│   No debts                                                     │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Score Meanings

| Score | Status | What It Means |
|-------|--------|---------------|
| 75-100 | **Likely Eligible** ✅ | Looks promising - worth pursuing |
| 50-74 | **Review Required** ⚠️ | Some concerns - needs investigation |
| 0-49 | **Likely Ineligible** ❌ | Has disqualifying factors |

### ⚠️ Important Disclaimer

> **Our score is an INDICATOR, not a guarantee.**
> 
> Only HMRC can confirm if a company is actually EIS-registered. We cannot access HMRC data. Our assessment is based on publicly available information and should be used as a starting point for due diligence, not a final decision.

---

## The Report

When you generate a PDF report, you get:

1. **Cover Page** - Portfolio summary
2. **Executive Summary** - How many companies look eligible
3. **Sector Analysis** - Breakdown by industry
4. **Company Profiles** - Detailed info on each company
5. **Risk Matrix** - Red flags identified
6. **Disclaimer** - Legal notice about limitations

---

# Part 2: Technical Explanation

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                                │
│                   (Next.js React Frontend)                          │
│            http://localhost:3000/eis                                │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            │ HTTP Requests
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        BACKEND API                                   │
│                   (FastAPI Python Server)                           │
│            http://localhost:8000/api/eis/*                          │
│                                                                     │
│  ┌──────────────────────┐  ┌────────────────────────────────────┐  │
│  │ Companies House      │  │ EIS Heuristics Module              │  │
│  │ Client               │  │ (eis_heuristics.py)                │  │
│  │                      │  │                                    │  │
│  │ - get_company()      │  │ - calculate_eis_likelihood()       │  │
│  │ - get_officers()     │  │ - check_sic_exclusions()           │  │
│  │ - get_pscs()         │  │ - 10 scoring factors               │  │
│  │ - get_charges()      │  │                                    │  │
│  │ - get_filings()      │  └────────────────────────────────────┘  │
│  │ - get_full_profile() │                                          │
│  └──────────┬───────────┘  ┌────────────────────────────────────┐  │
│             │              │ Newsletter Generator               │  │
│             │              │ (eis_newsletter.py)                │  │
│             │              │                                    │  │
│             ▼              │ - Generate PDF                     │  │
│  ┌──────────────────────┐  │ - Cover page, summaries            │  │
│  │ Companies House API  │  │ - Company profiles                 │  │
│  │ (UK Government)      │  │ - Risk matrix                      │  │
│  │                      │  └────────────────────────────────────┘  │
│  │ api.company-         │                                          │
│  │ information.         │                                          │
│  │ service.gov.uk       │                                          │
│  └──────────────────────┘                                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### 1. Search Companies

```
GET /api/eis/search?query=tech&limit=20
```

**Purpose:** Find companies by name or number

**Response:**
```json
{
  "results": [
    {
      "company_number": "12345678",
      "title": "TECH INNOVATIONS LTD",
      "company_status": "active",
      "address_snippet": "London, EC1A 1BB"
    }
  ]
}
```

---

### 2. Get Full Company Profile

```
GET /api/eis/company/{company_number}/full-profile
```

**Purpose:** Fetch ALL available data about a company + EIS assessment

**What it does:**
1. Calls 5 Companies House API endpoints
2. Aggregates all data
3. Runs EIS heuristics calculation
4. Returns combined result

**Response Structure:**
```json
{
  "company": {
    "company_number": "12345678",
    "company_name": "TECH INNOVATIONS LTD",
    "company_status": "active",
    "date_of_creation": "2021-03-15",
    "sic_codes": ["62012"],
    "has_insolvency_history": false,
    "has_charges": false
  },
  "officers": {
    "director_count": 2,
    "directors": [...]
  },
  "pscs": {
    "items": [...],  // Shareholders with 25%+ ownership
    "active_count": 2
  },
  "charges": {
    "items": [...],  // Mortgages, security interests
    "outstanding_count": 0
  },
  "filings": {
    "items": [...],
    "analysis": {
      "has_share_allotments": true,
      "accounts_type": "micro-entity"
    }
  },
  "eis_assessment": {
    "score": 85,
    "status": "Likely Eligible",
    "factors": [
      {
        "factor": "Company Age",
        "value": "3 years",
        "points": 15,
        "max_points": 20,
        "rationale": "Under 7 years - eligible for EIS",
        "impact": "positive"
      },
      // ... 9 more factors
    ],
    "flags": [],
    "recommendations": ["Consider applying for HMRC Advance Assurance"]
  }
}
```

---

### 3. Generate Newsletter PDF

```
POST /api/eis/newsletter
Content-Type: application/json

[
  { company1_data... },
  { company2_data... }
]
```

**Purpose:** Generate professional PDF report

**Response:** Binary PDF file

---

## EIS Heuristics Algorithm

### Code Location
`backend/analytics/eis_heuristics.py`

### Function: `calculate_eis_likelihood()`

```python
def calculate_eis_likelihood(full_profile: Dict) -> Dict:
    """
    Calculate EIS likelihood score based on Companies House data.
    
    Returns:
        score: 0-100
        status: "Likely Eligible" | "Review Required" | "Likely Ineligible"
        factors: List of 10 scoring factors with explanations
    """
```

### Factor Calculation Logic

#### Factor 1: Company Age (max 20 points)
```python
age = get_company_age_years(company.get("date_of_creation"))

if age <= 2:
    score += 20  # SEIS eligible
elif age <= 7:
    score += 15  # EIS eligible
elif age <= 10:
    score += 5   # Knowledge-intensive exception possible
else:
    score += 0   # Too old
```

#### Factor 2: Company Status (max 15 points)
```python
status = company.get("company_status", "").lower()

if status == "active":
    score += 15
else:
    score += 0
    flags.append("Company not active - must be trading for EIS")
```

#### Factor 3: Insolvency History (max 15 points)
```python
has_insolvency = company.get("has_insolvency_history", False)

if not has_insolvency:
    score += 15
else:
    score += 0
    flags.append("Insolvency history - disqualifying factor")
```

#### Factor 4: SIC Code Analysis (max 15 points)
```python
# Excluded SIC codes (property, finance, legal, etc.)
EXCLUDED_SIC_CODES = {
    "68100": "Buying and selling of own real estate",
    "64110": "Central banking",
    "69102": "Solicitors",
    # ... more exclusions
}

if company has excluded SIC code:
    score += 0
    flags.append("Excluded sector")
elif company has qualifying SIC code:
    score += 15
else:
    score += 10  # Neutral
```

#### Factor 5-10: Additional Checks
- Share allotments (SH01 filings) → Investment activity
- Outstanding charges → Financial risk
- Director structure → Governance
- UK jurisdiction → Required
- Filing compliance → Company health
- Accounts type → Size indicator

### Status Thresholds

```python
if score >= 75:
    status = "Likely Eligible"
elif score >= 50:
    status = "Review Required"
else:
    status = "Likely Ineligible"
```

---

## Data Flow: User Journey

```
User searches "tech startup"
        │
        ▼
Frontend calls: GET /api/eis/search?query=tech+startup
        │
        ▼
Backend calls Companies House: /search/companies
        │
        ▼
Results displayed in UI
        │
        ▼
User clicks "Add to Portfolio" on a company
        │
        ▼
Frontend calls: GET /api/eis/company/12345678/full-profile
        │
        ▼
Backend orchestrates 5 API calls:
  ├─► /company/12345678
  ├─► /company/12345678/officers
  ├─► /company/12345678/persons-with-significant-control
  ├─► /company/12345678/charges
  └─► /company/12345678/filing-history
        │
        ▼
Backend runs: calculate_eis_likelihood(full_profile)
        │
        ▼
Combined result returned to frontend
        │
        ▼
User sees expandable sections with all data + EIS score
        │
        ▼
User clicks "Generate Report"
        │
        ▼
Frontend calls: POST /api/eis/newsletter with selected companies
        │
        ▼
Backend generates PDF using ReportLab
        │
        ▼
PDF downloaded to user's computer
```

---

## Companies House API

### API Key Setup

```env
# .env file
COMPANIES_HOUSE_API_KEY=your-api-key-here
```

### Authentication

```python
# HTTP Basic Auth
self.session.auth = (self.api_key, "")  # Key as username, empty password
```

### Rate Limits

| Limit | Value |
|-------|-------|
| Requests per 5 minutes | 600 |
| Recommended delay | 100ms between requests |

### API Base URL
```
https://api.company-information.service.gov.uk
```

### Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `/company/{number}` | Company profile |
| `/company/{number}/officers` | Directors, secretaries |
| `/company/{number}/persons-with-significant-control` | Major shareholders |
| `/company/{number}/charges` | Mortgages, security |
| `/company/{number}/filing-history` | Filed documents |

---

## File Structure

```
backend/
├── api/
│   └── server.py              # FastAPI endpoints
├── data/
│   └── companies_house.py     # Companies House API client
├── analytics/
│   └── eis_heuristics.py      # EIS scoring algorithm
├── reports/
│   └── eis_newsletter.py      # PDF generation
└── .env                       # API keys

frontend/
└── src/app/eis/
    └── page.tsx               # React component

docs/stage1/
└── data_source_evaluation.md  # Documentation
```

---

## Key Limitations to Remember

1. **HMRC Status Unknown** - We cannot verify actual EIS registration
2. **No Financial Data** - Revenue/profit not available without iXBRL parsing
3. **Heuristic Only** - Score is an indicator, not a guarantee
4. **Data Lag** - Companies House data may be up to 24 hours old
5. **Rate Limits** - 600 requests per 5 minutes

---

**Document Version:** 1.0  
**Last Updated:** December 2024  
**Author:** Sapphire Intelligence Platform
