# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in the Profitelligence MCP Server, please report it responsibly.

### How to Report

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please email us at: **security@profitelligence.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes (optional)

### What to Expect

1. **Acknowledgment**: We'll acknowledge receipt within 48 hours
2. **Assessment**: We'll assess the severity and impact within 7 days
3. **Resolution**: We'll work on a fix and coordinate disclosure
4. **Credit**: With your permission, we'll credit you in the security advisory

### Scope

This security policy covers:
- The Profitelligence MCP Server codebase
- Docker images published to Docker Hub
- Official deployment configurations

Out of scope:
- The Profitelligence API backend (report separately to security@profitelligence.com)
- Third-party dependencies (report to their maintainers)
- Social engineering attacks

## Security Best Practices for Users

### API Key Security

- **Never commit API keys** to version control
- Use environment variables or secure secret management
- Rotate keys periodically
- Use test keys (`pk_test_*`) for development

```bash
# Good: Environment variable
export PROF_API_KEY="pk_live_..."

# Bad: Hardcoded in config files
PROF_API_KEY="pk_live_..." # Don't do this in committed files
```

### Docker Security

When running the Docker container:

```bash
# Good: Pass API key via environment
docker run -e PROF_API_KEY="$PROF_API_KEY" profitelligence/mcp-server

# Good: Use Docker secrets (Swarm/Kubernetes)
docker service create --secret prof_api_key ...

# Bad: API key in docker-compose.yml committed to git
```

### OAuth Security

When using OAuth 2.1 authentication:
- Use HTTPS for all OAuth flows
- Store tokens securely
- Implement proper token refresh handling
- Never log or expose tokens

### Network Security

- Run in HTTP mode only on trusted networks or behind a reverse proxy
- Use TLS termination (nginx, Caddy, cloud load balancer) for production
- Consider network policies to restrict access

## Known Security Considerations

### Data Sensitivity

The MCP server provides access to:
- Public market data
- SEC filing data (public information)
- Economic indicators (public FRED data)

No PII or non-public information is transmitted through this server.

### Authentication Methods

| Method | Security Level | Use Case |
|--------|---------------|----------|
| API Key | Good | Simple deployments, CI/CD |
| OAuth 2.1 | Better | Interactive clients, browser-based |
| Firebase JWT | Good | Legacy integrations |

### Dependency Security

We regularly update dependencies to address known vulnerabilities. Check `pyproject.toml` for current versions.

To audit dependencies:
```bash
pip install pip-audit
pip-audit
```

## Security Updates

Security updates are released as patch versions (e.g., 0.1.1, 0.1.2).

Subscribe to:
- GitHub releases for notifications
- Docker Hub for image updates

## Acknowledgments

We appreciate the security research community. Responsible disclosure helps keep everyone safe.

---

Last updated: December 2024
