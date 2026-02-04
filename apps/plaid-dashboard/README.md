# Plaid Dashboard

A lightweight personal finance dashboard powered by Plaid, built following Midday's architecture.

## Stack

- **Dashboard**: Next.js 15 + React 19 + Tailwind CSS
- **Engine API**: Hono + TypeScript
- **Database**: PostgreSQL + Drizzle ORM
- **Bank Integration**: Plaid API

## Quick Start

### 1. Prerequisites

- [Bun](https://bun.sh) (package manager)
- [Docker](https://docker.com) (for PostgreSQL)
- [Plaid Account](https://dashboard.plaid.com) (get API keys)

### 2. Setup Environment

```bash
cd apps/plaid-dashboard

# Copy environment template
cp .env.example .env

# Edit .env with your Plaid credentials
# PLAID_CLIENT_ID=your_client_id
# PLAID_SECRET=your_secret
# PLAID_ENVIRONMENT=sandbox
```

### 3. Start Database

```bash
docker-compose up -d
```

### 4. Install Dependencies

```bash
bun install
```

### 5. Run Migrations

```bash
cd db && bun run migrate
```

### 6. Start Development Servers

```bash
# Terminal 1: Start Engine API (port 3001)
cd engine && bun run dev

# Terminal 2: Start Dashboard (port 3000)
cd dashboard && bun run dev
```

### 7. Open Dashboard

Visit [http://localhost:3000](http://localhost:3000)

## Project Structure

```
plaid-dashboard/
├── dashboard/          # Next.js frontend
│   ├── src/
│   │   ├── app/       # Pages (home, accounts, transactions)
│   │   ├── actions/   # Server actions (Plaid link/exchange)
│   │   ├── components/# React components
│   │   └── lib/       # Utilities & API client
│   └── package.json
│
├── engine/            # Hono API backend
│   ├── src/
│   │   ├── providers/plaid/  # Plaid API wrapper
│   │   ├── routes/           # API endpoints
│   │   ├── services/         # Business logic
│   │   └── db/               # Database schema
│   └── package.json
│
├── db/                # Database package
│   ├── src/
│   │   ├── schema.ts # Drizzle schema
│   │   └── client.ts # DB connection
│   └── drizzle.config.ts
│
├── docker-compose.yml # Local PostgreSQL
├── turbo.json         # Monorepo config
└── package.json       # Workspace root
```

## API Endpoints

### Authentication
- `POST /auth/plaid/link` - Create Plaid Link token
- `POST /auth/plaid/exchange` - Exchange public token for access token

### Accounts
- `GET /accounts?accessToken=xxx` - Get accounts from Plaid
- `GET /accounts/balance?accessToken=xxx&accountId=xxx` - Get balance
- `GET /accounts/status?accessToken=xxx` - Check connection status

### Transactions
- `GET /transactions?accessToken=xxx` - Get transactions from Plaid
- `POST /transactions/sync` - Sync with cursor pagination

### Sync (Database)
- `POST /sync/connection` - Save new connection to database
- `POST /sync/refresh` - Refresh transactions for connection
- `GET /sync/connections` - Get all saved connections
- `GET /sync/transactions/:accountId` - Get transactions from DB

## Development

### Run All Services
```bash
# From plaid-dashboard root
bun run dev
```

### Database Commands
```bash
cd db
bun run generate  # Generate migrations
bun run migrate   # Apply migrations
bun run studio    # Open Drizzle Studio
```

## Plaid Sandbox Testing

In sandbox mode, use these test credentials:
- **Username**: `user_good`
- **Password**: `pass_good`
- **Institution**: Any bank (Chase, Bank of America, etc.)

See [Plaid Sandbox Docs](https://plaid.com/docs/sandbox/) for more test scenarios.

## Future Enhancements

- [ ] Webhooks for real-time updates
- [ ] Background sync jobs (Trigger.dev)
- [ ] Multi-user support
- [ ] Transaction categorization UI
- [ ] Spending charts & analytics
- [ ] Account reconnection flow
- [ ] Export to CSV

---

## Privacy Policy

**Effective Date:** December 22, 2025

### Introduction

Finance Guru ("we", "our", "us") is a personal finance dashboard that helps you track and manage your financial accounts. This Privacy Policy explains how we collect, use, and protect your information when you use our application.

### Information We Collect

**Financial Data (via Plaid)**
- Bank account names, types, and balances
- Transaction history (date, amount, merchant, category)
- Account and routing numbers (masked/encrypted)

**Technical Data**
- Session information
- Error logs for troubleshooting

### How We Use Your Information

Your financial data is used exclusively to:
- Display your account balances and transactions
- Provide budgeting and financial analysis features
- Sync and refresh your financial information

**We do NOT:**
- Sell your data to third parties
- Share your data with advertisers
- Use your data for marketing purposes
- Store your bank login credentials

### Data Security

- All data is encrypted at rest (AES-256) and in transit (TLS 1.3)
- Plaid access tokens are stored securely and never exposed to clients
- We never store your bank username or password
- Access to production systems requires multi-factor authentication

### Data Retention

| Data Type | Retention Period |
|-----------|-----------------|
| Transaction history | 24 months |
| Account balances | 90 days |
| Session logs | 90 days |
| Plaid tokens | Duration of connection |

### Your Rights

You have the right to:
- **Access** your data at any time through the dashboard
- **Delete** your data by disconnecting your accounts
- **Request** a copy of your stored data
- **Withdraw** consent by removing bank connections

### Data Deletion

To delete your data:
1. Disconnect your bank accounts in the dashboard
2. Contact support@example.com for full data removal
3. We will process deletion requests within 30 days

### Third-Party Services

We use [Plaid](https://plaid.com) to securely connect to your financial institutions. Plaid's privacy policy is available at [plaid.com/legal](https://plaid.com/legal).

### California Privacy Rights (CCPA)

California residents have additional rights including the right to know what personal information is collected and to request deletion. We do not sell personal information.

### Changes to This Policy

We may update this Privacy Policy periodically. Significant changes will be communicated through the application.

### Contact

For privacy questions or data requests:
- **Email:** support@example.com
- **Response Time:** Within 5 business days

---

*This application is for personal use only and does not constitute financial advice. Consult a qualified financial professional for investment decisions.*
