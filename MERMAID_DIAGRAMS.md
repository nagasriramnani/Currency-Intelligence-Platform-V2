# EIS Architecture - Mermaid Diagrams

Copy each diagram below into [Mermaid Chart](https://mermaid.live) to download as PNG/SVG.

---

## 1. EIS Page - How It Works

```
flowchart TB
    subgraph Frontend["Frontend (Next.js)"]
        Search[Search Bar]
        Results[Results Grid]
        Details[Company Details]
        Portfolio[Portfolio Tab]
    end

    subgraph Backend["Backend (FastAPI)"]
        SearchAPI["/api/eis/search"]
        ProfileAPI["/api/eis/company/full-profile"]
        EISEngine[EIS Scoring Engine]
    end

    subgraph External["External APIs"]
        CH[Companies House]
        Tavily[Tavily API]
    end

    Search --> SearchAPI
    SearchAPI --> CH
    CH --> Results
    Results --> ProfileAPI
    ProfileAPI --> CH
    ProfileAPI --> EISEngine
    EISEngine --> Details
    ProfileAPI -.-> Tavily
    Tavily -.-> Details
    Details --> Portfolio
```

---

## 2. EIS Page - Data Flow

```
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
    
    Backend-->>Frontend: Full profile + EIS assessment
    Frontend->>Frontend: Display with eligibility badge
    
    Note over Frontend: If ANY factor score = 0<br/>Show "Likely Not Eligible" (red)
```

---

## 3. Research Agent - How It Works

```
flowchart TB
    subgraph Input["User Input"]
        Name[Company Name]
        Industry[Industry/Sector]
    end

    subgraph Research["Research Agent"]
        API["/api/research/company"]
        Researcher[CompanyResearcher]
    end

    subgraph Queries["16 Tavily Queries"]
        Q1[Company: Funding, Team, HQ]
        Q2[Industry: Market, Trends]
        Q3[Financial: Revenue, Growth]
        Q4[News: Press, Products]
    end

    subgraph Output["Report Output"]
        Report[4-Section Report]
        PDF[PDF Export]
        Email[Email Delivery]
    end

    Name --> API
    Industry --> API
    API --> Researcher
    Researcher --> Q1 & Q2 & Q3 & Q4
    Q1 & Q2 & Q3 & Q4 --> Report
    Report --> PDF
    Report --> Email
```

---

## 4. Research Agent - Data Flow

```
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

## 5. Newsletter - How It Works

```
flowchart TB
    subgraph Trigger["Trigger Options"]
        Now[Send Now]
        Weekly[Weekly Schedule]
        Monthly[Monthly Schedule]
    end

    subgraph Data["Data Collection"]
        Portfolio[Load Portfolio]
        CH[Companies House]
        Tavily[Tavily News]
        AI[HuggingFace AI]
    end

    subgraph Email["Newsletter"]
        HTML[HTML Generator]
        Gmail[Gmail SMTP]
    end

    Now --> Portfolio
    Weekly --> Portfolio
    Monthly --> Portfolio
    Portfolio --> CH
    Portfolio --> Tavily
    Tavily --> AI
    CH --> HTML
    AI --> HTML
    HTML --> Gmail
```

---

## 6. Newsletter - Data Flow

```
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

## 7. AI Newsroom - How It Works

```
flowchart TB
    subgraph Trigger["User Action"]
        Button[AI Newsroom Button]
        Company[Selected Company]
    end

    subgraph Pipeline["News Pipeline"]
        API["/api/eis/company/news"]
        Tavily[Tavily Search]
        Filter[Relevance Filter]
        AI[HuggingFace Mistral 7B]
    end

    subgraph Display["Modal Display"]
        Summary[AI Summary]
        Cards[News Cards]
        Sources[Source Links]
    end

    Button --> Company
    Company --> API
    API --> Tavily
    Tavily --> Filter
    Filter --> AI
    AI --> Summary
    Tavily --> Cards
    Tavily --> Sources
```

---

## 8. AI Newsroom - Data Flow

```
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

## 9. Daily News - How It Works

```
flowchart TB
    subgraph Trigger["Trigger"]
        Button[Daily News Button]
    end

    subgraph Sectors["4 Sector Queries"]
        Tech[Technology: AI, SaaS]
        Health[Healthcare: Biotech]
        Fintech[Fintech: Payments]
        Clean[Clean Energy: Green]
    end

    subgraph Output["Display"]
        Tabs[Sector Tabs]
        Cards[News Cards]
        Insights[AI Insights]
    end

    Button --> Tech & Health & Fintech & Clean
    Tech & Health & Fintech & Clean --> Tabs
    Tabs --> Cards
    Tabs --> Insights
```

---

## 10. Daily News - Data Flow

```
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

## How to Use

1. Go to [mermaid.live](https://mermaid.live)
2. Copy any diagram code above (without the ``` marks)
3. Paste into the editor
4. Click **Actions > Download PNG** or **Download SVG**
