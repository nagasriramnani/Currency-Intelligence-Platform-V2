# Risk Analytics Page
## Complete Walkthrough Guide

This guide explains every component of the **Risk Analytics** page in the Sapphire Intelligence Platform. Written for both business users and technical teams.

---

## 📊 Table of Contents

1. [Page Overview](#page-overview)
2. [Value at Risk (VaR) Analysis](#value-at-risk-var-analysis)
3. [Stress Test Scenarios](#stress-test-scenarios)
4. [Hedging Recommendations](#hedging-recommendations)
5. [Understanding Risk Levels](#understanding-risk-levels)

---

## Page Overview

The Risk Analytics page helps you understand and manage currency risk exposure. It answers three critical questions:

1. **How much could I lose?** → VaR Analysis
2. **What happens in a crisis?** → Stress Test Scenarios
3. **What should I do about it?** → Hedging Recommendations

### Page Controls

| Control | Function |
|---------|----------|
| **95% Confidence** | Confidence level for VaR calculation (90%, 95%, or 99%) |
| **1-Day Horizon** | Time period for risk measurement (1, 5, or 10 days) |
| **Refresh** | Update all risk metrics with latest data |

---

## Value at Risk (VaR) Analysis

VaR tells you the **maximum expected loss** at a given confidence level over a specified time period.

### Reading the VaR Panel

```
┌─────────────────────────────────────────────────────────┐
│  Value at Risk Analysis                                 │
│  95% confidence, 1-day horizon                          │
├─────────────────────────────────────────────────────────┤
│  USD/EUR              Critical    │  USD/GBP    Critical │
│  VaR (Parametric)      5.08%      │  VaR         5.31%   │
│  VaR (Historical)      4.81%      │  VaR         5.48%   │
│  CVaR (Expected...)    8.23%      │  CVaR        7.10%   │
│  Volatility (Ann.)    48.7%       │  Volatility  51.9%   │
└─────────────────────────────────────────────────────────┘
```

### What Each Metric Means

| Metric | Definition | Example |
|--------|------------|---------|
| **VaR (Parametric)** | Maximum loss assuming normal distribution | 5.08% = "There's a 5% chance of losing more than 5.08% tomorrow" |
| **VaR (Historical)** | Maximum loss based on actual historical data | Uses real past price movements |
| **CVaR (Expected Shortfall)** | Average loss when VaR is exceeded | "When things go bad, expect to lose ~8.23%" |
| **Volatility (Ann.)** | Annualized price fluctuation intensity | 48.7% = highly volatile |

### Risk Level Badges

| Badge | VaR Range | What It Means |
|-------|-----------|---------------|
| 🟢 **Low** | < 2% | Normal risk, no immediate action |
| 🟡 **High** | 2% - 5% | Elevated risk, monitor closely |
| 🔴 **Critical** | > 5% | High risk, hedging recommended |

### For Business Users

**"5.08% VaR at 95% confidence"** means:
- Tomorrow, you have a **95% chance** of NOT losing more than 5.08%
- There's a **5% chance** you could lose MORE than 5.08%
- If you have $1 million in EUR exposure, potential loss is $50,800

**When to worry:**
- VaR > 5% → Consider hedging
- CVaR significantly higher than VaR → Fat-tailed risk (extreme events more likely)
- Volatility > 40% → Very unstable market

### For Technical Users

**Parametric VaR Calculation:**
```
VaR = μ + z * σ
Where:
  μ = mean daily return
  z = z-score for confidence level (1.645 for 95%)
  σ = standard deviation of returns
```

**Historical VaR:**
- Sort historical returns
- Find the return at the (1 - confidence) percentile
- No distributional assumptions

**CVaR Calculation:**
```
CVaR = E[Loss | Loss > VaR]
Average of all losses exceeding the VaR threshold
```

---

## Stress Test Scenarios

Shows how your portfolio would perform during historical crisis events.

### Available Scenarios

| Scenario | Description | Historical Period |
|----------|-------------|-------------------|
| **2008 GFC** | Global Financial Crisis peak volatility | Sep-Nov 2008 |
| **Brexit Vote** | UK referendum shock | June 2016 |
| **COVID Crash** | Pandemic market selloff | March 2020 |
| **2022 Energy Crisis** | European energy crisis, USD strength | 2022 |
| **Fed Rate Shock** | Rapid Fed rate hike (+150bps) | 2022-2023 |

### Reading the Table

| Scenario | EUR | GBP | CAD |
|----------|-----|-----|-----|
| 2008 GFC | -8.5% ↘ | -15.2% ↘ | -18.7% ↘ |
| Brexit Vote | -3.2% ↘ | -11.8% ↘ | -2.1% ↘ |

### Color Coding

| Color | Range | Meaning |
|-------|-------|---------|
| 🔴 **Severe** | < -10% | Major loss |
| 🟠 **High** | -5% to -10% | Significant loss |
| 🟡 **Moderate** | -5% to 0% | Minor loss |
| 🟢 **Positive** | > 0% | Gain |

### For Business Users

**What this tells you:**
- "If another 2008-style crisis happens, EUR could drop 8.5%"
- Use this to size hedging positions
- GBP is most vulnerable to UK-specific events (Brexit: -11.8%)

**Action items:**
- If you have GBP exposure and fear political risk, hedge heavily
- CAD correlates with commodity prices (Energy Crisis: -5.8%)

### For Technical Users

- Data source: Historical exchange rate data during each crisis period
- Values represent the maximum drawdown during the crisis window
- Applied using historical simulation methodology

---

## Hedging Recommendations

AI-generated actionable insights based on current risk levels.

### Risk Status Banner

| Badge | Meaning |
|-------|---------|
| 🔴 **CRITICAL RISK** | Immediate hedging required |
| 🟠 **ELEVATED RISK** | Hedging recommended |
| 🟢 **NORMAL** | Standard monitoring |

### Currency Recommendations

Each currency shows:

```
EUR  [HEDGE] [Immediate]
Volatility at 48.7% (very high); VaR at 5.08% exceeds threshold
Suggested coverage: 100%    Confidence: 85%
[FX Forwards (1-3M)]  [Currency Options (puts)]
```

| Element | Meaning |
|---------|---------|
| **HEDGE** | Action recommendation |
| **Immediate** | Urgency level |
| **Suggested coverage: 100%** | Hedge your full exposure |
| **Confidence: 85%** | Model confidence in recommendation |
| **FX Forwards** | Recommended hedging instrument |
| **Currency Options** | Alternative hedging approach |

### Hedging Instruments Explained

| Instrument | Best For | Cost |
|------------|----------|------|
| **FX Forwards (1-3M)** | Locking in rates, certainty | Premium over spot |
| **Currency Options (puts)** | Downside protection + upside | Option premium |

### Cross-Currency Opportunities

```
Cross-Currency Opportunities
• EUR-GBP correlation is 0.96 - hedge only one for natural offset
• EUR-CAD correlation is 0.83 - hedge only one for natural offset
• GBP-CAD correlation is 0.82 - hedge only one for natural offset
```

**What this means:**
- If EUR and GBP move 96% together, hedging EUR partially hedges GBP
- You can save hedging costs by hedging only the larger exposure
- Natural offset reduces total portfolio risk

### For Business Users

**Recommended actions:**
1. Review the "HEDGE" currencies
2. Contact your bank/broker for FX forward quotes
3. For options, buy puts on currencies you're short

**Estimated risk reduction: 85%** - Following these recommendations would reduce your portfolio risk by approximately 85%.

### For Technical Users

- Recommendations generated by rule-based AI system
- Inputs: VaR levels, volatility, correlation matrix
- Thresholds: VaR > 2%, Volatility > 30% trigger hedge alerts
- Coverage calculation: Based on Kelly criterion and portfolio optimization

---

## Understanding Risk Levels

### Quick Reference

| Metric | Low Risk | Medium Risk | High Risk |
|--------|----------|-------------|-----------|
| **VaR (1-day)** | < 2% | 2% - 5% | > 5% |
| **CVaR** | < 3% | 3% - 8% | > 8% |
| **Volatility** | < 20% | 20% - 40% | > 40% |

### Formulas Reference

| Metric | Formula |
|--------|---------|
| **Daily Returns** | `ln(Price_t / Price_t-1)` |
| **Volatility (Ann.)** | `StdDev(Daily Returns) × √252` |
| **VaR (95%)** | `Mean + 1.645 × StdDev` |
| **VaR (99%)** | `Mean + 2.326 × StdDev` |

---

## Disclaimer

> **Risk metrics calculated using historical data. Past performance does not guarantee future results.**

Currency markets can experience extreme events not captured in historical data. Always consult with risk management professionals before making hedging decisions.

---

*Document Version: 1.0 | Last Updated: December 2025*
