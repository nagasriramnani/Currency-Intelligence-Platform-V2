# Settings Page
## Complete Walkthrough Guide

This guide explains every section of the **Settings** page in the Sapphire Intelligence Platform. Written for both administrators and end users.

---

## 📊 Table of Contents

1. [Settings Overview](#settings-overview)
2. [General Settings](#general-settings)
3. [Appearance](#appearance)
4. [Notifications](#notifications)
5. [API Keys](#api-keys)
6. [Data Sources](#data-sources)
7. [Security](#security)

---

## Settings Overview

The Settings page allows you to configure your platform preferences, manage integrations, and control security settings.

### Sidebar Navigation

| Section | Purpose | Icon |
|---------|---------|------|
| **General** | Default currency, timezone, language | ⚙️ |
| **Appearance** | Theme colors, display modes | 🎨 |
| **Notifications** | Alert preferences, Slack integration | 🔔 |
| **API Keys** | Manage access tokens | 🔑 |
| **Data Sources** | External data connections | 🗄️ |
| **Security** | 2FA, session management | 🛡️ |

---

## General Settings

Configure your default preferences for the platform.

### Default Currency

| Option | Description |
|--------|-------------|
| **$ USD - US Dollar** | United States Dollar (default) |
| **€ EUR - Euro** | European Union Euro |
| **£ GBP - British Pound** | United Kingdom Pound Sterling |
| **¥ JPY - Japanese Yen** | Japanese Yen |
| **Fr CHF - Swiss Franc** | Swiss Franc |

**What it affects:**
- Base currency for all calculations
- Default display currency in KPI cards
- Portfolio valuation base

### Timezone

| Option | UTC Offset |
|--------|------------|
| **Eastern Time (ET)** | UTC-5 / UTC-4 (DST) |
| **Central Time (CT)** | UTC-6 / UTC-5 (DST) |
| **Pacific Time (PT)** | UTC-8 / UTC-7 (DST) |
| **London (GMT)** | UTC+0 / UTC+1 (DST) |
| **Central European (CET)** | UTC+1 / UTC+2 (DST) |
| **Japan (JST)** | UTC+9 |

**What it affects:**
- Scheduled report delivery times
- Alert timestamps
- "Last Updated" display time

### Language

| Option | Language |
|--------|----------|
| **English (US)** | American English (default) |
| **English (UK)** | British English |
| **Español** | Spanish |
| **Français** | French |
| **Deutsch** | German |

---

## Appearance

Customize the look and feel of the platform.

### Theme Accent Color

The accent color changes buttons, icons, active states, and highlights across all pages.

| Theme | Color | Best For |
|-------|-------|----------|
| **Sapphire** | Blue | Default, professional look |
| **Emerald** | Green | Finance-focused, growth theme |
| **Violet** | Purple | Modern, creative environments |
| **Rose** | Red/Pink | Alert-focused, attention-grabbing |

**How to change:**
1. Click on a theme card
2. The checkmark (✓) shows current selection
3. Theme applies immediately across all pages
4. Persists across sessions (saved to browser)

### Additional Options

| Setting | Description | Default |
|---------|-------------|---------|
| **Compact Mode** | Reduce spacing for more data density | Off |
| **Animations** | Enable micro-animations and transitions | On |

---

## Notifications

Configure alerts and delivery preferences.

### Alert Types

| Alert | Description | Trigger |
|-------|-------------|---------|
| **Volatility Alerts** | Currency volatility spikes | Exceeds 2 standard deviations |
| **Price Alerts** | Currency hits target price | User-defined price levels |
| **Forecast Updates** | New predictions generated | Model retraining complete |

### Delivery Channels

| Channel | Description | Setup Required |
|---------|-------------|----------------|
| **Email Notifications** | Send to registered email | Email address |
| **Push Notifications** | Browser notifications | Browser permission |
| **Daily Digest** | Summary email at 8:00 AM | Email address |

### Slack Integration

Connect the platform to your Slack workspace for real-time alerts.

**Current Webhook:**
```
https://hooks.slack.com/services/YOUR_WORKSPACE/YOUR_CHANNEL/YOUR_SECRET
```

**Setup Steps:**
1. Go to your Slack workspace settings
2. Create an Incoming Webhook
3. Paste the webhook URL in the Settings page
4. Click "Test" to verify connection

**What you'll receive in Slack:**
- VaR breach alerts
- Volatility spike notifications
- Daily market summaries

---

## API Keys

Manage your API access tokens for programmatic access.

### Current Keys

| Key Name | Purpose | Created |
|----------|---------|---------|
| **FMP API Key** | Financial Modeling Prep data access | Dec 14, 2025 |
| **Slack Webhook URL** | Slack alert integration | Dec 14, 2025 |
| **Supabase URL** | Database connection endpoint | Dec 14, 2025 |
| **Supabase Anon Key** | Database authentication | Dec 14, 2025 |

### Key Details

#### FMP API Key
```
your_fmp_api_key_here
```
- **Source:** Financial Modeling Prep
- **Tier:** Free Tier
- **Rate Limit:** 250 requests/day
- **Used For:** Exchange rates, historical data

#### Slack Webhook URL
```
https://hooks.slack.com/services/YOUR_WORKSPACE/YOUR_CHANNEL/YOUR_SECRET
```
- **Workspace:** Your Slack team
- **Channel:** Configured in Slack
- **Used For:** Real-time alerts

#### Supabase Credentials
```
URL: https://eepxywpskwjijxbroeoi.supabase.co
Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
- **Project:** Currency Intelligence Platform
- **Features:** Auth, Database, Real-time
- **Used For:** Data persistence, user sessions

### Key Management Features

| Button | Action |
|--------|--------|
| **👁️ Eye Icon** | Show/hide key value |
| **📋 Copy Icon** | Copy key to clipboard |
| **⚡ Generate New Key** | Create new API key |

### Security Notice

> ⚠️ **Keep your API keys secure. Never share them or commit them to version control. Rotate keys regularly for enhanced security.**

---

## Data Sources

Manage external data connections.

### Connected Sources

| Source | Status | Tier | Last Sync |
|--------|--------|------|-----------|
| **Financial Modeling Prep** | 🟢 Connected | Free Tier | 2 min ago |
| **U.S. Treasury Fiscal Data** | 🟢 Connected | Public API | 5 min ago |

### Status Indicators

| Status | Icon | Meaning |
|--------|------|---------|
| **Connected** | 🟢 | Active and syncing |
| **Disconnected** | ⚪ | Not currently connected |
| **Error** | 🔴 | Connection failed |

### Adding New Sources

Click **"+ Add New Data Source"** to connect:
- Alpha Vantage (Premium)
- Reuters Eikon (Enterprise)
- Bloomberg Terminal (Enterprise)
- Custom REST API

---

## Security

Protect your account and manage access.

### Two-Factor Authentication (2FA)

| Setting | Description |
|---------|-------------|
| **Enable 2FA** | Add authenticator app verification |
| **Status** | Currently: Disabled |

**Recommended:** Enable 2FA for admin accounts.

### Session Timeout

| Option | Description |
|--------|-------------|
| **15 minutes** | High security environments |
| **30 minutes** | Default setting |
| **1 hour** | Standard office use |
| **4 hours** | Low-risk environments |

### Recent Activity

Monitor login history and security events:

| Event | Time | IP Address |
|-------|------|------------|
| Login from Chrome on Windows | 2 hours ago | 192.168.1.1 |
| API key generated | 3 days ago | 192.168.1.1 |
| Password changed | 1 week ago | 10.0.0.5 |

### Security Actions

| Button | Action |
|--------|--------|
| **Sign Out All Devices** | Force logout everywhere |

---

## Configuration Files

For technical users, these environment variables should be set:

### Backend (.env file)

```bash
# API Keys
FMP_API_KEY=your_fmp_api_key_here

# Slack Integration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Supabase Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

### Frontend (.env.local file)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://eepxywpskwjijxbroeoi.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| Theme not applying | Refresh browser, clear cache |
| Slack alerts not working | Test webhook URL, check channel permissions |
| Data not updating | Check API key status, verify rate limits |
| Session expiring quickly | Increase timeout in Security settings |

---

*Document Version: 1.0 | Last Updated: December 2025*
