# EIS Investment Scanner
## Architecture & Technical Documentation

**Version 2.2.0** | December 2024 | Sapphire Intelligence Platform

---

## Executive Summary

The EIS Investment Scanner screens UK companies for **Enterprise Investment Scheme (EIS)** eligibility. It combines data from Companies House with AI-powered news analysis to generate eligibility scores and investment insights.

**Core Capabilities:**
- Search and analyze 5M+ UK companies via Companies House API
- Calculate EIS eligibility scores (0-100) using heuristic rules
- Fetch real-time AI news and financial data via Tavily
- Generate professional PDF reports and email newsletters

---

## System Architecture Overview

The platform follows a classic **3-tier architecture**:

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                            │
│  Next.js 14 + TypeScript + Tailwind CSS + Framer Motion         │
│                                                                  │
│  Pages: /eis (Scanner) | /research (Agent) | /daily-news        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND LAYER                             │
│  FastAPI + Python 3.11 + Pandas + WeasyPrint                    │
│                                                                  │
│  Services: EIS Heuristics | Research Agent | Newsletter         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      EXTERNAL APIs                               │
│                                                                  │
│  Companies House | Tavily AI | HuggingFace | Gmail SMTP         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. EIS Page — Company Search & Scoring

### What It Does

Users search for UK companies, view detailed profiles, and get EIS eligibility assessments with a 0-100 score.

### Data Flow

```
User enters company name
        │
        ▼
┌───────────────────┐     ┌────────────────────┐
│   Frontend        │────▶│  /api/eis/search   │
│   Search Bar      │     │  Backend Endpoint  │
└───────────────────┘     └─────────┬──────────┘
                                    │
                                    ▼
                          ┌─────────────────────┐
                          │  Companies House    │
                          │  Search API         │
                          └─────────┬───────────┘
                                    │
                                    ▼
                          ┌─────────────────────┐
                          │  Return company     │
                          │  list to frontend   │
                          └─────────────────────┘
```

### Company Profile Flow

```
User clicks on company
        │
        ▼
┌───────────────────────────────────────────────────────┐
│              /api/eis/company/{id}/full-profile       │
└───────────────────────────────────────────────────────┘
        │
        ├────▶ Companies House: Profile, Officers, PSCs, Filings
        │
        ├────▶ EIS Heuristics Engine: Calculate Score (0-100)
        │
        └────▶ Tavily (if no accounts): Fetch Revenue Data
        │
        ▼
┌───────────────────────────────────────────────────────┐
│              Return to Frontend:                       │
│  • Company Details                                     │
│  • EIS Score + Status Badge                           │
│  • Directors, PSCs, Share Allotments, Age, Revenue    │
│  • Eligibility Gates (Status, SIC, Independence)      │
│  • Score Breakdown by Factor                          │
└───────────────────────────────────────────────────────┘
```

### EIS Scoring Factors

| Factor | Max Points | Criteria |
|--------|-----------|----------|
| Company Age | 20 | Under 7 years old |
| Company Status | 15 | Active (not dissolved) |
| SIC Codes | 20 | Not in excluded sectors |
| Insolvency | 15 | No insolvency history |
| Excluded Trades | 15 | Not in banned activities |
| R&D Intensive | 15 | Knowledge-intensive indicators |
| **Total** | **100** | |

### Eligibility Logic

```
IF any factor score = 0  →  "Likely Not Eligible" (RED)
IF total score < 50      →  "Likely Not Eligible" (RED)
ELSE                     →  "Likely Eligible" (GREEN)
```

### Technology Used

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, Framer Motion
- **Backend**: FastAPI, Python 3.11
- **APIs**: Companies House (company data), Tavily (revenue fallback)
- **Storage**: Browser LocalStorage (portfolio)

---

## 2. Company Research Agent

### What It Does

Deep-dive research on any company using 16 parallel AI queries, with PDF export and email delivery.

### Data Flow

```
User enters: Company Name + Industry
        │
        ▼
┌───────────────────────────────────────────────────────┐
│              /api/research/company                     │
└───────────────────────────────────────────────────────┘
        │
        ├────▶ 4x Company Queries (funding, valuation, team, HQ)
        ├────▶ 4x Industry Queries (market, trends, competition)
        ├────▶ 4x Financial Queries (revenue, growth, funding)
        └────▶ 4x News Queries (latest, press, products)
        │
        ▼ (16 parallel Tavily API calls)
        │
┌───────────────────────────────────────────────────────┐
│              Aggregate into 4 Report Sections          │
│  1. Company Overview                                   │
│  2. Industry Analysis                                  │
│  3. Financial Profile                                  │
│  4. Recent Developments                                │
└───────────────────────────────────────────────────────┘
        │
        ├────▶ Copy to Clipboard
        ├────▶ /api/research/pdf → WeasyPrint → Download PDF
        └────▶ /api/research/email → Gmail SMTP → Send Report
```

### Technology Used

- **AI Search**: Tavily API (16 parallel queries)
- **PDF Generation**: WeasyPrint
- **Email**: Gmail SMTP with PDF attachment

---

## 3. Subscribe — Newsletter System

### What It Does

Generates and sends professional HTML newsletters with portfolio intelligence, AI company news, and sector insights.

### Newsletter Structure

```
┌─────────────────────────────────────────────────────────────┐
│  📧 EIS PORTFOLIO INTELLIGENCE — Weekly Snapshot            │
├─────────────────────────────────────────────────────────────┤
│  PORTFOLIO SUMMARY                                          │
│  • 7 companies reviewed                                     │
│  • 4 likely eligible | 2 review required | 1 ineligible    │
├─────────────────────────────────────────────────────────────┤
│  TOP CHANGES (Top 3 companies)                              │
│  • Company name, score, status, revenue, sector             │
│  • Risk signals + Recommended actions                       │
├─────────────────────────────────────────────────────────────┤
│  🤖 AI COMPANY INTELLIGENCE (Tavily News)                   │
│  • Per-company news summaries                               │
│  • Revenue, sector, eligibility status                      │
├─────────────────────────────────────────────────────────────┤
│  WATCHLIST (Companies needing review)                       │
├─────────────────────────────────────────────────────────────┤
│  FULL PORTFOLIO (Compact table)                             │
├─────────────────────────────────────────────────────────────┤
│  DATA SOURCES: Companies House, Tavily AI, HuggingFace      │
│  NEXT RUN: Monday 08:00 (Weekly)                            │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User clicks Subscribe → Send Now
        │
        ▼
┌───────────────────────────────────────────────────────┐
│         /api/eis/automation/send-email                 │
└───────────────────────────────────────────────────────┘
        │
        ├────▶ Load portfolio companies from request
        │
        ├────▶ For each company (max 5):
        │         • Companies House: Get latest profile
        │         • Tavily: Search company news
        │         • HuggingFace: Summarize with Mistral 7B
        │
        ├────▶ Fetch sector news (Tech, Healthcare, Fintech)
        │
        ├────▶ Generate HTML email (7 sections)
        │
        └────▶ Gmail SMTP → Recipient inbox
```

### Frequency Options

| Frequency | Next Run |
|-----------|----------|
| Now | Immediate (manual trigger) |
| Weekly | Every Monday at 08:00 |
| Monthly | 1st of month at 08:00 |
| Yearly | January 1st at 08:00 |

---

## 4. AI Newsroom

### What It Does

Fetches real-time news for a selected company using Tavily AI search, then summarizes with HuggingFace LLM.

### Data Flow

```
User clicks "AI Newsroom" button on company card
        │
        ▼
┌───────────────────────────────────────────────────────┐
│         /api/eis/company/{id}/news                     │
└───────────────────────────────────────────────────────┘
        │
        ├────▶ Tavily: Search "{company} news funding UK"
        │         → Returns 5-10 news articles
        │
        ├────▶ Filter by relevance score
        │
        └────▶ HuggingFace: Summarize for EIS context
                 → Mistral 7B Instruct model
        │
        ▼
┌───────────────────────────────────────────────────────┐
│              Display in Modal:                         │
│  • AI-generated summary                                │
│  • News article cards with headlines                   │
│  • Source links (clickable)                            │
└───────────────────────────────────────────────────────┘
```

### Technology Used

- **News Search**: Tavily API
- **Summarization**: HuggingFace API with Mistral 7B Instruct

---

## 5. AI Daily News

### What It Does

Provides sector-wide UK investment news across 4 key sectors for EIS-eligible startups.

### Sectors Covered

| Sector | Query Focus |
|--------|-------------|
| Technology | UK tech startup funding, Series A, 2024-2025 |
| Healthcare | UK biotech, medtech startup investment |
| Fintech | UK digital banking, payments startups |
| Clean Energy | UK cleantech, green energy funding |

### Data Flow

```
User clicks "AI Daily News" in header
        │
        ▼
┌───────────────────────────────────────────────────────┐
│         /api/eis/daily-news                            │
└───────────────────────────────────────────────────────┘
        │
        ├────▶ Tavily: Technology query (parallel)
        ├────▶ Tavily: Healthcare query (parallel)
        ├────▶ Tavily: Fintech query (parallel)
        └────▶ Tavily: Clean Energy query (parallel)
        │
        ▼
┌───────────────────────────────────────────────────────┐
│              Display on /daily-news page:              │
│  • Sector tabs (click to filter)                       │
│  • News grid with article cards                        │
│  • AI market insights summary                          │
└───────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| Next.js 14 | React framework with SSR |
| TypeScript | Type-safe JavaScript |
| Tailwind CSS | Utility-first styling |
| Framer Motion | Animations |
| Lucide React | Icon library |
| Recharts | Score gauge charts |

### Backend
| Technology | Purpose |
|------------|---------|
| FastAPI | Python REST API framework |
| Python 3.11 | Backend language |
| Pandas | Data processing |
| WeasyPrint | PDF generation |

### External APIs
| API | Purpose |
|-----|---------|
| Companies House | UK company data (profiles, officers, filings) |
| Tavily | AI-powered news search |
| HuggingFace | LLM summarization (Mistral 7B) |
| Gmail SMTP | Email delivery |

### Storage
| Storage | Purpose |
|---------|---------|
| LocalStorage | Portfolio persistence in browser |
| scan_history.json | Scan results cache |
| trained_models/ | ML model files |

---

## Environment Variables

Create `backend/.env` with:

```env
# Companies House (required)
COMPANIES_HOUSE_API_KEY=your_key_here

# Tavily AI Search (required for AI features)
TAVILY_API_KEY=tvly-xxxxxxxxxxxx

# HuggingFace LLM (required for AI summaries)
HF_API_KEY=hf_xxxxxxxxxxxx

# Gmail (required for newsletter)
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password
```

---

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/eis/search/{query}` | GET | Search UK companies |
| `/api/eis/company/{id}/full-profile` | GET | Full company profile + EIS score |
| `/api/eis/company/{id}/news` | GET | AI Newsroom for company |
| `/api/eis/daily-news` | GET | Sector-wide daily news |
| `/api/eis/automation/send-email` | POST | Send newsletter |
| `/api/research/company` | POST | Deep company research |
| `/api/research/pdf` | POST | Generate PDF report |
| `/api/research/email` | POST | Email research report |

---

*Document Version: 2.2.0*  
*Last Updated: December 26, 2024*  
*Sapphire Intelligence Platform*
