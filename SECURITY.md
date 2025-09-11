# Security Policy

We take the security of this project seriously. If you discover a security vulnerability, please follow the steps below.

## Reporting a Vulnerability

- Do NOT open a public GitHub issue for security-related matters.
- Preferred: Use GitHub Security Advisories to privately report a vulnerability:
  - Navigate to the repository Security tab
  - Click "Report a vulnerability"
- Alternatively: Email the maintainers via a private channel if available on the repo profile.

Please include:
- A detailed description of the vulnerability and potential impact
- Steps to reproduce (PoC if possible)
- Affected versions/commit
- Any known mitigations or workarounds

We will acknowledge receipt within 72 hours, assess the report, and provide a target timeline for a fix if the issue is confirmed.

## Supported Versions

This is a community project under active development. We aim to patch the latest `main` branch and create a release as needed. Older tags are not guaranteed to receive fixes.

## Security Best Practices for Contributors

- Never commit secrets (API keys, credentials, tokens). Use environment variables and `.env` files (already ignored).
- Validate and sanitize external inputs. Treat all network data as untrusted.
- Prefer least-privilege IAM and scoped credentials for any AWS resources.
- Review CI logs before publishing to ensure they contain no sensitive data.
- Use `npm audit` (or GitHub advisories) to stay aware of vulnerable dependencies.
