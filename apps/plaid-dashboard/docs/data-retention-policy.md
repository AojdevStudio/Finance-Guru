# Finance Guru Data Deletion and Retention Policy

**Effective Date:** December 22, 2025
**Last Reviewed:** December 22, 2025
**Next Review Date:** June 22, 2026
**Policy Owner:** Finance Guru Development Team

---

## 1. Purpose

This policy establishes guidelines for the retention and deletion of user data collected through Finance Guru's integration with Plaid and other financial data services. It ensures compliance with applicable data privacy laws including the California Consumer Privacy Act (CCPA) and incorporates GDPR best practices.

---

## 2. Scope

This policy applies to all personal and financial data collected, processed, and stored by Finance Guru, including:

- Bank account information (account names, types, balances)
- Transaction history and metadata
- User authentication tokens and credentials
- Plaid access tokens and item IDs
- User profile information

---

## 3. Data Categories and Retention Periods

### 3.1 Financial Data (from Plaid)

| Data Type | Retention Period | Justification |
|-----------|------------------|---------------|
| Account balances | 90 days | Operational necessity for balance tracking |
| Transaction history | 24 months | Budgeting and financial analysis features |
| Account metadata | Duration of connection | Required for active bank connections |
| Plaid access tokens | Duration of connection | Required for API access |

### 3.2 User Data

| Data Type | Retention Period | Justification |
|-----------|------------------|---------------|
| User profile | Duration of account + 30 days | Account functionality |
| Authentication data | Duration of account | Security requirements |
| Session logs | 90 days | Security and debugging |
| Error logs | 30 days | Technical troubleshooting |

### 3.3 Aggregated/Anonymized Data

Anonymized, aggregated data used for application improvement may be retained indefinitely as it cannot be linked to individual users.

---

## 4. Data Deletion Procedures

### 4.1 User-Initiated Deletion

Users may request deletion of their data at any time by:

1. Disconnecting their bank accounts through the Finance Guru dashboard
2. Contacting support at support@example.com
3. Submitting a written request

**Response Timeline:** All deletion requests will be processed within 30 days.

### 4.2 Automatic Deletion

The system automatically deletes:

- **Stale connections:** Bank connections inactive for 12+ months
- **Expired tokens:** Plaid tokens that have been revoked or expired
- **Session data:** Sessions older than 90 days
- **Temporary files:** Processing cache cleared within 24 hours

### 4.3 Deletion Process

When data is deleted:

1. **Soft delete:** Data is marked for deletion and removed from active systems
2. **Hard delete:** Data is permanently removed from databases within 7 days
3. **Backup purge:** Data is removed from backups within 30 days
4. **Plaid disconnection:** Access tokens are revoked via Plaid API

### 4.4 Plaid Token Revocation

When a user disconnects a bank account or deletes their account:

```
1. Call Plaid /item/remove endpoint to revoke access token
2. Delete stored access token from local database
3. Delete associated account and transaction data
4. Log deletion event for audit trail
```

---

## 5. Data Minimization

Finance Guru adheres to data minimization principles:

- **Collect only necessary data:** Only data required for stated features is collected
- **No data selling:** User financial data is never sold or shared with third parties
- **Limited access:** Data access is restricted to essential application functions
- **Purpose limitation:** Data is used only for the purposes disclosed to users

---

## 6. Legal Compliance

### 6.1 California Consumer Privacy Act (CCPA)

Users have the right to:
- Know what personal information is collected
- Request deletion of personal information
- Opt-out of sale of personal information (N/A - we do not sell data)
- Non-discrimination for exercising privacy rights

### 6.2 Financial Data Protection

- All financial data is encrypted at rest (AES-256)
- All data in transit uses TLS 1.3
- Access tokens are stored securely and never exposed to client applications
- No financial credentials (usernames/passwords) are stored

---

## 7. Policy Review Schedule

This policy is reviewed:

- **Semi-annually:** Every 6 months (June and December)
- **After incidents:** Following any data breach or security incident
- **Regulatory changes:** When relevant privacy laws are updated
- **Product changes:** When new features affect data handling

### Review Checklist

- [ ] Verify retention periods align with business needs
- [ ] Confirm deletion procedures are functioning
- [ ] Review compliance with current regulations
- [ ] Update contact information if changed
- [ ] Test data deletion workflows
- [ ] Audit access logs

---

## 8. Contact Information

For questions about this policy or to submit a data deletion request:

**Email:** support@example.com
**Response Time:** Within 5 business days

---

## 9. Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-12-22 | Initial policy creation | Finance Guru Team |

---

*This policy is maintained as part of Finance Guru's commitment to user privacy and data protection.*
