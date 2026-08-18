# Security Policy

## Reporting a Vulnerability

We take security seriously. If you find a security problem in the
Profitelligence MCP server or the hosted endpoint at
`mcp.profitelligence.com`, report it responsibly.

### How to Report

**Do not** create a public GitHub issue for security vulnerabilities.

Email us at **security@profitelligence.com** and include:

- A description of the vulnerability
- Steps to reproduce it
- The potential impact
- Suggested fixes (optional)

### What to Expect

1. **Acknowledgment** — we acknowledge receipt within 48 hours
2. **Assessment** — we assess severity and impact within 7 days
3. **Resolution** — we fix the problem and coordinate disclosure
4. **Credit** — with your permission, we credit you in the advisory

### Scope

This policy covers:

- The hosted MCP endpoint (`mcp.profitelligence.com`)
- The OAuth authorization server (`auth.profitelligence.com`)
- The Profitelligence API backend

Out of scope:

- Third-party dependencies (report to their maintainers)
- Social engineering attacks

## Security Best Practices for Users

### API Key Security

- **Never commit API keys** to version control
- Use environment variables or a secret manager
- Rotate keys periodically from your [dashboard](https://profitelligence.com/account/api-keys)
- Revoke a key immediately if you suspect exposure

### OAuth Security

- The hosted server supports OAuth 2.1; clients such as Claude handle the
  flow automatically
- Never log or share access tokens

## Data Sensitivity

The MCP server provides access to:

- Public market data
- SEC filing data (public information)
- Economic indicators (public FRED data)

The server is read-only. It cannot modify your account or execute trades.

## Acknowledgments

We appreciate the security research community. Responsible disclosure helps
keep everyone safe.
