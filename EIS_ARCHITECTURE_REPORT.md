# EIS Investment Scanner - Architecture Report

## Complete System Architecture & Component Documentation

**Version:** 2.2.0  
**Last Updated:** December 27, 2024  
**Author:** Sapphire Intelligence Team

---

## Table of Contents

1. [Complete EIS Page Architecture](#1-complete-eis-page-architecture)
2. [Company Research Agent](#2-company-research-agent)
3. [Newsletter Subscribe System](#3-newsletter-subscribe-system)
4. [AI Newsroom](#4-ai-newsroom)
5. [AI Daily News](#5-ai-daily-news)

---

## 1. Complete EIS Page Architecture

### Overview
The EIS Investment Scanner is a full-stack application that screens UK companies for Enterprise Investment Scheme eligibility using Companies House data and AI-powered analysis.

### System Block Diagram

```mermaid
flowchart LR
    subgraph User["� User"]
        Search["Search Company"]
    end

    subgraph Frontend["🖥️ Frontend"]
        Dashboard["EIS Dashboard"]
        Details["Company Details"]
        Portfolio["Portfolio"]
    end

    subgraph Backend["⚙️ Backend"]
        API["FastAPI Server"]
        Scorer["EIS Scorer"]
    end

    subgraph APIs["🌐 External APIs"]
        CH["Companies House"]
        Tavily["Tavily"]
    end

    Search --> Dashboard
    Dashboard --> API
    API --> CH
    CH --> Scorer
    Scorer --> Details
    API --> Tavily
    Tavily --> Details
    Details --> Portfolio
```

### Data Flow (Step by Step)

```mermaid
flowchart TD
    A["1️⃣ User Searches Company"] --> B["2️⃣ API calls Companies House"]
    B --> C["3️⃣ Fetch Profile + Officers + Filings"]
    C --> D["4️⃣ EIS Heuristics Engine Scores"]
    D --> E{"5️⃣ Financial Data Available?"}
    E -->|Yes| F["6️⃣ Show Score + Revenue"]
    E -->|No| G["6️⃣ Tavily Fetches Revenue"]
    G --> F
    F --> H["7️⃣ User Adds to Portfolio"]
```

### Key Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **EIS Dashboard** | React + TypeScript | Main user interface |
| **Company Search** | Next.js API Routes | Search Companies House |
| **EIS Heuristics Engine** | Python | Calculate eligibility score |
| **Score Calculator** | Python | 0-100 scoring with factors |
| **Tavily Financial** | Tavily API | Fallback revenue lookup |

### Plugins & Presets Used

| Plugin/Library | Version | Purpose |
|----------------|---------|---------|
| **Next.js** | 14.x | React framework with App Router |
| **Tailwind CSS** | 3.x | Utility-first styling |
| **Framer Motion** | 10.x | Animations & transitions |
| **Lucide React** | Latest | Icon library |
| **Recharts** | 2.x | Data visualization |
| **FastAPI** | 0.100+ | Python REST API |
| **Pandas** | 2.x | Data processing |
| **httpx** | 0.24+ | Async HTTP client |

### EIS Scoring Factors

```mermaid
pie title EIS Score Distribution (100 Points)
    "Company Age under 7 years" : 20
    "Active Status" : 15
    "Qualifying SIC Codes" : 20
    "No Insolvency" : 15
    "No Excluded Trades" : 15
    "R&D/Knowledge Intensive" : 15
```

### Eligibility Logic Flow

```mermaid
flowchart TD
    A[Company Profile Loaded] --> B{Any Factor Score = 0?}
    B -->|Yes| C[❌ Likely Not Eligible]
    B -->|No| D{Total Score < 50?}
    D -->|Yes| C
    D -->|No| E{All Gates Pass?}
    E -->|Yes| F[✅ Likely Eligible]
    E -->|No| G[⚠️ Review Required]
    
    style C fill:#ef4444,color:#fff
    style F fill:#22c55e,color:#fff
    style G fill:#f59e0b,color:#fff
```

---

## 2. Company Research Agent

### Overview
The Research Agent performs deep company research using Tavily AI search, generating structured reports with PDF export and email delivery.

### Architecture Diagram

```mermaid
graph LR
    subgraph Input["📝 User Input"]
        Form[Research Form]
        Examples[Example Companies]
    end

    subgraph ResearchEngine["🔬 Research Engine"]
        Orchestrator[Query Orchestrator]
        Q1[Company Queries]
        Q2[Industry Queries]
        Q3[Financial Queries]
        Q4[News Queries]
    end

    subgraph TavilySearch["🔍 Tavily API"]
        Search1[Search 1-4]
        Search2[Search 5-8]
        Search3[Search 9-12]
        Search4[Search 13-16]
    end

    subgraph Processing["⚙️ Processing"]
        Aggregator[Result Aggregator]
        Dedup[Deduplication]
        Formatter[Report Formatter]
    end

    subgraph Output["📤 Output Options"]
        Display[UI Display]
        PDF[PDF Generator]
        Email[Email Sender]
    end

    Form --> Orchestrator
    Examples --> Form
    
    Orchestrator --> Q1
    Orchestrator --> Q2
    Orchestrator --> Q3
    Orchestrator --> Q4
    
    Q1 --> Search1
    Q2 --> Search2
    Q3 --> Search3
    Q4 --> Search4
    
    Search1 --> Aggregator
    Search2 --> Aggregator
    Search3 --> Aggregator
    Search4 --> Aggregator
    
    Aggregator --> Dedup
    Dedup --> Formatter
    
    Formatter --> Display
    Formatter --> PDF
    PDF --> Email
```

### Query Categories (16 Total Queries)

```mermaid
graph TD
    subgraph Company["🏢 Company Overview (4)"]
        C1[Company + funding history]
        C2[Company + valuation]
        C3[Company + founding team]
        C4[Company + headquarters]
    end

    subgraph Industry["🏭 Industry (4)"]
        I1[Industry + market size]
        I2[Industry + trends 2024]
        I3[Industry + competitive landscape]
        I4[Industry + growth forecast]
    end

    subgraph Financial["💰 Financial (4)"]
        F1[Company + revenue]
        F2[Company + profitability]
        F3[Company + funding rounds]
        F4[Company + investors]
    end

    subgraph News["📰 Recent News (4)"]
        N1[Company + latest news]
        N2[Company + announcements]
        N3[Company + press release]
        N4[Company + CEO interview]
    end
```

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/research/company` | POST | Trigger 16-query research |
| `/api/research/pdf` | POST | Generate WeasyPrint PDF |
| `/api/research/email` | POST | Send PDF via Gmail SMTP |

---

## 3. Newsletter Subscribe System

### Overview
The Subscribe system sends professional HTML emails with portfolio intelligence, AI company news, and eligibility analysis.

### Architecture Diagram

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Tavily
    participant HuggingFace
    participant Mailer
    participant Gmail

    User->>Frontend: Click Subscribe
    Frontend->>Frontend: Select Frequency (Now/Weekly/Monthly)
    Frontend->>API: POST /api/eis/automation/send-email
    
    API->>API: Load Portfolio Companies
    
    loop For Each Company
        API->>Tavily: Search Company News
        Tavily-->>API: News Results
        API->>HuggingFace: Summarize News
        HuggingFace-->>API: AI Summary
    end
    
    API->>Tavily: Get Sector News
    Tavily-->>API: Tech/Healthcare/Fintech News
    
    API->>Mailer: Generate Newsletter HTML
    Mailer->>Mailer: Build 7 Sections
    Mailer-->>API: HTML + Plain Text
    
    API->>Gmail: Send via SMTP
    Gmail-->>User: Email Delivered
```

### Newsletter Sections

```mermaid
graph TD
    subgraph Newsletter["📧 Newsletter Email Structure"]
        H[Header: EIS Portfolio Intelligence]
        S1[Portfolio Summary]
        S2[Top Changes - 3 Companies]
        S3[🤖 AI Company Intelligence]
        S4[Watchlist - Review Required]
        S5[Full Portfolio Table]
        S6[Data Sources Used]
        S7[Next Scheduled Run]
        F[Footer]
    end

    H --> S1
    S1 --> S2
    S2 --> S3
    S3 --> S4
    S4 --> S5
    S5 --> S6
    S6 --> S7
    S7 --> F
```

### Frequency Options

| Frequency | Next Run Calculation |
|-----------|---------------------|
| **Weekly** | Next Monday 08:00 |
| **Monthly** | 1st of Next Month 08:00 |
| **Yearly** | January 1st 08:00 |
| **Now** | Immediate (Manual) |

### Email Content Per Company

```
┌─────────────────────────────────────────────────────────────┐
│ COMPANY NAME (00000000) — Likely Not Eligible (Score: 78)  │
│ 💰 Revenue: £45.6M | 🏢 Sector: Technology                  │
│ • Company Age score is 0/20                                 │
│ → Recommended: Remove from EIS candidate list               │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. AI Newsroom

### Overview
The AI Newsroom provides real-time company news using Tavily search with HuggingFace AI summarization.

### Architecture Diagram

```mermaid
graph TB
    subgraph Trigger["🎯 Trigger"]
        Button[AI Newsroom Button]
        Auto[Auto-refresh on Selection]
    end

    subgraph NewsEngine["📰 News Engine"]
        CompanyLookup[Get Company Name]
        SICCodes[Extract SIC Codes]
        QueryBuilder[Build Search Query]
    end

    subgraph TavilySearch["🔍 Tavily Search"]
        NewsQuery[Company + News + SIC]
        MaxResults[Max 5 Results]
    end

    subgraph AIProcessing["🤖 AI Processing"]
        ResearchAgent[Research Agent]
        EditorAgent[Editor Agent]
        Summarizer[HuggingFace Mistral]
    end

    subgraph Output["📋 Output"]
        NewsList[News Articles List]
        Summary[AI Summary]
        Sources[Source Citations]
        Relevance[Relevance Score]
    end

    Button --> CompanyLookup
    Auto --> CompanyLookup
    CompanyLookup --> SICCodes
    SICCodes --> QueryBuilder
    
    QueryBuilder --> NewsQuery
    NewsQuery --> MaxResults
    
    MaxResults --> ResearchAgent
    ResearchAgent --> EditorAgent
    EditorAgent --> Summarizer
    
    Summarizer --> Summary
    ResearchAgent --> NewsList
    NewsList --> Sources
    EditorAgent --> Relevance
```

### News Card Display

```mermaid
graph LR
    subgraph NewsCard["📰 News Card Component"]
        Title[Headline Title]
        Snippet[Content Snippet]
        Source[Source Domain]
        Link[Read More Link]
        Date[Publication Date]
    end

    subgraph AIInsight["🤖 AI Insight"]
        Summary[2-3 Sentence Summary]
        Impact[EIS Impact Analysis]
        Score[Relevance Score]
    end

    NewsCard --> AIInsight
```

### API Flow

| Step | Endpoint | Data |
|------|----------|------|
| 1 | `/api/eis/company/id/news` | Company Number |
| 2 | Internal | Tavily Search Query |
| 3 | Internal | HuggingFace Summarization |
| 4 | Response | News + AI Summary |

---

## 5. AI Daily News

### Overview
The AI Daily News feature provides sector-wide EIS market intelligence updated daily.

### Architecture Diagram

```mermaid
graph TB
    subgraph DailyNews["🗞️ AI Daily News"]
        Button[AI Daily News Button]
        Modal[News Modal Window]
    end

    subgraph SectorQueries["🏭 Sector Queries"]
        Tech[UK Technology Startup Funding]
        Health[UK Healthcare Biotech Funding]
        Fintech[UK Fintech Payments Investment]
        Clean[UK CleanTech Green Energy]
    end

    subgraph TavilyAPI["🔍 Tavily API"]
        Search[Parallel Searches]
        Results[Top 2-3 per Sector]
    end

    subgraph Processing["⚙️ Processing"]
        Filter[Date Filter - Recent]
        Dedupe[Remove Duplicates]
        Format[Format for Display]
    end

    subgraph Display["📱 Display"]
        SectorTabs[Sector Tabs]
        ArticleList[Article Cards]
        ReadMore[External Links]
    end

    Button --> Modal
    Modal --> SectorQueries
    
    Tech --> Search
    Health --> Search
    Fintech --> Search
    Clean --> Search
    
    Search --> Results
    Results --> Filter
    Filter --> Dedupe
    Dedupe --> Format
    
    Format --> SectorTabs
    SectorTabs --> ArticleList
    ArticleList --> ReadMore
```

### Sector Categories

```mermaid
graph LR
    subgraph Sectors["📊 EIS Qualifying Sectors"]
        S1["🖥️ Technology"]
        S2["🏥 Healthcare/Biotech"]
        S3["💳 Fintech"]
        S4["🌱 Clean Energy"]
    end

    subgraph Queries["🔍 Search Terms"]
        Q1[UK tech startup funding investment]
        Q2[UK healthcare biotech medtech startup]
        Q3[UK fintech digital banking payments]
        Q4[UK cleantech green energy funding]
    end

    S1 --> Q1
    S2 --> Q2
    S3 --> Q3
    S4 --> Q4
```

### News Display Format

```
┌─────────────────────────────────────────────────────────────┐
│ 📅 December 27, 2024                                        │
├─────────────────────────────────────────────────────────────┤
│ 🖥️ TECHNOLOGY                                               │
│ ─────────────────────────────────────────────────────────── │
│ UK AI Startup Raises £50M Series B                          │
│ The London-based AI company has secured funding...          │
│ 📰 TechCrunch | Read More →                                 │
├─────────────────────────────────────────────────────────────┤
│ 🏥 HEALTHCARE                                               │
│ ─────────────────────────────────────────────────────────── │
│ Biotech Firm Gets NHS Innovation Contract                   │
│ A Manchester biotech startup has won...                     │
│ 📰 The Guardian | Read More →                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack Summary

```mermaid
graph TB
    subgraph Frontend["Frontend Stack"]
        Next[Next.js 14]
        React[React 18]
        TS[TypeScript]
        Tailwind[Tailwind CSS]
        Framer[Framer Motion]
    end

    subgraph Backend["Backend Stack"]
        FastAPI[FastAPI]
        Python[Python 3.11+]
        Pandas[Pandas]
        HTTPX[HTTPX Async]
    end

    subgraph APIs["External APIs"]
        CH[Companies House]
        Tavily[Tavily Search]
        HF[HuggingFace]
        Gmail[Gmail SMTP]
    end

    subgraph Tools["Dev Tools"]
        Git[Git/GitHub]
        NPM[NPM]
        Conda[Conda]
        WeasyPrint[WeasyPrint]
    end

    Frontend --> Backend
    Backend --> APIs
```

---

## Environment Configuration

```env
# Companies House API
COMPANIES_HOUSE_API_KEY=xxxxxxxxxx

# Tavily AI Search
TAVILY_API_KEY=tvly-xxxxxxxxxx

# HuggingFace LLM
HF_API_KEY=hf_xxxxxxxxxx

# Gmail SMTP
GMAIL_ADDRESS=your@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

---

## Repository

**GitHub:** [nagasriramnani/Currency-Intelligence-Platform-V2](https://github.com/nagasriramnani/Currency-Intelligence-Platform-V2)

---

*Report Generated: December 27, 2024*  
*Version: 2.2.0*
