# EIS Investment Scanner - Architecture Documentation

> **Sapphire Intelligence Platform** — Enterprise Investment Scheme Analysis System  
> *Last Updated: December 27, 2024*

---

## Table of Contents

1. [EIS Page Complete Workflow](#1-eis-page-complete-workflow)
2. [Company Research Agent](#2-company-research-agent)
3. [Subscribe & Newsletter System](#3-subscribe--newsletter-system)
4. [AI Newsroom](#4-ai-newsroom)
5. [AI Daily News](#5-ai-daily-news)

---

## 1. EIS Page Complete Workflow

### Overview

The EIS Investment Scanner page is the main interface for screening UK companies for Enterprise Investment Scheme eligibility. It combines real-time Companies House data with AI-powered analysis.

### Architecture Diagram

```mermaid
flowchart TB
    subgraph Frontend["🖥️ Next.js Frontend (localhost:3000/eis)"]
        UI[EIS Dashboard UI]
        SearchBar[Search Bar]
        Portfolio[Portfolio Tab]
        SearchResults[Search Results Tab]
        CompanyDetails[Company Details Panel]
        StatsGrid[Stats Grid: Directors, PSCs, Age, Revenue]
        EligibilityGates[Eligibility Gates Display]
        ScoreBreakdown[Score Breakdown 0-100]
    end

    subgraph Backend["⚙️ FastAPI Backend (localhost:8000)"]
        API["/api/eis/..."]
        SearchAPI["/api/eis/search"]
        ProfileAPI["/api/eis/company/{id}/full-profile"]
        NewsAPI["/api/eis/company/{id}/news"]
        EISEngine[EIS Heuristics Engine]
        TavilyFinance[Tavily Financial Lookup]
    end

    subgraph External["🌐 External APIs"]
        CH[Companies House API]
        Tavily[Tavily News API]
        HF[HuggingFace API]
    end

    subgraph DataFlow["📊 Data Processing"]
        ProfileData[Company Profile]
        Officers[Officers/Directors]
        PSCs[PSCs - Significant Control]
        Charges[Charges/Mortgages]
        Filings[Filing History]
        Accounts[Accounts Data]
    end

    %% User Flow
    UI --> SearchBar
    SearchBar -->|"Company Name/Number"| SearchAPI
    SearchAPI --> CH
    CH -->|"Search Results"| SearchResults
    
    SearchResults -->|"Select Company"| ProfileAPI
    ProfileAPI --> CH
    CH --> ProfileData
    CH --> Officers
    CH --> PSCs
    CH --> Charges
    CH --> Filings
    
    ProfileData --> EISEngine
    Officers --> EISEngine
    PSCs --> EISEngine
    Filings --> EISEngine
    
    EISEngine -->|"Score 0-100"| CompanyDetails
    EISEngine -->|"Factors"| ScoreBreakdown
    EISEngine -->|"Gates"| EligibilityGates
    
    %% Revenue Lookup
    Accounts -->|"If empty"| TavilyFinance
    TavilyFinance --> Tavily
    Tavily -->|"Revenue Data"| StatsGrid
    
    %% Portfolio
    CompanyDetails -->|"Add to Portfolio"| Portfolio
    Portfolio -->|"Save Locally"| UI

    style Frontend fill:#1e293b,stroke:#3b82f6,color:#fff
    style Backend fill:#0f172a,stroke:#10b981,color:#fff
    style External fill:#18181b,stroke:#f59e0b,color:#fff
```

### Key Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Search Bar** | React + Debounce | Real-time company search |
| **Company Profile** | Companies House API | Full company data |
| **EIS Engine** | Python Heuristics | 0-100 eligibility scoring |
| **Stats Grid** | React Cards | Directors, PSCs, Age, Revenue |
| **Eligibility Gates** | Visual Indicators | Pass/Fail for key criteria |
| **Score Breakdown** | Progress Bars | Factor-by-factor scoring |

### Plugins & Libraries Used

| Library | Version | Purpose |
|---------|---------|---------|
| `next` | 14.x | React framework |
| `framer-motion` | 10.x | Animations |
| `lucide-react` | latest | Icons |
| `tailwindcss` | 3.x | Styling |
| `fastapi` | 0.100+ | Python API |
| `tavily-python` | 0.3+ | News search |
| `huggingface-hub` | 0.19+ | AI summarization |

### Eligibility Scoring Logic

```mermaid
flowchart LR
    subgraph Factors["Score Factors (0-100)"]
        F1[Company Age<br/>≤7 years = +20]
        F2[Company Status<br/>Active = +15]
        F3[SIC Codes<br/>Eligible = +20]
        F4[Insolvency<br/>None = +15]
        F5[Excluded Trades<br/>None = +15]
        F6[R&D/KI<br/>Yes = +15]
    end

    subgraph Logic["Eligibility Logic"]
        Check{Any Factor = 0?}
        Score{Total < 50?}
        Eligible[✅ Likely Eligible]
        NotEligible[❌ Likely Not Eligible]
    end

    F1 --> Check
    F2 --> Check
    F3 --> Check
    F4 --> Check
    F5 --> Check
    F6 --> Check
    
    Check -->|Yes| NotEligible
    Check -->|No| Score
    Score -->|Yes| NotEligible
    Score -->|No| Eligible

    style Eligible fill:#10b981,color:#fff
    style NotEligible fill:#ef4444,color:#fff
```

---

## 2. Company Research Agent

### Overview

The Research Agent performs deep-dive company research using Tavily AI search, generating comprehensive reports with PDF export and email delivery.

### Architecture Diagram

```mermaid
flowchart TB
    subgraph UI["🖥️ Research Page (/research)"]
        Form[Company Input Form]
        Examples[Example Companies<br/>Spotify, Revolut, Stripe, Notion]
        Progress[Research Progress Indicator]
        Report[Structured Report Display]
        Actions[Copy | PDF | Email]
    end

    subgraph Backend["⚙️ Research API"]
        ResearchEndpoint["/api/research/company"]
        PDFEndpoint["/api/research/pdf"]
        EmailEndpoint["/api/research/email"]
        Researcher[CompanyResearcher Class]
    end

    subgraph Tavily["🔍 Tavily AI Search"]
        Q1[Company Overview Queries<br/>4 queries]
        Q2[Industry Analysis Queries<br/>4 queries]
        Q3[Financial Data Queries<br/>4 queries]
        Q4[Recent News Queries<br/>4 queries]
    end

    subgraph Output["📄 Output Generation"]
        PDFGen[WeasyPrint PDF Generator]
        EmailSend[Gmail SMTP Sender]
        JSONReport[JSON Report Structure]
    end

    %% Flow
    Form -->|"Company Name + Industry"| ResearchEndpoint
    Examples -->|"Quick Fill"| Form
    
    ResearchEndpoint --> Researcher
    Researcher -->|"16 Parallel Queries"| Tavily
    
    Tavily --> Q1
    Tavily --> Q2
    Tavily --> Q3
    Tavily --> Q4
    
    Q1 -->|"Aggregate"| JSONReport
    Q2 -->|"Aggregate"| JSONReport
    Q3 -->|"Aggregate"| JSONReport
    Q4 -->|"Aggregate"| JSONReport
    
    JSONReport --> Progress
    Progress --> Report
    Report --> Actions
    
    Actions -->|"Download PDF"| PDFEndpoint
    Actions -->|"Send Email"| EmailEndpoint
    
    PDFEndpoint --> PDFGen
    EmailEndpoint --> EmailSend
    EmailSend -->|"PDF Attachment"| User((📧 User Email))

    style UI fill:#1e293b,stroke:#3b82f6,color:#fff
    style Backend fill:#0f172a,stroke:#10b981,color:#fff
    style Tavily fill:#18181b,stroke:#a855f7,color:#fff
    style Output fill:#18181b,stroke:#f59e0b,color:#fff
```

### Research Query Categories

| Category | Queries | Example |
|----------|---------|---------|
| **Company Overview** | 4 | "Spotify funding history valuation headquarters" |
| **Industry Analysis** | 4 | "Music streaming market size trends competitors" |
| **Financial Data** | 4 | "Spotify revenue growth profitability 2024" |
| **Recent News** | 4 | "Spotify latest news announcements 2024" |

### Report Structure

```mermaid
flowchart LR
    subgraph Report["📊 Research Report"]
        H[Header: Company + Date]
        S1[1. Company Overview]
        S2[2. Industry Analysis]
        S3[3. Financial Overview]
        S4[4. Recent News]
        M[Metadata: Sources, Query Count]
    end

    H --> S1 --> S2 --> S3 --> S4 --> M

    style Report fill:#1e293b,stroke:#3b82f6,color:#fff
```

---

## 3. Subscribe & Newsletter System

### Overview

The Subscribe system allows users to receive periodic EIS portfolio updates via email with AI-generated company intelligence.

### Architecture Diagram

```mermaid
flowchart TB
    subgraph Frontend["🖥️ Subscribe Modal"]
        SubBtn[Subscribe Button]
        Modal[Subscription Modal]
        FreqSelect[Frequency Selector<br/>Weekly | Monthly | Yearly | Now]
        EmailInput[Email Address Input]
        SendBtn[Send Newsletter]
    end

    subgraph Backend["⚙️ Newsletter API"]
        SendEmail["/api/eis/automation/send-email"]
        Mailer[ProfessionalNewsletterGenerator]
        Writer[EISWriter]
    end

    subgraph DataSources["📊 Data Sources"]
        Portfolio[Portfolio Companies]
        ScanHistory[Scan History]
        CH[Companies House]
        TavilyNews[Tavily News Search]
        HFSummary[HuggingFace Summarizer]
    end

    subgraph EmailGen["📧 Email Generation"]
        HTML[HTML Template]
        PlainText[Plain Text Fallback]
        Subject[Dynamic Subject Line]
    end

    subgraph Sections["📄 Newsletter Sections"]
        S1[Portfolio Summary]
        S2[Top Changes + Revenue]
        S3[🤖 AI Company Intelligence]
        S4[Watchlist]
        S5[Full Portfolio Table]
        S6[Data Sources]
        S7[Next Scheduled Run]
    end

    %% Flow
    SubBtn --> Modal
    Modal --> FreqSelect
    Modal --> EmailInput
    FreqSelect --> SendBtn
    EmailInput --> SendBtn
    
    SendBtn -->|"POST"| SendEmail
    
    SendEmail --> Portfolio
    SendEmail --> ScanHistory
    
    Portfolio -->|"Company Data"| CH
    Portfolio -->|"News Search"| TavilyNews
    TavilyNews -->|"Summarize"| HFSummary
    
    CH --> Writer
    HFSummary --> Writer
    
    Writer --> Mailer
    Mailer --> HTML
    Mailer --> PlainText
    Mailer --> Subject
    
    HTML --> S1
    HTML --> S2
    HTML --> S3
    HTML --> S4
    HTML --> S5
    HTML --> S6
    HTML --> S7
    
    S7 -->|"SMTP"| Gmail((📧 Gmail))
    Gmail --> User((👤 Recipient))

    style Frontend fill:#1e293b,stroke:#3b82f6,color:#fff
    style Backend fill:#0f172a,stroke:#10b981,color:#fff
    style DataSources fill:#18181b,stroke:#a855f7,color:#fff
    style EmailGen fill:#18181b,stroke:#f59e0b,color:#fff
```

### Newsletter Content Flow

```mermaid
flowchart LR
    subgraph Input["Input Data"]
        Companies[Portfolio Companies]
        Frequency[Selected Frequency]
    end

    subgraph Processing["Processing"]
        Lookup[Companies House Lookup]
        News[Tavily News Fetch]
        Eligibility[Zero-Score Check]
        Revenue[Revenue Lookup]
    end

    subgraph Output["Email Output"]
        Header[EIS Portfolio Intelligence<br/>Weekly Snapshot - Date]
        Summary[📊 X companies, Y eligible]
        TopChanges[Top 3 with Revenue + Status]
        AINews[🤖 AI Company News]
        Table[Full Portfolio Table]
    end

    Companies --> Lookup
    Companies --> News
    Lookup --> Eligibility
    Lookup --> Revenue
    News --> AINews
    
    Eligibility --> TopChanges
    Revenue --> TopChanges
    
    Frequency --> Header
    Header --> Summary --> TopChanges --> AINews --> Table

    style Input fill:#1e293b,stroke:#3b82f6,color:#fff
    style Processing fill:#0f172a,stroke:#10b981,color:#fff
    style Output fill:#18181b,stroke:#f59e0b,color:#fff
```

### Frequency Options

| Frequency | Next Run Calculation |
|-----------|---------------------|
| **Weekly** | Next Monday 08:00 |
| **Monthly** | 1st of next month 08:00 |
| **Yearly** | January 1st 08:00 |
| **Now** | Immediate send |

---

## 4. AI Newsroom

### Overview

The AI Newsroom provides real-time news for individual companies using Tavily search with HuggingFace AI summarization.

### Architecture Diagram

```mermaid
flowchart TB
    subgraph UI["🖥️ AI Newsroom Button"]
        NewsBtn[🤖 AI Newsroom Button]
        NewsPanel[News Panel Overlay]
        NewsList[News Items List]
        Summary[AI-Generated Summary]
    end

    subgraph Backend["⚙️ News API"]
        NewsEndpoint["/api/eis/company/{id}/news"]
        ResearchAgent[ResearchAgent Class]
        EditorAgent[EditorAgent Class]
    end

    subgraph Tavily["🔍 Tavily Search"]
        Query[Company + SIC Codes Query]
        Results[Top 5 News Results]
    end

    subgraph HuggingFace["🤖 HuggingFace (Mistral 7B)"]
        Summarizer[News Summarizer]
        Relevance[Relevance Checker]
    end

    subgraph Output["📰 News Output"]
        Headlines[News Headlines]
        Summaries[AI Summaries]
        Sources[Source Links]
        Timestamp[Last Updated]
    end

    %% Flow
    NewsBtn -->|"Click"| NewsEndpoint
    NewsEndpoint --> ResearchAgent
    
    ResearchAgent -->|"Search Query"| Query
    Query --> Tavily
    Tavily --> Results
    
    Results --> EditorAgent
    EditorAgent --> Summarizer
    Summarizer --> Relevance
    
    Relevance -->|"Relevant News"| NewsPanel
    
    NewsPanel --> Headlines
    NewsPanel --> Summaries
    NewsPanel --> Sources
    NewsPanel --> Timestamp
    
    Headlines --> NewsList
    Summaries --> Summary

    style UI fill:#1e293b,stroke:#3b82f6,color:#fff
    style Backend fill:#0f172a,stroke:#10b981,color:#fff
    style Tavily fill:#18181b,stroke:#a855f7,color:#fff
    style HuggingFace fill:#18181b,stroke:#ec4899,color:#fff
    style Output fill:#18181b,stroke:#f59e0b,color:#fff
```

### News Processing Pipeline

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Tavily
    participant HuggingFace

    User->>Frontend: Click AI Newsroom
    Frontend->>API: GET /api/eis/company/{id}/news
    API->>Tavily: Search(company_name + SIC codes)
    Tavily-->>API: Raw Results (5 items)
    
    loop For each result
        API->>HuggingFace: Summarize(content)
        HuggingFace-->>API: AI Summary
        API->>HuggingFace: Check Relevance(summary)
        HuggingFace-->>API: is_relevant: true/false
    end
    
    API-->>Frontend: Filtered & Summarized News
    Frontend-->>User: Display News Panel
```

---

## 5. AI Daily News

### Overview

AI Daily News provides sector-level market intelligence with the latest funding, investment, and startup news across EIS-relevant sectors.

### Architecture Diagram

```mermaid
flowchart TB
    subgraph UI["🖥️ AI Daily News Page"]
        DailyBtn[✨ AI Daily News Button]
        NewsPage[Daily News Page]
        SectorTabs[Sector Tabs:<br/>Technology | Healthcare | Fintech | Clean Energy]
        NewsFeed[News Feed]
        Filters[Date & Relevance Filters]
    end

    subgraph Backend["⚙️ Daily News API"]
        DailyEndpoint["/api/eis/daily-news"]
        SectorQueries[Sector-Specific Queries]
    end

    subgraph Tavily["🔍 Tavily Sector Search"]
        TechQ[Tech: UK startup funding 2024]
        HealthQ[Healthcare: biotech medtech UK]
        FintechQ[Fintech: digital banking payments]
        CleanQ[Clean Energy: cleantech green]
    end

    subgraph Processing["📊 Processing"]
        Aggregate[Aggregate Results]
        Dedupe[Deduplicate]
        Sort[Sort by Date/Relevance]
        Format[Format for Display]
    end

    subgraph Output["📰 News Display"]
        Card1[News Card: Title + Summary]
        Card2[Source Badge + Link]
        Card3[Sector Tag]
        Card4[Published Date]
    end

    %% Flow
    DailyBtn --> NewsPage
    NewsPage --> SectorTabs
    SectorTabs --> DailyEndpoint
    
    DailyEndpoint --> SectorQueries
    SectorQueries --> TechQ
    SectorQueries --> HealthQ
    SectorQueries --> FintechQ
    SectorQueries --> CleanQ
    
    TechQ --> Tavily
    HealthQ --> Tavily
    FintechQ --> Tavily
    CleanQ --> Tavily
    
    Tavily --> Aggregate
    Aggregate --> Dedupe
    Dedupe --> Sort
    Sort --> Format
    
    Format --> NewsFeed
    NewsFeed --> Card1
    NewsFeed --> Card2
    NewsFeed --> Card3
    NewsFeed --> Card4
    
    Filters --> Sort

    style UI fill:#1e293b,stroke:#3b82f6,color:#fff
    style Backend fill:#0f172a,stroke:#10b981,color:#fff
    style Tavily fill:#18181b,stroke:#a855f7,color:#fff
    style Processing fill:#18181b,stroke:#10b981,color:#fff
    style Output fill:#18181b,stroke:#f59e0b,color:#fff
```

### Sector Query Configuration

| Sector | Search Query | Focus |
|--------|--------------|-------|
| **Technology** | UK technology startup funding investment Series A 2024 | Software, AI, SaaS |
| **Healthcare** | UK healthcare biotech medtech startup funding | Diagnostics, Therapeutics |
| **Fintech** | UK fintech digital banking payments startup investment | Payments, InsurTech |
| **Clean Energy** | UK cleantech green energy clean technology funding | Renewables, Battery |

### Data Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Tavily

    User->>Frontend: Open AI Daily News
    Frontend->>API: GET /api/eis/daily-news
    
    par Parallel Sector Searches
        API->>Tavily: Search(Technology Query)
        API->>Tavily: Search(Healthcare Query)
        API->>Tavily: Search(Fintech Query)
        API->>Tavily: Search(Clean Energy Query)
    end
    
    Tavily-->>API: Tech Results
    Tavily-->>API: Healthcare Results
    Tavily-->>API: Fintech Results
    Tavily-->>API: Clean Energy Results
    
    API->>API: Aggregate & Deduplicate
    API->>API: Sort by Date
    API-->>Frontend: Formatted News Feed
    Frontend-->>User: Display by Sector
```

---

## Complete System Architecture

```mermaid
flowchart TB
    subgraph User["👤 User"]
        Browser[Web Browser]
    end

    subgraph Frontend["🖥️ Next.js Frontend :3000"]
        Dashboard[Currency Dashboard]
        EISPage[EIS Investment Scanner]
        ResearchPage[Research Agent]
        DailyNews[AI Daily News]
    end

    subgraph Backend["⚙️ FastAPI Backend :8000"]
        EISAPI[EIS APIs]
        ResearchAPI[Research APIs]
        NewsAPI[News APIs]
        AutomationAPI[Automation APIs]
    end

    subgraph Services["🔧 Backend Services"]
        EISEngine[EIS Heuristics]
        ResearcherSvc[CompanyResearcher]
        EditorSvc[EditorAgent]
        MailerSvc[NewsletterGenerator]
        PDFSvc[PDFGenerator]
    end

    subgraph External["🌐 External APIs"]
        CH[Companies House]
        Tavily[Tavily AI]
        HF[HuggingFace]
        Gmail[Gmail SMTP]
        Slack[Slack]
    end

    Browser --> Frontend
    Frontend --> Backend
    
    EISAPI --> Services
    ResearchAPI --> Services
    NewsAPI --> Services
    AutomationAPI --> Services
    
    Services --> External

    style User fill:#374151,stroke:#9ca3af,color:#fff
    style Frontend fill:#1e293b,stroke:#3b82f6,color:#fff
    style Backend fill:#0f172a,stroke:#10b981,color:#fff
    style Services fill:#18181b,stroke:#a855f7,color:#fff
    style External fill:#18181b,stroke:#f59e0b,color:#fff
```

---

## Environment Variables Required

```env
# Companies House API
COMPANIES_HOUSE_API_KEY=your_api_key

# Tavily AI Search
TAVILY_API_KEY=tvly-xxxxxxxxxxxx

# HuggingFace (Mistral 7B)
HF_API_KEY=hf_xxxxxxxxxxxx

# Gmail SMTP
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password

# Slack (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

---

*Generated: December 27, 2024*  
*Sapphire Intelligence Platform v2.2.0*
