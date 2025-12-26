# EIS Investment Scanner — Architecture Report

## System Overview

The EIS Investment Scanner is a comprehensive platform for screening UK companies for Enterprise Investment Scheme (EIS) eligibility. This document details the architecture and data flow for each major component.

---

## 1. Complete EIS Page Architecture

### How It Works

The EIS page is a full-stack application connecting a Next.js frontend to a FastAPI backend, which integrates with multiple external APIs.

```mermaid
flowchart TB
    subgraph Frontend["🖥️ Next.js Frontend"]
        SearchBar[Search Input]
        PortfolioTab[Portfolio Tab]
        SearchTab[Search Results Tab]
        CompanyDetails[Company Details Panel]
        StatsGrid[Stats Grid: Directors, PSCs, Share Allotments, Age, Revenue]
        EligibilityGates[Eligibility Gates Display]
        ScoreBreakdown[Score Breakdown 0-100]
        ActionButtons[Add to Portfolio / Subscribe / Export]
    end

    subgraph Backend["⚙️ FastAPI Backend"]
        SearchAPI["/api/eis/search/{query}"]
        ProfileAPI["/api/eis/company/{id}/full-profile"]
        NewsAPI["/api/eis/company/{id}/news"]
        EISEngine[EIS Heuristics Engine]
        TavilyFinancial[Tavily Financial Research]
    end

    subgraph External["🌐 External APIs"]
        CompaniesHouse["Companies House API"]
        TavilyAPI["Tavily API"]
        HuggingFace["HuggingFace API"]
    end

    subgraph Storage["💾 Local Storage"]
        LocalPortfolio[Browser LocalStorage]
        ScanHistory[scan_history.json]
    end

    SearchBar --> SearchAPI
    SearchAPI --> CompaniesHouse
    CompaniesHouse --> SearchTab
    
    SearchTab -->|Select Company| ProfileAPI
    ProfileAPI --> CompaniesHouse
    ProfileAPI --> EISEngine
    EISEngine --> ScoreBreakdown
    
    ProfileAPI -->|No Accounts Data| TavilyFinancial
    TavilyFinancial --> TavilyAPI
    TavilyAPI --> StatsGrid
    
    CompanyDetails --> EligibilityGates
    ActionButtons -->|Save| LocalPortfolio
    PortfolioTab --> LocalPortfolio
```

### Plugins & Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend Framework** | Next.js 14 + TypeScript | Server-side rendering, routing |
| **Styling** | Tailwind CSS | Utility-first styling |
| **Animations** | Framer Motion | Smooth transitions |
| **Icons** | Lucide React | Modern icon library |
| **Charts** | Recharts | Score gauge visualization |
| **State** | React useState + LocalStorage | Portfolio persistence |

### Key Features Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant CompaniesHouse
    participant Tavily

    User->>Frontend: Enter company name
    Frontend->>Backend: GET /api/eis/search/{query}
    Backend->>CompaniesHouse: Search companies
    CompaniesHouse-->>Backend: Company list
    Backend-->>Frontend: Search results

    User->>Frontend: Click company
    Frontend->>Backend: GET /api/eis/company/{id}/full-profile
    Backend->>CompaniesHouse: Get profile, officers, PSCs, filings
    CompaniesHouse-->>Backend: Full company data
    Backend->>Backend: Calculate EIS Score (0-100)
    
    alt No Financial Data
        Backend->>Tavily: Search revenue/funding
        Tavily-->>Backend: Financial info
    end
    
    Backend-->>Frontend: Full profile + EIS assessment + financials
    Frontend->>Frontend: Display with eligibility badge
    
    Note over Frontend: If ANY factor score = 0<br/>Show "Likely Not Eligible" (red)
```

---

## 2. Company Research Agent Architecture

### How It Works

The Research Agent performs deep company research using Tavily AI search across 4 categories with 16 parallel queries.

```mermaid
flowchart TB
    subgraph Input["📝 User Input"]
        CompanyName[Company Name]
        Industry[Industry/Sector]
    end

    subgraph Frontend["🖥️ Research Page"]
        ResearchForm[Research Form]
        ProgressIndicator[Progress Indicator]
        ReportDisplay[Structured Report Display]
        ActionBar[Copy / PDF / Email Buttons]
    end

    subgraph Backend["⚙️ FastAPI Backend"]
        ResearchEndpoint["/api/research/company"]
        PDFEndpoint["/api/research/pdf"]
        EmailEndpoint["/api/research/email"]
        CompanyResearcher[CompanyResearcher Service]
    end

    subgraph TavilyQueries["🔍 16 Parallel Tavily Queries"]
        subgraph Category1["Company Overview (4)"]
            Q1[Funding & Investors]
            Q2[Valuation & Growth]
            Q3[Leadership Team]
            Q4[Headquarters & Employees]
        end
        subgraph Category2["Industry Overview (4)"]
            Q5[Market Size]
            Q6[Trends & Disruption]
            Q7[Competitive Landscape]
            Q8[Regulatory Environment]
        end
        subgraph Category3["Financial Overview (4)"]
            Q9[Revenue Model]
            Q10[Growth Metrics]
            Q11[Profitability]
            Q12[Funding Rounds]
        end
        subgraph Category4["Recent News (4)"]
            Q13[Latest News]
            Q14[Press Releases]
            Q15[Product Launches]
            Q16[Partnerships]
        end
    end

    subgraph Output["📊 Report Sections"]
        Section1[Company Overview]
        Section2[Industry Analysis]
        Section3[Financial Profile]
        Section4[Recent Developments]
    end

    subgraph Delivery["📤 Delivery Options"]
        CopyClipboard[Copy to Clipboard]
        PDFDownload[Download PDF]
        EmailSend[Email Report]
    end

    CompanyName --> ResearchForm
    Industry --> ResearchForm
    ResearchForm --> ResearchEndpoint
    ResearchEndpoint --> CompanyResearcher
    
    CompanyResearcher --> Q1 & Q2 & Q3 & Q4
    CompanyResearcher --> Q5 & Q6 & Q7 & Q8
    CompanyResearcher --> Q9 & Q10 & Q11 & Q12
    CompanyResearcher --> Q13 & Q14 & Q15 & Q16
    
    Q1 & Q2 & Q3 & Q4 --> Section1
    Q5 & Q6 & Q7 & Q8 --> Section2
    Q9 & Q10 & Q11 & Q12 --> Section3
    Q13 & Q14 & Q15 & Q16 --> Section4
    
    Section1 & Section2 & Section3 & Section4 --> ReportDisplay
    
    ReportDisplay --> ActionBar
    ActionBar --> CopyClipboard
    ActionBar --> PDFEndpoint --> PDFDownload
    ActionBar --> EmailEndpoint --> EmailSend
```

### Research Agent Data Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Tavily
    participant WeasyPrint
    participant Gmail

    User->>Frontend: Enter company + industry
    Frontend->>Backend: POST /api/research/company
    
    par Parallel Queries
        Backend->>Tavily: Company funding query
        Backend->>Tavily: Industry trends query
        Backend->>Tavily: Financial metrics query
        Backend->>Tavily: Recent news query
    end
    
    Tavily-->>Backend: All results
    Backend->>Backend: Aggregate into sections
    Backend-->>Frontend: Structured report
    
    alt User clicks PDF
        Frontend->>Backend: POST /api/research/pdf
        Backend->>WeasyPrint: Generate PDF
        WeasyPrint-->>Backend: PDF bytes
        Backend-->>Frontend: PDF download
    end
    
    alt User clicks Email
        Frontend->>Backend: POST /api/research/email
        Backend->>WeasyPrint: Generate PDF
        Backend->>Gmail: Send with attachment
        Gmail-->>Backend: Sent confirmation
        Backend-->>Frontend: Success
    end
```

---

## 3. Subscribe (Newsletter) Architecture

### How It Works

The Subscribe feature generates professional HTML email newsletters with portfolio intelligence, AI company news, and sector insights.

```mermaid
flowchart TB
    subgraph Trigger["🔔 Trigger Options"]
        ManualNow[Send Now Button]
        ScheduledWeekly[Weekly Schedule]
        ScheduledMonthly[Monthly Schedule]
    end

    subgraph Frontend["🖥️ Subscribe Modal"]
        EmailInput[Email Address Input]
        FrequencySelect[Frequency: Now/Weekly/Monthly/Yearly]
        SubmitButton[Subscribe Button]
    end

    subgraph Backend["⚙️ Newsletter Pipeline"]
        SendEmailAPI["/api/eis/automation/send-email"]
        PortfolioLoader[Load Portfolio Companies]
        CompanyEnricher[Enrich with Companies House]
        NewsGenerator[Generate AI News per Company]
        SectorNewsFetcher[Fetch Sector News]
        HTMLGenerator[ProfessionalNewsletterGenerator]
    end

    subgraph DataSources["📊 Data Sources"]
        CompaniesHouse["Companies House API"]
        TavilyAPI["Tavily API"]
        HuggingFaceAPI["HuggingFace API"]
        ScanHistory[scan_history.json]
    end

    subgraph Newsletter["✉️ Newsletter Sections"]
        Header[Header: EIS Portfolio Intelligence]
        Summary[Portfolio Summary Stats]
        TopChanges[Top Changes - Top 3 Companies]
        AIIntelligence[AI Company Intelligence]
        Watchlist[Watchlist - Review Required]
        FullPortfolio[Full Portfolio Table]
        DataSourcesSection[Data Sources Used]
        NextRun[Next Scheduled Run]
        Footer[Sapphire Intelligence Footer]
    end

    subgraph Delivery["📤 Email Delivery"]
        GmailSMTP[Gmail SMTP]
        RecipientInbox[Recipient Inbox]
    end

    ManualNow --> SubmitButton
    ScheduledWeekly --> SendEmailAPI
    ScheduledMonthly --> SendEmailAPI
    
    SubmitButton --> SendEmailAPI
    SendEmailAPI --> PortfolioLoader
    PortfolioLoader --> CompanyEnricher
    CompanyEnricher --> CompaniesHouse
    
    CompanyEnricher --> NewsGenerator
    NewsGenerator --> TavilyAPI
    TavilyAPI --> HuggingFaceAPI
    
    SendEmailAPI --> SectorNewsFetcher
    SectorNewsFetcher --> TavilyAPI
    
    NewsGenerator --> HTMLGenerator
    SectorNewsFetcher --> HTMLGenerator
    
    HTMLGenerator --> Header
    HTMLGenerator --> Summary
    HTMLGenerator --> TopChanges
    HTMLGenerator --> AIIntelligence
    HTMLGenerator --> Watchlist
    HTMLGenerator --> FullPortfolio
    HTMLGenerator --> DataSourcesSection
    HTMLGenerator --> NextRun
    HTMLGenerator --> Footer
    
    Footer --> GmailSMTP
    GmailSMTP --> RecipientInbox
```

### Newsletter Content Generation

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant CompaniesHouse
    participant Tavily
    participant HuggingFace
    participant Gmail

    User->>Frontend: Click Subscribe > Send Now
    Frontend->>Backend: POST /api/eis/automation/send-email
    
    Backend->>Backend: Load portfolio companies
    
    loop For each company (max 5)
        Backend->>CompaniesHouse: Get company profile
        CompaniesHouse-->>Backend: Profile data
        Backend->>Tavily: Search company news
        Tavily-->>Backend: News results
        Backend->>HuggingFace: Summarize news
        HuggingFace-->>Backend: AI summary
    end
    
    par Sector News
        Backend->>Tavily: UK Technology startup news
        Backend->>Tavily: UK Healthcare biotech news
        Backend->>Tavily: UK Fintech news
    end
    
    Backend->>Backend: Generate HTML newsletter
    Note over Backend: 7 sections: Summary, Top Changes,<br/>AI Intelligence, Watchlist, Portfolio,<br/>Data Sources, Next Run
    
    Backend->>Gmail: Send HTML email
    Gmail-->>Backend: Sent
    Backend-->>Frontend: Success response
```

---

## 4. AI Newsroom Architecture

### How It Works

The AI Newsroom fetches real-time news for a selected company using Tavily and summarizes it with HuggingFace.

```mermaid
flowchart TB
    subgraph Trigger["🔔 Trigger"]
        NewsroomButton[AI Newsroom Button]
        CompanySelect[Selected Company in Details]
    end

    subgraph Frontend["🖥️ AI Newsroom Modal"]
        NewsModal[News Modal Window]
        LoadingSpinner[Loading State]
        NewsCards[News Article Cards]
        AISummary[AI-Generated Summary]
        SourceLinks[Source Links]
    end

    subgraph Backend["⚙️ News Pipeline"]
        NewsAPI["/api/eis/company/{id}/news"]
        ResearchAgent[ResearchAgent - Tavily]
        EditorAgent[EditorAgent - HuggingFace]
    end

    subgraph Processing["🔄 AI Processing"]
        TavilySearch[Tavily News Search]
        Relevance[Filter Relevant Results]
        Summarize[Summarize with Mistral 7B]
        FormatOutput[Format for Display]
    end

    NewsroomButton --> CompanySelect
    CompanySelect --> NewsAPI
    
    NewsAPI --> ResearchAgent
    ResearchAgent --> TavilySearch
    TavilySearch --> Relevance
    Relevance --> EditorAgent
    EditorAgent --> Summarize
    Summarize --> FormatOutput
    
    FormatOutput --> AISummary
    FormatOutput --> NewsCards
    FormatOutput --> SourceLinks
    
    AISummary --> NewsModal
    NewsCards --> NewsModal
    SourceLinks --> NewsModal
```

### AI Newsroom Data Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Tavily
    participant HuggingFace

    User->>Frontend: Click AI Newsroom button
    Frontend->>Backend: GET /api/eis/company/{id}/news
    
    Backend->>Tavily: Search "{company_name} news funding UK"
    Tavily-->>Backend: 5-10 news results
    
    Backend->>Backend: Filter by relevance score
    
    Backend->>HuggingFace: Summarize for EIS context
    Note over HuggingFace: Mistral 7B Instruct<br/>Prompt: Summarize for investor<br/>Include EIS relevance
    HuggingFace-->>Backend: AI summary
    
    Backend-->>Frontend: News + Summary + Sources
    Frontend->>Frontend: Display in modal
```

---

## 5. AI Daily News Architecture

### How It Works

The AI Daily News feature provides sector-wide investment news across Technology, Healthcare, Fintech, and Clean Energy sectors.

```mermaid
flowchart TB
    subgraph Trigger["🔔 Trigger"]
        DailyNewsButton[AI Daily News Button in Header]
    end

    subgraph Frontend["🖥️ Daily News Page"]
        NewsPage["/daily-news"]
        SectorTabs[Sector Tabs: Tech / Healthcare / Fintech / CleanTech]
        NewsGrid[News Article Grid]
        AIInsights[AI Market Insights]
        LastUpdated[Last Updated Timestamp]
    end

    subgraph Backend["⚙️ Daily News Pipeline"]
        DailyNewsAPI["/api/eis/daily-news"]
        SectorQueries[Sector-Specific Queries]
        ResultAggregator[Aggregate Results]
        InsightsGenerator[Generate AI Insights]
    end

    subgraph TavilyQueries["🔍 Sector Queries"]
        TechQuery["UK technology startup funding 2024 2025"]
        HealthQuery["UK healthcare biotech medtech funding 2024 2025"]
        FintechQuery["UK fintech digital banking payments 2024 2025"]
        CleanQuery["UK cleantech green energy funding 2024 2025"]
    end

    subgraph Output["📊 News Display"]
        TechNews[Technology News Cards]
        HealthNews[Healthcare News Cards]
        FintechNews[Fintech News Cards]
        CleanNews[Clean Energy News Cards]
    end

    DailyNewsButton --> DailyNewsAPI
    
    DailyNewsAPI --> SectorQueries
    SectorQueries --> TechQuery
    SectorQueries --> HealthQuery
    SectorQueries --> FintechQuery
    SectorQueries --> CleanQuery
    
    TechQuery --> ResultAggregator
    HealthQuery --> ResultAggregator
    FintechQuery --> ResultAggregator
    CleanQuery --> ResultAggregator
    
    ResultAggregator --> InsightsGenerator
    InsightsGenerator --> AIInsights
    
    ResultAggregator --> TechNews
    ResultAggregator --> HealthNews
    ResultAggregator --> FintechNews
    ResultAggregator --> CleanNews
    
    TechNews --> SectorTabs
    HealthNews --> SectorTabs
    FintechNews --> SectorTabs
    CleanNews --> SectorTabs
    
    SectorTabs --> NewsGrid
    AIInsights --> NewsPage
```

### Daily News Sequence

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Tavily

    User->>Frontend: Click AI Daily News button
    Frontend->>Backend: GET /api/eis/daily-news
    
    par Parallel Sector Queries
        Backend->>Tavily: Technology sector query
        Backend->>Tavily: Healthcare sector query
        Backend->>Tavily: Fintech sector query
        Backend->>Tavily: Clean Energy sector query
    end
    
    Tavily-->>Backend: All sector results
    
    Backend->>Backend: Aggregate by sector
    Backend->>Backend: Generate AI insights
    
    Backend-->>Frontend: Sectored news + insights
    Frontend->>Frontend: Display in tabs
    
    User->>Frontend: Click sector tab
    Frontend->>Frontend: Filter to selected sector
```

---

## Technology Stack Summary

```mermaid
mindmap
  root((EIS Scanner))
    Frontend
      Next.js 14
      TypeScript
      Tailwind CSS
      Framer Motion
      Lucide Icons
      Recharts
    Backend
      FastAPI
      Python 3.11
      Pandas
      WeasyPrint
    APIs
      Companies House
      Tavily AI
      HuggingFace
      Gmail SMTP
    AI Models
      Mistral 7B Instruct
      Research Agent
      Editor Agent
    Storage
      LocalStorage
      scan_history.json
      trained_models/
```

---

## Environment Variables Required

| Variable | Service | Purpose |
|----------|---------|---------|
| `COMPANIES_HOUSE_API_KEY` | Companies House | UK company data |
| `TAVILY_API_KEY` | Tavily | AI news search |
| `HF_API_KEY` | HuggingFace | LLM summarization |
| `GMAIL_ADDRESS` | Gmail | Newsletter sending |
| `GMAIL_APP_PASSWORD` | Gmail | SMTP authentication |

---

*Report Generated: December 26, 2024*  
*Platform Version: 2.2.0*
