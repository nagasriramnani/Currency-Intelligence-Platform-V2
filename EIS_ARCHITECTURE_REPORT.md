# EIS Investment Scanner - Architecture Report

## Executive Summary

The **EIS Investment Scanner** is a comprehensive AI-powered platform for screening UK companies for Enterprise Investment Scheme (EIS) eligibility. This document provides detailed architecture diagrams and explanations for each major component.

---

## Table of Contents

1. [EIS Page - Complete System Architecture](#1-eis-page---complete-system-architecture)
2. [Company Research Agent](#2-company-research-agent)
3. [Newsletter Subscription Flow](#3-newsletter-subscription-flow)
4. [AI Newsroom](#4-ai-newsroom)
5. [AI Daily News](#5-ai-daily-news)

---

## 1. EIS Page - Complete System Architecture

### Overview
The EIS Page is the main dashboard for searching, analyzing, and managing UK companies for EIS eligibility assessment.

### Flow Diagram

```mermaid
flowchart TB
    subgraph User["👤 User Interface"]
        SearchBar[("🔍 Search Bar")]
        PortfolioTab["📁 Portfolio Tab"]
        SearchResults["📋 Search Results"]
        CompanyDetails["📊 Company Details Panel"]
    end

    subgraph Frontend["⚛️ Next.js Frontend"]
        EISPage["EIS Page Component"]
        SearchHandler["Search Handler"]
        ProfileLoader["Profile Loader"]
        PortfolioManager["Portfolio Manager"]
        ScoreGauge["Score Gauge Component"]
        StatsCards["Stats Cards Component"]
    end

    subgraph Backend["🐍 FastAPI Backend"]
        SearchAPI["/api/eis/search"]
        FullProfileAPI["/api/eis/company/{id}/full-profile"]
        EISHeuristics["EIS Heuristics Engine"]
        TavilyFinancial["Tavily Financial Research"]
    end

    subgraph External["🌐 External APIs"]
        CompaniesHouse["UK Companies House API"]
        TavilyAPI["Tavily Search API"]
    end

    subgraph DataFlow["📊 Data Processing"]
        CompanyProfile["Company Profile Data"]
        OfficersData["Officers & Directors"]
        PSCData["Persons of Significant Control"]
        FilingsData["Filing History"]
        ChargesData["Charges & Mortgages"]
    end

    %% User Flow
    SearchBar -->|"Enter company name"| SearchHandler
    SearchHandler -->|"GET request"| SearchAPI
    SearchAPI -->|"Search query"| CompaniesHouse
    CompaniesHouse -->|"Search results"| SearchAPI
    SearchAPI -->|"JSON response"| SearchResults

    %% Company Selection
    SearchResults -->|"Click company"| ProfileLoader
    ProfileLoader -->|"GET request"| FullProfileAPI

    %% Full Profile Fetching
    FullProfileAPI -->|"Parallel requests"| CompaniesHouse
    CompaniesHouse --> CompanyProfile
    CompaniesHouse --> OfficersData
    CompaniesHouse --> PSCData
    CompaniesHouse --> FilingsData
    CompaniesHouse --> ChargesData

    %% EIS Assessment
    CompanyProfile --> EISHeuristics
    OfficersData --> EISHeuristics
    FilingsData --> EISHeuristics
    EISHeuristics -->|"Score calculation"| FullProfileAPI

    %% Tavily Financial Fallback
    FullProfileAPI -->|"If no accounts data"| TavilyFinancial
    TavilyFinancial -->|"Search: company + revenue"| TavilyAPI
    TavilyAPI -->|"Financial data"| TavilyFinancial
    TavilyFinancial -->|"Parsed revenue"| FullProfileAPI

    %% Display
    FullProfileAPI -->|"Complete profile + EIS score"| CompanyDetails
    CompanyDetails --> ScoreGauge
    CompanyDetails --> StatsCards

    %% Portfolio
    CompanyDetails -->|"Add to Portfolio"| PortfolioManager
    PortfolioManager --> PortfolioTab

    style User fill:#e1f5fe
    style Frontend fill:#fff3e0
    style Backend fill:#e8f5e9
    style External fill:#fce4ec
    style DataFlow fill:#f3e5f5
```

### Key Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **EIS Page** | Next.js 14 + TypeScript | Main dashboard UI |
| **Search API** | FastAPI | Company name search |
| **Full Profile API** | FastAPI | Comprehensive company data |
| **EIS Heuristics** | Python | 0-100 eligibility scoring |
| **Tavily Financial** | Tavily API | Revenue lookup fallback |
| **Companies House** | External API | Official UK company data |

### EIS Scoring Breakdown

```mermaid
flowchart LR
    subgraph Scoring["EIS Score Calculation (0-100)"]
        Age["Company Age<br/>≤7 years: +20"]
        Status["Active Status<br/>+15"]
        SIC["Qualifying SIC<br/>+20"]
        Insolvency["No Insolvency<br/>+15"]
        Trades["No Excluded Trades<br/>+15"]
        RnD["R&D Intensive<br/>+15"]
    end

    subgraph Result["Final Result"]
        Score["Total Score"]
        Eligible["✅ Likely Eligible<br/>(score ≥ 50, no 0 factors)"]
        NotEligible["❌ Likely Not Eligible<br/>(any factor = 0 or score < 50)"]
    end

    Age --> Score
    Status --> Score
    SIC --> Score
    Insolvency --> Score
    Trades --> Score
    RnD --> Score

    Score -->|"≥50 & no zeros"| Eligible
    Score -->|"<50 OR any factor=0"| NotEligible

    style Eligible fill:#4caf50,color:#fff
    style NotEligible fill:#f44336,color:#fff
```

---

## 2. Company Research Agent

### Overview
The Research Agent performs deep-dive company research using Tavily AI, generating structured reports with PDF export and email delivery.

### Flow Diagram

```mermaid
flowchart TB
    subgraph Input["📝 User Input"]
        CompanyName["Company Name"]
        Industry["Industry/Sector"]
        ExampleBtn["Example Company Buttons"]
    end

    subgraph Frontend["⚛️ Research Page UI"]
        InputForm["Research Form"]
        ProgressIndicator["Research Progress<br/>(0-100%)"]
        ReportDisplay["Structured Report Display"]
        ActionButtons["PDF | Copy | Email Buttons"]
    end

    subgraph ResearchAPI["🔬 Research Endpoints"]
        StartResearch["/api/research/company<br/>POST"]
        GeneratePDF["/api/research/pdf<br/>POST"]
        SendEmail["/api/research/email<br/>POST"]
    end

    subgraph TavilyEngine["🤖 Tavily Research Engine"]
        QueryBuilder["Query Builder<br/>(16 queries)"]
        ParallelSearch["Parallel Search Execution"]
        ResultAggregator["Result Aggregator"]
    end

    subgraph Categories["📊 Research Categories"]
        Company["Company Overview<br/>(4 queries)"]
        Industry2["Industry Overview<br/>(4 queries)"]
        Financial["Financial Overview<br/>(4 queries)"]
        News["Recent News<br/>(4 queries)"]
    end

    subgraph Output["📄 Output Formats"]
        JSONReport["JSON Report<br/>(structured data)"]
        PDFFile["PDF Report<br/>(WeasyPrint)"]
        EmailDelivery["Email with PDF<br/>(Gmail SMTP)"]
    end

    %% Flow
    CompanyName --> InputForm
    Industry --> InputForm
    ExampleBtn --> InputForm
    InputForm -->|"Submit"| StartResearch
    StartResearch --> QueryBuilder

    QueryBuilder --> Company
    QueryBuilder --> Industry2
    QueryBuilder --> Financial
    QueryBuilder --> News

    Company --> ParallelSearch
    Industry2 --> ParallelSearch
    Financial --> ParallelSearch
    News --> ParallelSearch

    ParallelSearch -->|"Tavily API"| ResultAggregator
    ResultAggregator --> JSONReport
    JSONReport --> ReportDisplay
    ReportDisplay --> ProgressIndicator

    %% Actions
    ActionButtons -->|"Download PDF"| GeneratePDF
    GeneratePDF -->|"WeasyPrint"| PDFFile

    ActionButtons -->|"Send Email"| SendEmail
    SendEmail -->|"Gmail SMTP"| EmailDelivery

    style Input fill:#e3f2fd
    style TavilyEngine fill:#fff8e1
    style Categories fill:#f1f8e9
    style Output fill:#fce4ec
```

### Research Query Categories

| Category | Queries | Purpose |
|----------|---------|---------|
| **Company Overview** | Funding, valuation, team, headquarters | Core company information |
| **Industry Overview** | Market size, trends, competitors | Sector context |
| **Financial Overview** | Revenue, growth, profitability | Financial health |
| **Recent News** | Press releases, announcements | Latest updates |

### API Endpoints

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant R as /api/research/company
    participant T as Tavily API
    participant P as /api/research/pdf
    participant E as /api/research/email

    U->>F: Enter company name + industry
    F->>R: POST {company, industry}
    R->>T: 16 parallel search queries
    T-->>R: Aggregated results
    R-->>F: Structured report JSON
    F->>U: Display report sections

    U->>F: Click "Download PDF"
    F->>P: POST {report_data}
    P-->>F: PDF binary
    F->>U: Download PDF file

    U->>F: Click "Email Report"
    F->>E: POST {report, email}
    E-->>F: Success confirmation
```

---

## 3. Newsletter Subscription Flow

### Overview
Users can subscribe to receive AI-powered newsletter emails with portfolio updates, EIS assessments, and AI-generated company intelligence.

### Flow Diagram

```mermaid
flowchart TB
    subgraph Trigger["🔔 Subscription Trigger"]
        SubscribeBtn["Subscribe Button"]
        FrequencySelect["Frequency Selector<br/>(Weekly/Monthly/Yearly/Now)"]
        EmailInput["Email Address Input"]
    end

    subgraph Frontend["⚛️ Frontend Handler"]
        SubscribeModal["Subscribe Modal Dialog"]
        PortfolioData["Portfolio Companies Data"]
        LoadingState["Loading State"]
    end

    subgraph API["📡 Send Email Endpoint"]
        SendEmailAPI["/api/eis/automation/send-email<br/>POST"]
        CredentialsCheck["Gmail Credentials Check"]
        PortfolioProcessor["Portfolio Processor"]
    end

    subgraph AIProcessing["🤖 AI Processing"]
        ResearchAgent["Research Agent<br/>(Tavily)"]
        EditorAgent["Editor Agent<br/>(HuggingFace)"]
        MarketInsights["Market Insights Generator"]
        SectorNews["Sector News Fetcher"]
    end

    subgraph NewsletterGen["📧 Newsletter Generator"]
        Mailer["Professional Newsletter Generator"]
        HTMLTemplate["HTML Email Template"]
        PlainText["Plain Text Fallback"]
    end

    subgraph Sections["📑 Newsletter Sections"]
        Summary["Portfolio Summary"]
        TopChanges["Top Changes"]
        AIIntelligence["AI Company Intelligence"]
        Watchlist["Watchlist"]
        FullPortfolio["Full Portfolio Table"]
        DataSources["Data Sources"]
        NextRun["Next Scheduled Run"]
    end

    subgraph Delivery["📤 Email Delivery"]
        Gmail["Gmail SMTP<br/>(TLS/SSL)"]
        Recipient["Recipient Inbox"]
    end

    %% Flow
    SubscribeBtn --> SubscribeModal
    FrequencySelect --> SubscribeModal
    EmailInput --> SubscribeModal
    SubscribeModal -->|"Confirm"| SendEmailAPI

    SendEmailAPI --> CredentialsCheck
    CredentialsCheck -->|"Valid"| PortfolioProcessor
    PortfolioData --> PortfolioProcessor

    PortfolioProcessor -->|"For each company"| ResearchAgent
    ResearchAgent -->|"Tavily search"| EditorAgent
    EditorAgent -->|"HuggingFace summarize"| MarketInsights
    PortfolioProcessor --> SectorNews

    MarketInsights --> Mailer
    SectorNews --> Mailer
    PortfolioProcessor --> Mailer

    Mailer --> HTMLTemplate
    Mailer --> PlainText

    HTMLTemplate --> Summary
    HTMLTemplate --> TopChanges
    HTMLTemplate --> AIIntelligence
    HTMLTemplate --> Watchlist
    HTMLTemplate --> FullPortfolio
    HTMLTemplate --> DataSources
    HTMLTemplate --> NextRun

    HTMLTemplate --> Gmail
    PlainText --> Gmail
    Gmail --> Recipient

    style Trigger fill:#e8eaf6
    style AIProcessing fill:#fff3e0
    style NewsletterGen fill:#e8f5e9
    style Delivery fill:#ffebee
```

### Frequency Options

| Frequency | Next Scheduled Run |
|-----------|-------------------|
| **Weekly** | Every Monday at 08:00 |
| **Monthly** | 1st of each month at 08:00 |
| **Yearly** | January 1st at 08:00 |
| **Now** | Immediate (on-demand) |

### Newsletter Email Structure

```
┌────────────────────────────────────────────────────┐
│  EIS Portfolio Intelligence — Weekly Snapshot      │
│  Week of December 27, 2024                         │
├────────────────────────────────────────────────────┤
│  PORTFOLIO SUMMARY                                 │
│  • Companies reviewed: 7                           │
│  • Likely eligible: 5                              │
│  • Review required: 1                              │
│  • Likely ineligible: 1                            │
├────────────────────────────────────────────────────┤
│  TOP CHANGES (This Period)                         │
│  1) Company A — Likely Eligible (Score: 85/100)    │
│     💰 Revenue: £2.3M | 🏢 Sector: Technology      │
│     → Recommended: HMRC Advance Assurance check    │
├────────────────────────────────────────────────────┤
│  🤖 AI COMPANY INTELLIGENCE                        │
│  ┌─────────────────────────────────────────────┐   │
│  │ Company B (12345678)              78/100    │   │
│  │ 💰 Revenue: £1.5M | 📊 Status: Eligible     │   │
│  │ Recent funding round announced...           │   │
│  │ 📰 Sources: TechCrunch                      │   │
│  └─────────────────────────────────────────────┘   │
├────────────────────────────────────────────────────┤
│  WATCHLIST (Review Required)                       │
│  • Sector/SIC mismatch                             │
│  • Age outside standard EIS window                 │
├────────────────────────────────────────────────────┤
│  FULL PORTFOLIO                                    │
│  Company  | Score | Status  | Sector              │
│  ─────────┼───────┼─────────┼────────             │
│  Comp A   | 85    | Eligible| Tech                │
│  Comp B   | 78    | Eligible| Healthcare          │
├────────────────────────────────────────────────────┤
│  DATA SOURCES: Companies House, Tavily, HuggingFace│
│  Next Scheduled Run: Monday, Dec 30, 2024 at 08:00 │
└────────────────────────────────────────────────────┘
```

---

## 4. AI Newsroom

### Overview
The AI Newsroom provides real-time, AI-curated news for individual companies using Tavily search and HuggingFace summarization.

### Flow Diagram

```mermaid
flowchart TB
    subgraph Trigger["🎯 Trigger"]
        NewsButton["AI Newsroom Button<br/>(in Company Details)"]
        CompanyContext["Company Name + SIC Codes"]
    end

    subgraph API["📡 News Endpoint"]
        NewsAPI["/api/eis/company/{id}/news<br/>GET"]
        CompanyLookup["Company Name Lookup"]
    end

    subgraph Research["🔍 Research Agent"]
        TavilySearch["Tavily Search<br/>(max 5 results)"]
        QueryGeneration["Query: Company + Sector + Funding"]
    end

    subgraph Editor["✍️ Editor Agent"]
        HuggingFace["HuggingFace API<br/>(Mistral 7B)"]
        Summarizer["News Summarizer"]
        RelevanceFilter["Relevance Filter"]
    end

    subgraph Output["📰 News Output"]
        NewsSummary["AI Summary<br/>(2-3 sentences)"]
        Sources["Source URLs"]
        Relevance["Relevance Score"]
        Timestamp["Last Updated"]
    end

    subgraph Display["🖥️ UI Display"]
        NewsModal["News Modal Dialog"]
        LoadingSpinner["Loading Animation"]
        NewsCards["Formatted News Cards"]
    end

    %% Flow
    NewsButton --> NewsAPI
    CompanyContext --> NewsAPI
    NewsAPI --> CompanyLookup
    CompanyLookup --> QueryGeneration
    QueryGeneration --> TavilySearch
    TavilySearch -->|"Raw results"| Summarizer
    Summarizer --> HuggingFace
    HuggingFace --> RelevanceFilter
    RelevanceFilter --> NewsSummary
    RelevanceFilter --> Sources
    RelevanceFilter --> Relevance

    NewsSummary --> NewsCards
    Sources --> NewsCards
    Timestamp --> NewsCards
    LoadingSpinner --> NewsModal
    NewsCards --> NewsModal

    style Trigger fill:#e1f5fe
    style Research fill:#fff8e1
    style Editor fill:#f3e5f5
    style Output fill:#e8f5e9
```

### News Processing Pipeline

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant N as News API
    participant R as Research Agent
    participant T as Tavily
    participant E as Editor Agent
    participant H as HuggingFace

    U->>F: Click "AI Newsroom"
    F->>N: GET /api/eis/company/{id}/news
    N->>R: Get company news
    R->>T: Search: "Company X funding investment UK"
    T-->>R: 5 search results
    R->>E: Summarize results for Company X
    E->>H: Generate summary (Mistral 7B)
    H-->>E: AI-generated summary
    E-->>N: Filtered, relevant summary
    N-->>F: {summary, sources, relevance}
    F->>U: Display news modal
```

---

## 5. AI Daily News

### Overview
The AI Daily News feature provides sector-wide market intelligence across UK startup sectors (Technology, Healthcare, Fintech, Clean Energy).

### Flow Diagram

```mermaid
flowchart TB
    subgraph Trigger["📅 Daily News Trigger"]
        DailyNewsBtn["AI Daily News Button<br/>(Header)"]
        ScheduledJob["Scheduled Job<br/>(optional)"]
    end

    subgraph API["📡 Daily News Endpoint"]
        DailyNewsAPI["/api/eis/daily-news<br/>GET"]
        SectorQueries["Sector Query Builder"]
    end

    subgraph Sectors["🏢 UK Startup Sectors"]
        Tech["Technology<br/>'UK tech startup funding 2024'"]
        Healthcare["Healthcare<br/>'UK biotech medtech startup'"]
        Fintech["Fintech<br/>'UK fintech digital banking'"]
        CleanEnergy["Clean Energy<br/>'UK cleantech green tech'"]
    end

    subgraph TavilySearch["🔍 Tavily Multi-Search"]
        ParallelQueries["4 Parallel Searches"]
        ResultsPerSector["2 Results per Sector"]
    end

    subgraph Processing["⚙️ Result Processing"]
        URLParser["URL/Domain Parser"]
        ContentTrimmer["Content Trimmer<br/>(200 chars)"]
        Deduplication["Deduplication"]
    end

    subgraph Output["📊 Aggregated Output"]
        SectorNews["Sector News Array"]
        Headlines["Headlines"]
        Summaries["Content Summaries"]
        SourceLinks["Source Links"]
    end

    subgraph Display["🖥️ UI Display"]
        DailyNewsPage["Daily News Page"]
        SectorCards["Sector Cards"]
        NewsTimeline["News Timeline"]
    end

    %% Flow
    DailyNewsBtn --> DailyNewsAPI
    ScheduledJob --> DailyNewsAPI
    DailyNewsAPI --> SectorQueries

    SectorQueries --> Tech
    SectorQueries --> Healthcare
    SectorQueries --> Fintech
    SectorQueries --> CleanEnergy

    Tech --> ParallelQueries
    Healthcare --> ParallelQueries
    Fintech --> ParallelQueries
    CleanEnergy --> ParallelQueries

    ParallelQueries --> ResultsPerSector
    ResultsPerSector --> URLParser
    URLParser --> ContentTrimmer
    ContentTrimmer --> Deduplication
    Deduplication --> SectorNews

    SectorNews --> Headlines
    SectorNews --> Summaries
    SectorNews --> SourceLinks

    Headlines --> SectorCards
    Summaries --> SectorCards
    SourceLinks --> SectorCards
    SectorCards --> DailyNewsPage
    SectorCards --> NewsTimeline

    style Trigger fill:#e8eaf6
    style Sectors fill:#e3f2fd
    style TavilySearch fill:#fff8e1
    style Output fill:#e8f5e9
```

### Daily News Data Structure

```json
{
  "sectors": [
    {
      "name": "Technology",
      "news": [
        {
          "title": "UK Tech Startup Raises £10M Series A",
          "content": "Summary of the article...",
          "source": "techcrunch.com",
          "url": "https://..."
        }
      ]
    },
    {
      "name": "Healthcare",
      "news": [...]
    },
    {
      "name": "Fintech",
      "news": [...]
    },
    {
      "name": "Clean Energy",
      "news": [...]
    }
  ],
  "generated_at": "2024-12-27T19:00:00Z"
}
```

### Sector Query Templates

| Sector | Search Query |
|--------|-------------|
| Technology | `UK technology startup funding investment Series A 2024 2025` |
| Healthcare | `UK healthcare biotech medtech startup funding 2024 2025` |
| Fintech | `UK fintech digital banking payments startup investment 2024 2025` |
| Clean Energy | `UK cleantech green energy clean technology funding 2024 2025` |

---

## Technology Stack Summary

```mermaid
flowchart LR
    subgraph Frontend["Frontend"]
        Next["Next.js 14"]
        React["React 18"]
        TS["TypeScript"]
        Tailwind["Tailwind CSS"]
        Framer["Framer Motion"]
    end

    subgraph Backend["Backend"]
        FastAPI["FastAPI"]
        Python["Python 3.11"]
        Pandas["Pandas"]
    end

    subgraph AI["AI/ML"]
        Tavily["Tavily API"]
        HF["HuggingFace<br/>(Mistral 7B)"]
        XGBoost["XGBoost"]
    end

    subgraph External["External APIs"]
        CH["Companies House"]
        Gmail["Gmail SMTP"]
        Slack["Slack Webhooks"]
    end

    Frontend --> Backend
    Backend --> AI
    Backend --> External

    style Frontend fill:#61dafb
    style Backend fill:#3572A5
    style AI fill:#ff6b6b
    style External fill:#2ecc71
```

---

## Environment Variables Required

```env
# Core APIs
COMPANIES_HOUSE_API_KEY=your_key
TAVILY_API_KEY=tvly-xxxxxxxxxx
HF_API_KEY=hf_xxxxxxxxxx

# Email
GMAIL_ADDRESS=your@gmail.com
GMAIL_APP_PASSWORD=app_password

# Optional
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

---

*Report Generated: December 27, 2024*  
*Version: 2.2.0*
