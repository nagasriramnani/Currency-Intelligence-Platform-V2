# Sapphire Intelligence Platform

**Enterprise-Grade Financial Analytics & AI-Powered Investment Screening**

![Version](https://img.shields.io/badge/version-3.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![Next.js](https://img.shields.io/badge/next.js-14.0-black)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🎯 Overview

The **Sapphire Intelligence Platform** is a comprehensive financial analytics system featuring:

| Module | Description |
|--------|-------------|
| **EIS Investment Scanner** | UK company screening with mandatory eligibility gates |
| **AI-Powered EIS Advisor** | Conversational agent powered by Ollama (llama3.2) |
| **Currency Intelligence** | FX monitoring, ML forecasting, and risk analytics |
| **Newsletter System** | Professional HTML emails with company intelligence |

Built for **Sapphire Capital Partners** with a premium Next.js dashboard and Python/FastAPI backend.

---

## ✨ Key Features

### 🏢 EIS Investment Scanner

| Feature | Description |
|---------|-------------|
| **Company Search** | UK Companies House integration (10M+ companies) |
| **Mandatory Gates** | 6 hard gates - fail ANY = Not Eligible |
| **EIS Scoring** | 0-100 heuristic scoring based on HMRC criteria |
| **Failed Gates UI** | Clear red banner showing which criteria failed |
| **Portfolio Management** | 5 portfolio slots with localStorage persistence |
| **Remove from Portfolio** | Hover-to-remove with one-click deletion |

### 🤖 EIS Advisor (AI Chat)

| Feature | Description |
|---------|-------------|
| **Local LLM** | Ollama (llama3.2) - runs 100% locally |
| **Multi-Tool Agent** | Companies House, EIS Scoring, News, Financials |
| **EIS Knowledge Base** | Built-in HMRC rules and criteria |
| **Conversation Memory** | Maintains context across messages |

### 📊 Currency Intelligence

| Feature | Description |
|---------|-------------|
| **Official Data** | US Treasury FX rates with 5+ years history |
| **ML Forecasting** | XGBoost, Prophet, ARIMA with confidence intervals |
| **Risk Management** | VaR, CVaR, stress testing (GFC, Brexit, COVID) |
| **Alerting** | Slack webhooks for significant movements |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 14)                         │
│  /              - Currency Dashboard                             │
│  /eis           - EIS Scanner & Portfolio                        │
│  /advisor       - AI Chat (EIS Advisor)                          │
│  /analysis      - Currency Analysis                              │
│  /risk          - Risk Analytics                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                             │
│  api/server.py           - Main REST API                         │
│  analytics/eis_heuristics.py - EIS Scoring Engine               │
│  services/advisor_agent.py   - AI Advisor Agent                 │
│  automation/mailer.py        - Newsletter System                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Ollama LLM  │    │ Companies   │    │ Tavily API  │
│ (llama3.2)  │    │ House API   │    │ (News)      │
└─────────────┘    └─────────────┘    └─────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Ollama (for EIS Advisor)

### Installation

```bash
# Clone repository
git clone https://github.com/nagasriramnani/Currency-Intelligence-Platform-V2.git
cd Currency-Intelligence-Platform-V2

# Backend setup
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys

# Frontend setup
cd ../frontend
npm install

# Start Ollama (for EIS Advisor)
ollama pull llama3.2
ollama serve
```

### Running

**Windows:**
```cmd
run.bat
```

**Manual:**
```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### URLs

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| EIS Scanner | http://localhost:3000/eis |
| EIS Advisor | http://localhost:3000/advisor |
| API Docs | http://localhost:8000/docs |

---

## ⚙️ Environment Variables

Create `backend/.env`:

```env
# Required for EIS Scanner
COMPANIES_HOUSE_API_KEY=your_key

# Required for News/Research
TAVILY_API_KEY=your_key

# Optional - EIS Advisor (defaults to localhost)
OLLAMA_URL=http://localhost:11434

# Optional - AI Summaries
HF_API_KEY=your_key

# Optional - Newsletter
GMAIL_ADDRESS=your_email
GMAIL_APP_PASSWORD=your_app_password

# Optional - Alerts
SLACK_WEBHOOK_URL=your_webhook
```

---

## 📁 Project Structure

```
sapphire-intelligence-platform/
├── backend/
│   ├── api/                    # FastAPI server
│   │   └── server.py           # Main API (3500+ lines)
│   ├── analytics/              # Business logic
│   │   ├── eis_heuristics.py   # EIS scoring with mandatory gates
│   │   └── companies_house.py  # UK company data
│   ├── services/               # AI agents
│   │   ├── advisor_agent.py    # EIS Advisor (Ollama)
│   │   ├── research_agent.py   # Tavily news
│   │   └── editor_agent.py     # HuggingFace AI
│   ├── automation/             # Email & scheduling
│   │   ├── mailer.py           # Newsletter generator
│   │   └── pdf_generator.py    # PDF reports
│   ├── ml/                     # Machine learning
│   └── requirements.txt
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx            # Currency Dashboard
│   │   ├── eis/page.tsx        # EIS Scanner
│   │   ├── advisor/page.tsx    # AI Advisor Chat
│   │   ├── analysis/           # Currency analysis
│   │   └── risk/               # Risk analytics
│   └── src/components/         # React components
├── docs/                       # Documentation
├── README.md
└── run.bat                     # Windows startup
```

---

## 🔐 EIS Mandatory Gates

**Critical Rule: If ANY gate fails → Company is NOT ELIGIBLE (Score = 0)**

| Gate | Criteria | KIC Exception |
|------|----------|---------------|
| **Status** | Must be 'active' | None |
| **Sector** | Not banking, property, hotels, legal | None |
| **Age** | <7 years from first sale | <10 years |
| **Employees** | <250 FTE | <500 |
| **Gross Assets** | <£15M before investment | None |
| **Independence** | Not controlled by another company | None |

---

## 🔄 Recent Updates (v3.0.0)

### New Features
- ✅ **EIS Advisor** - AI chat for company analysis
- ✅ **Mandatory Gates** - Hard eligibility checks (fail any = 0)
- ✅ **Failed Gates UI** - Red banner showing failed criteria
- ✅ **Portfolio Remove** - One-click company removal
- ✅ **7-Year Age Rule** - KIC exception support

### Improvements
- ✅ Conversation memory in Advisor
- ✅ Cleaner eligibility badges
- ✅ Portfolio statistics update on removal

---

## 📊 Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, Framer Motion |
| **Backend** | Python 3.9+, FastAPI, Pandas, XGBoost, Prophet |
| **AI/LLM** | Ollama (llama3.2), HuggingFace (Mistral 7B) |
| **Data APIs** | UK Companies House, US Treasury, Tavily |
| **Storage** | localStorage (frontend), SQLite (newsletter) |

---

## 📝 License

MIT License - See [LICENSE](LICENSE)

---

## 🔗 Links

- **GitHub**: [nagasriramnani/Currency-Intelligence-Platform-V2](https://github.com/nagasriramnani/Currency-Intelligence-Platform-V2)
- **API Docs**: http://localhost:8000/docs (when running)

---

**Built for Sapphire Capital Partners** | Version 3.0.0 | January 2026
