# Sapphire Intelligence Platform
## Complete Dashboard Walkthrough Guide

Welcome to the Currency Intelligence Platform! This guide explains every component of the dashboard, designed for both **business users** and **technical teams**.

---

## 📊 Table of Contents

1. [Dashboard Overview](#dashboard-overview)
2. [Market Pulse - KPI Cards](#market-pulse---kpi-cards)
3. [Historical Trends Chart](#historical-trends-chart)
4. [Volatility Risk Chart](#volatility-risk-chart)
5. [AI Forecasting & Projections](#ai-forecasting--projections)
6. [Year-on-Year Comparison](#year-on-year-comparison)
7. [System Alerts](#system-alerts)
8. [Analysis Page](#analysis-page)
9. [Scenario Builder](#scenario-builder)

---

## Dashboard Overview

The main dashboard provides a real-time snapshot of currency exchange rates, trends, and risk indicators. It's designed to help treasury teams, financial analysts, and business users make informed currency decisions.

### Navigation Bar
| Element | Purpose |
|---------|---------|
| **Dashboard** | Main overview with KPIs and charts |
| **Analysis** | Deep-dive into correlations and seasonality |
| **Risk** | Value-at-Risk and stress testing |
| **Settings** | Configure preferences and data sources |
| **Refresh Data** | Manually update all data from APIs |
| **Last Updated** | Shows when data was last refreshed |

---

## Market Pulse - KPI Cards

The **Market Pulse** section displays three key currency pairs with real-time rates and changes.

### Understanding Each KPI Card

```
┌─────────────────────────────────────────────┐
│  USD/CAD                              [↗]   │
│  1.3920  CAD                                │
│                                             │
│  ↑+2.81%   YoY   from 1.3540                │
└─────────────────────────────────────────────┘
```

| Element | What It Means |
|---------|---------------|
| **USD/CAD** | Currency pair being tracked (US Dollar to Canadian Dollar) |
| **1.3920** | Current exchange rate (1 USD = 1.3920 CAD) |
| **CAD** | Base currency label |
| **[↗]** | Direction arrow (green = rising, red = falling) |
| **+2.81%** | Percentage change over selected period |
| **YoY** | Period label (Year-over-Year in this case) |
| **from 1.3540** | Starting rate at beginning of period |

### Interpreting the Data

**For Business Users:**
- **Green arrow up (↗)**: USD is strengthening against this currency. If you pay suppliers in this currency, costs are going up.
- **Red arrow down (↘)**: USD is weakening. Foreign revenue converts to more USD.
- **Percentage**: Shows how much the rate has changed. +2.81% means USD buys 2.81% more CAD than before.

**For Technical Users:**
- Data source: Financial Modeling Prep API + US Treasury
- Calculation: `(current_rate - period_start_rate) / period_start_rate * 100`
- Animation: Count-up effect uses IntersectionObserver + requestAnimationFrame

### Example Cards from Screenshots

| Card | Rate | Change | Meaning |
|------|------|--------|---------|
| **USD/CAD** | 1.3920 | +2.81% | USD strengthened vs CAD over past year |
| **USD/EUR** | 0.8520 | +8.97% | Significant USD strength vs Euro |
| **USD/GBP** | 0.7440 | +10.36% | Strong USD appreciation vs British Pound |

### Date Range Controls

| Control | Function |
|---------|----------|
| **1Y / 3Y / 5Y / Max** | Quick preset time ranges |
| **From / To** | Custom date range picker |
| **Reset** | Return to default 3-year view |

---

## Historical Trends Chart

The multi-line chart shows how each currency pair has moved over time.

### Reading the Chart

| Line Color | Currency Pair |
|------------|---------------|
| 🔴 Red | USD/EUR |
| 🟢 Green | USD/GBP |
| 🔵 Blue | USD/CAD |
| Dotted lines | Moving Averages (3-period) |

**For Business Users:**
- **Upward trend**: USD is getting stronger (you get more foreign currency per USD)
- **Downward trend**: USD is weakening (foreign currency buys more USD)
- **Flat line**: Exchange rate is stable

**For Technical Users:**
- Chart library: Recharts (React)
- Data points: Daily closing rates
- Moving averages: 3-period simple moving average (SMA)
- Download button exports data as CSV

---

## Volatility Risk Chart

Shows how "jumpy" each currency has been over time.

### Understanding Volatility

| Volatility Level | What It Means |
|------------------|---------------|
| **< 10%** | Very stable, low risk |
| **10-20%** | Normal fluctuations |
| **20-30%** | Elevated risk, consider hedging |
| **> 30%** | High volatility, hedging recommended |

**For Business Users:**
- Higher volatility = more uncertainty in budgets
- If EUR volatility spikes, lock in rates with forward contracts
- The dotted "Mea" line shows the historical average

**For Technical Users:**
- Calculation: Annualized standard deviation of daily returns
- Formula: `volatility = std_dev(daily_returns) * sqrt(252)`
- 252 = trading days per year

---

## AI Forecasting & Projections

The platform uses machine learning (XGBoost) to predict future exchange rates.

### Understanding the Forecast Panel

| Element | Meaning |
|---------|---------|
| **Actual (solid blue)** | Historical observed rates |
| **Forecast (dashed orange)** | Predicted future rates |
| **Confidence Band (shaded)** | Range where actual rate is likely to fall |

### Key Metrics Explained

| Metric | Value | What It Means |
|--------|-------|---------------|
| **MAPE** | 70.7% | Model error rate (lower = better, <10% is good) |
| **Forecast Horizon** | 6 periods | How far into the future we're predicting |
| **Direction** | Rising ↗ | Model predicts USD will strengthen |
| **Confidence** | 0.9014 - 0.9879 | 80% confidence interval range |

### AI Intelligence Panel

The right sidebar provides natural language summaries:

> "USD has weakened against EUR by -3.4% over the past year, reaching 0.8520 as of 2025-09-30."

> "USD/EUR is currently experiencing normal volatility, with recent fluctuations in line with historical averages. Annualized volatility stands at 111.85%."

> "Our forecasting model anticipates mild depreciation in USD/EUR over the next quarter, with moderate confidence (approximately 65%)."

**For Business Users:**
- Use forecasts to inform hedging decisions
- Wider confidence bands = more uncertainty
- Don't rely solely on predictions for critical decisions

**For Technical Users:**
- Model: XGBoost with recursive forecasting
- Training: Rolling window approach
- Features: Lagged values, technical indicators
- Confidence: Bootstrap prediction intervals

---

## Year-on-Year Comparison

The bar chart compares current rates to rates from one year ago.

### Reading the Chart

| Currency | Current | Year Ago | Change |
|----------|---------|----------|--------|
| **GBP** | 0.7440 | 0.7450 | -0.13% (slight USD weakening) |
| **CAD** | 1.3920 | 1.3520 | +2.96% (USD stronger) |
| **EUR** | 0.8520 | 0.8930 | -4.59% (significant USD weakening) |

### Color Coding

| Color | Meaning |
|-------|---------|
| **Gray bar** | Year ago rate |
| **Colored bar** | Current rate |
| **Green badge** | USD strengthened |
| **Red badge** | USD weakened |

---

## System Alerts

Real-time monitoring generates automated alerts when unusual conditions are detected.

### Alert Types

| Alert Type | What Triggers It |
|------------|------------------|
| **Volatility Check** | Currency volatility exceeds 2 standard deviations |
| **VaR Check** | Value-at-Risk threshold breached |
| **Regime Check** | Market regime change detected |

### Example Alert

```
🔴 CRITICAL | VaR Breach | EUR
EUR VaR breach: 95% VaR = 454.76%, CVaR = 700.78%
Model Confidence: ████████░░ 60%
CVAR: 700.78    THRESHOLD: 2.00
```

### Alert Actions

| Button | Action |
|--------|--------|
| **Acknowledge** | Mark as seen, keeps in history |
| **Resolve** | Mark as addressed |
| **Snooze** | Temporarily hide alert |

---

## Analysis Page

### Correlation Matrix

Shows how currency pairs move together.

| Value | Meaning |
|-------|---------|
| **1.00** | Perfect positive correlation (move together) |
| **0.00** | No correlation (independent movement) |
| **-1.00** | Perfect negative correlation (move opposite) |

**For Business Users:**
- If EUR and GBP are highly correlated, hedging one partially hedges the other
- Use this for diversification decisions

**For Technical Users:**
- Calculation: Pearson correlation on 90-day rolling returns
- Updated daily

### Seasonality Analysis

Shows average monthly performance over 5 years.

| Month | Green Bar | Red Bar |
|-------|-----------|---------|
| August | | USD typically weakens |
| November | USD typically strengthens | |

**For Business Users:**
- Plan major currency conversions around seasonal patterns
- June-August shows USD typically weakens vs EUR

---

## Scenario Builder

Simulate "what-if" scenarios to understand portfolio impact.

### Portfolio Composition

Enter your holdings in each currency:
- USD: 100,000
- EUR: 50,000
- GBP: 25,000
- CAD: 25,000

### Market Shocks

| Preset Scenario | What It Simulates |
|-----------------|-------------------|
| **USD Crash** | Sudden USD depreciation |
| **EUR Rally** | Euro strengthening |
| **Brexit 2.0** | GBP volatility spike |
| **Oil Spike** | CAD appreciation (oil exporter) |

### Custom Shocks

Use sliders to set custom percentage shocks:
- EUR Shock: -5% to +5%
- GBP Shock: -5% to +5%
- CAD Shock: -5% to +5%

### Impact Analysis

The chart shows:
- **Current**: Portfolio value today
- **Projected**: Value after applying shocks

**Net Impact**: Shows dollar gain/loss and percentage change

---

## Quick Reference Card

### Colors & Icons

| Icon/Color | Meaning |
|------------|---------|
| 🟢 Green | Positive / USD strengthening |
| 🔴 Red | Negative / USD weakening |
| 🔵 Blue | Neutral / Information |
| ↗ Arrow Up | Rising trend |
| ↘ Arrow Down | Falling trend |
| ─ Horizontal | Flat / Stable |

### Key Formulas

| Metric | Formula |
|--------|---------|
| **Percentage Change** | `(new - old) / old × 100` |
| **Volatility** | `StdDev(returns) × √252` |
| **VaR (95%)** | 95th percentile of potential losses |
| **Correlation** | `Cov(A,B) / (StdDev(A) × StdDev(B))` |

---

## Glossary

| Term | Definition |
|------|------------|
| **USD** | United States Dollar |
| **EUR** | Euro (European Union) |
| **GBP** | British Pound Sterling |
| **CAD** | Canadian Dollar |
| **YoY** | Year-over-Year (comparing to same date last year) |
| **VaR** | Value at Risk - maximum expected loss at confidence level |
| **CVaR** | Conditional VaR - average loss when VaR is exceeded |
| **MAPE** | Mean Absolute Percentage Error |
| **XGBoost** | Extreme Gradient Boosting (ML algorithm) |
| **Volatility** | Measure of price fluctuation intensity |
| **Correlation** | Statistical relationship between two variables |
| **Hedging** | Strategy to reduce currency risk |

---

## Need Help?

- **Refresh Data**: Click the "Refresh Data" button to get latest rates
- **Change Time Range**: Use the RANGE selector or date pickers
- **Export Data**: Click the download icon on charts
- **Settings**: Configure alerts, data sources, and theme

---

*Document Version: 1.0 | Last Updated: December 2025*
