# EIS Investment Scanner - Architecture Documentation

## Complete System Architecture with Mermaid Diagrams

---

## 1. EIS Investment Scanner - Complete Page Workflow

This diagram shows how the entire EIS Investment Scanner page works, from search to portfolio management.

```mermaid
flowchart TB
    subgraph Frontend["🖥️ Frontend (Next.js 14)"]
        UI[EIS Page<br/>page.tsx]
        Search[Search Input]
        Results[Search Results Grid]
        Details[Company Details Panel]
        Portfolio[Portfolio Tab]
        Stats[Stats Grid<br/>Directors/PSCs/Age/Revenue]
        Gates[Eligibility Gates Display]
        Breakdown[Score Breakdown]
    end

    subgraph Backend["⚙️ Backend (FastAPI)"]
        SearchAPI["/api/eis/search"]
        ProfileAPI["/api/eis/company/{id}/full-profile"]
        EISEngine[EIS Heuristics Engine<br/>eis_heuristics.py]
        TavilyFinance[Tavily Financial Research]
    end

    subgraph External["🌐 External APIs"]
        CH[Companies House API]
        Tavily[Tavily API]
    end

    subgraph Components["🧩 UI Components"]
        ScoreGauge[Score Gauge<br/>/100 scale]
        Badge[Eligibility Badge<br/>Green/Red]
        StatsCard[Stats Cards x5]
    end

    %% User Flow
    User([👤 User]) --> Search
    Search -->|"Enter company name"| SearchAPI
    SearchAPI -->|"Search query"| CH
    CH -->|"Company list"| Results
    Results -->|"Click company"| ProfileAPI
    
    %% Profile Loading
    ProfileAPI --> CH
    CH -->|"Full profile data"| EISEngine
    EISEngine -->|"Calculate score"| ProfileAPI
    ProfileAPI -->|"Check accounts"| TavilyFinance
    TavilyFinance -->|"If no data"| Tavily
    Tavily -->|"Revenue/Funding"| ProfileAPI
    
    %% Display
    ProfileAPI --> Details
    Details --> Stats
    Details --> Gates
    Details --> Breakdown
    Details --> ScoreGauge
    Details --> Badge
    
    %% Eligibility Logic
    EISEngine -->|"factors[]"| Badge
    Badge -->|"Any score=0?"| BadgeLogic{Zero Factor?}
    BadgeLogic -->|"Yes"| RedBadge[🔴 Likely Not Eligible]
    BadgeLogic -->|"No"| GreenBadge[🟢 Likely Eligible]
    
    %% Portfolio
    Details -->|"Add to Portfolio"| Portfolio
    Portfolio -->|"LocalStorage"| Browser[(Browser Storage)]

    style Frontend fill:#1e293b,stroke:#4f46e5,color:#fff
    style Backend fill:#1e293b,stroke:#10b981,color:#fff
    style External fill:#1e293b,stroke:#f59e0b,color:#fff
```

### Key Technologies & Plugins

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend Framework** | Next.js 14 | React SSR, App Router |
| **UI Library** | Tailwind CSS | Responsive styling |
| **Animations** | Framer Motion | Smooth transitions |
| **Icons** | Lucide React | Icon library |
| **Charts** | Recharts | Data visualization |
| **State** | React useState | Local state management |
| **Backend** | FastAPI | Python REST API |
| **EIS Engine** | Custom Python | Heuristic scoring |

---

## 2. Company Research Agent Workflow

This diagram shows how the AI-powered Research Agent generates company reports using Tavily.

```mermaid
flowchart TB
    subgraph Frontend["🖥️ Research Page"]
        Form[Company Input Form]
        Examples[Example Companies<br/>Spotify/Revolut/Stripe]
        Progress[Research Progress<br/>16 queries]
        Report[Structured Report<br/>4 Sections]
        Actions[Action Buttons<br/>Copy/PDF/Email]
    end

    subgraph Backend["⚙️ Backend Services"]
        ResearchAPI["/api/research/company"]
        Researcher[CompanyResearcher<br/>company_researcher.py]
        PDFGen[PDF Generator<br/>WeasyPrint]
        EmailService[Email Service<br/>Gmail SMTP]
    end

    subgraph Tavily["🔍 Tavily AI"]
        TavilyAPI[Tavily Search API]
        Q1[Company Queries x4]
        Q2[Industry Queries x4]
        Q3[Financial Queries x4]
        Q4[News Queries x4]
    end

    subgraph Output["📄 Output"]
        ReportData[Structured Report JSON]
        PDF[Professional PDF]
        Email[Email with Attachment]
    end

    %% Flow
    User([👤 User]) --> Form
    Form -->|"Company + Industry"| ResearchAPI
    Examples -->|"Quick Fill"| Form
    
    ResearchAPI --> Researcher
    Researcher -->|"16 Parallel Queries"| TavilyAPI
    TavilyAPI --> Q1
    TavilyAPI --> Q2
    TavilyAPI --> Q3
    TavilyAPI --> Q4
    
    Q1 -->|"Results"| Researcher
    Q2 -->|"Results"| Researcher
    Q3 -->|"Results"| Researcher
    Q4 -->|"Results"| Researcher
    
    Researcher -->|"Aggregate"| ReportData
    ReportData --> Progress
    Progress --> Report
    
    %% Actions
    Report --> Actions
    Actions -->|"Generate PDF"| PDFGen
    PDFGen --> PDF
    Actions -->|"Send Email"| EmailService
    EmailService --> Email

    style Frontend fill:#1e293b,stroke:#4f46e5,color:#fff
    style Backend fill:#1e293b,stroke:#10b981,color:#fff
    style Tavily fill:#1e293b,stroke:#f59e0b,color:#fff
```

### Research Query Categories

| Category | Queries | Example |
|----------|---------|---------|
| **Company** | Funding, Valuation, Team, HQ | "Spotify funding rounds 2024" |
| **Industry** | Market size, Trends, Competition | "Music streaming market size" |
| **Financial** | Revenue, Growth, Profitability | "Spotify revenue 2024" |
| **News** | Announcements, Press, Updates | "Spotify latest news" |

---

## 3. Newsletter Subscribe Workflow

This diagram shows the newsletter subscription and email sending process.

```mermaid
flowchart TB
    subgraph Frontend["🖥️ EIS Page"]
        Subscribe[Subscribe Button]
        Modal[Subscribe Modal]
        FreqSelect[Frequency Selector<br/>Weekly/Monthly/Yearly/Now]
        EmailInput[Email Address Input]
        SendBtn[Send Newsletter]
    end

    subgraph Backend["⚙️ Backend"]
        EmailAPI["/api/eis/automation/send-email"]
        Writer[EIS Writer<br/>writer.py]
        Mailer[Newsletter Generator<br/>mailer.py]
        ResearchAgent[Research Agent<br/>Tavily News]
        EditorAgent[Editor Agent<br/>HuggingFace]
    end

    subgraph Processing["🔄 Data Processing"]
        Portfolio[Portfolio Companies]
        ScanHistory[Scan History]
        NewsLookup[News Lookup per Company]
        FinancialLookup[Financial Data Lookup]
    end

    subgraph Email["📧 Email Generation"]
        HTML[HTML Email Template]
        Section1[Portfolio Summary]
        Section2[Top Changes]
        Section3[AI Company Intelligence]
        Section4[Watchlist]
        Section5[Full Portfolio Table]
        Gmail[Gmail SMTP]
    end

    %% Flow
    User([👤 User]) --> Subscribe
    Subscribe --> Modal
    Modal --> FreqSelect
    Modal --> EmailInput
    EmailInput --> SendBtn
    
    SendBtn -->|"POST request"| EmailAPI
    EmailAPI --> Portfolio
    EmailAPI --> ScanHistory
    
    Portfolio -->|"Each company"| ResearchAgent
    ResearchAgent -->|"Tavily search"| NewsLookup
    NewsLookup --> EditorAgent
    EditorAgent -->|"Summarize"| NewsLookup
    
    Portfolio --> FinancialLookup
    FinancialLookup -->|"If no CH data"| ResearchAgent
    
    NewsLookup --> Mailer
    FinancialLookup --> Mailer
    
    Mailer --> HTML
    HTML --> Section1
    HTML --> Section2
    HTML --> Section3
    HTML --> Section4
    HTML --> Section5
    
    HTML --> Gmail
    Gmail -->|"Send"| Inbox([📬 User Inbox])

    style Frontend fill:#1e293b,stroke:#4f46e5,color:#fff
    style Backend fill:#1e293b,stroke:#10b981,color:#fff
    style Processing fill:#1e293b,stroke:#8b5cf6,color:#fff
    style Email fill:#1e293b,stroke:#f59e0b,color:#fff
```

### Newsletter Email Sections

| Section | Content | Data Source |
|---------|---------|-------------|
| **Portfolio Summary** | Stats: reviewed, eligible, review, ineligible | Calculated from portfolio |
| **Top Changes** | Top 3 companies with recommendations | Portfolio + EIS scoring |
| **AI Company Intelligence** | Tavily news per company | Tavily API |
| **Watchlist** | Companies needing review | Risk flags analysis |
| **Full Portfolio** | Compact table with all companies | Portfolio data |
| **Next Scheduled Run** | Based on frequency selection | User selection |

---

## 4. AI Newsroom Workflow

This diagram shows how the AI Newsroom generates news summaries for companies.

```mermaid
flowchart TB
    subgraph Frontend["🖥️ EIS Page"]
        NewsBtn[AI Newsroom Button]
        NewsModal[Newsroom Modal]
        CompanyList[Company Selection]
        NewsDisplay[News Cards Display]
    end

    subgraph Backend["⚙️ Backend"]
        NewsAPI["/api/eis/company/{id}/news"]
        ResearchAgent[Research Agent<br/>research_agent.py]
        EditorAgent[Editor Agent<br/>editor_agent.py]
    end

    subgraph TavilySearch["🔍 Tavily Search"]
        Query1["Company + sector news"]
        Query2["Company + funding news"]
        Query3["Company + product news"]
        Results[Search Results<br/>max 5 per query]
    end

    subgraph HuggingFace["🤖 HuggingFace AI"]
        Mistral[Mistral 7B Model]
        Summarize[Summarize Results]
        Relevance[Check EIS Relevance]
    end

    subgraph Output["📰 News Output"]
        Summary[AI-Generated Summary]
        Sources[Source Links]
        Score[EIS Score Context]
    end

    %% Flow
    User([👤 User]) --> NewsBtn
    NewsBtn --> NewsModal
    NewsModal --> CompanyList
    CompanyList -->|"Select company"| NewsAPI
    
    NewsAPI --> ResearchAgent
    ResearchAgent -->|"Build queries"| Query1
    ResearchAgent -->|"Build queries"| Query2
    ResearchAgent -->|"Build queries"| Query3
    
    Query1 --> TavilyAPI[(Tavily API)]
    Query2 --> TavilyAPI
    Query3 --> TavilyAPI
    TavilyAPI --> Results
    
    Results --> EditorAgent
    EditorAgent --> Mistral
    Mistral --> Summarize
    Mistral --> Relevance
    
    Summarize --> Summary
    Relevance -->|"is_relevant: true/false"| Summary
    Results -->|"URLs"| Sources
    
    Summary --> NewsDisplay
    Sources --> NewsDisplay
    Score --> NewsDisplay

    style Frontend fill:#1e293b,stroke:#4f46e5,color:#fff
    style Backend fill:#1e293b,stroke:#10b981,color:#fff
    style TavilySearch fill:#1e293b,stroke:#f59e0b,color:#fff
    style HuggingFace fill:#1e293b,stroke:#ec4899,color:#fff
```

### AI Newsroom Features

| Feature | Description |
|---------|-------------|
| **Multi-Query Search** | 3 different query types per company |
| **AI Summarization** | Mistral 7B via HuggingFace |
| **Relevance Scoring** | Filters irrelevant results |
| **Source Attribution** | Links to original articles |
| **EIS Context** | Includes score and status |

---

## 5. AI Daily News Workflow

This diagram shows the sector-wide daily news aggregation system.

```mermaid
flowchart TB
    subgraph Frontend["🖥️ EIS Header"]
        DailyBtn[AI Daily News Button]
        DailyModal[Daily News Modal]
        SectorTabs[Sector Tabs<br/>Tech/Healthcare/Fintech/CleanEnergy]
        NewsFeed[News Feed Cards]
    end

    subgraph Backend["⚙️ Backend"]
        DailyAPI["/api/eis/daily-news"]
        SectorQueries[Sector Query Builder]
        Aggregator[News Aggregator]
    end

    subgraph TavilySearch["🔍 Tavily Sector Search"]
        TechQ["UK technology startup funding 2024"]
        HealthQ["UK healthcare biotech funding 2024"]
        FintechQ["UK fintech payments investment 2024"]
        CleanQ["UK cleantech green energy funding 2024"]
    end

    subgraph Processing["🔄 Processing"]
        Filter[Filter & Dedupe]
        Format[Format Results]
        Cache[Cache Results<br/>15 min TTL]
    end

    subgraph Output["📰 Daily News Output"]
        TechNews[Technology News]
        HealthNews[Healthcare News]
        FintechNews[Fintech News]
        CleanNews[Clean Energy News]
    end

    %% Flow
    User([👤 User]) --> DailyBtn
    DailyBtn --> DailyModal
    DailyModal --> SectorTabs
    
    SectorTabs -->|"Load sector"| DailyAPI
    DailyAPI --> SectorQueries
    
    SectorQueries --> TechQ
    SectorQueries --> HealthQ
    SectorQueries --> FintechQ
    SectorQueries --> CleanQ
    
    TechQ --> TavilyAPI[(Tavily API)]
    HealthQ --> TavilyAPI
    FintechQ --> TavilyAPI
    CleanQ --> TavilyAPI
    
    TavilyAPI --> Aggregator
    Aggregator --> Filter
    Filter --> Format
    Format --> Cache
    
    Cache --> TechNews
    Cache --> HealthNews
    Cache --> FintechNews
    Cache --> CleanNews
    
    TechNews --> NewsFeed
    HealthNews --> NewsFeed
    FintechNews --> NewsFeed
    CleanNews --> NewsFeed

    style Frontend fill:#1e293b,stroke:#4f46e5,color:#fff
    style Backend fill:#1e293b,stroke:#10b981,color:#fff
    style TavilySearch fill:#1e293b,stroke:#f59e0b,color:#fff
    style Processing fill:#1e293b,stroke:#8b5cf6,color:#fff
```

### Sector News Categories

| Sector | Focus Areas | UK Keywords |
|--------|-------------|-------------|
| **Technology** | AI, SaaS, Deep Tech | "UK technology startup funding" |
| **Healthcare** | Biotech, Medtech, Digital Health | "UK healthcare biotech investment" |
| **Fintech** | Payments, Banking, InsurTech | "UK fintech digital banking" |
| **Clean Energy** | Renewables, Battery, CleanTech | "UK cleantech green energy" |

---

## Complete System Integration

```mermaid
graph LR
    subgraph User["👤 User Interface"]
        EIS[EIS Scanner]
        Research[Research Agent]
        News[AI Newsroom]
        Daily[Daily News]
        Subscribe[Newsletter]
    end

    subgraph APIs["🔌 API Layer"]
        FastAPI[FastAPI Server<br/>server.py]
    end

    subgraph Services["⚙️ Services"]
        Heuristics[EIS Heuristics]
        ResearchSvc[Research Agent]
        EditorSvc[Editor Agent]
        MailerSvc[Mailer]
        PDFSvc[PDF Generator]
    end

    subgraph External["🌐 External"]
        CH[Companies House]
        Tavily[Tavily AI]
        HF[HuggingFace]
        Gmail[Gmail SMTP]
    end

    EIS --> FastAPI
    Research --> FastAPI
    News --> FastAPI
    Daily --> FastAPI
    Subscribe --> FastAPI

    FastAPI --> Heuristics
    FastAPI --> ResearchSvc
    FastAPI --> EditorSvc
    FastAPI --> MailerSvc
    FastAPI --> PDFSvc

    Heuristics --> CH
    ResearchSvc --> Tavily
    EditorSvc --> HF
    MailerSvc --> Gmail
    PDFSvc --> MailerSvc

    style User fill:#4f46e5,stroke:#fff,color:#fff
    style APIs fill:#10b981,stroke:#fff,color:#fff
    style Services fill:#8b5cf6,stroke:#fff,color:#fff
    style External fill:#f59e0b,stroke:#fff,color:#fff
```

---

## Environment Variables Required

```env
# Companies House API
COMPANIES_HOUSE_API_KEY=xxxxxxxx

# Tavily AI Search
TAVILY_API_KEY=tvly-xxxxxxxx

# HuggingFace AI
HF_API_KEY=hf_xxxxxxxx

# Gmail SMTP
GMAIL_ADDRESS=your@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

---

*Report Generated: December 26, 2024*
*Platform: Sapphire Intelligence EIS Scanner v2.2.0*
