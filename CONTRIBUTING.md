# Contributing to Agentic World

Thanks for your interest in improving Agentic World. This guide explains how to set up your environment, make changes, and submit contributions.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Development Workflow](#development-workflow)
- [Linting and Formatting](#linting-and-formatting)
- [Testing and CI](#testing-and-ci)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Security](#security)
- [License](#license)

## Code of Conduct
By participating, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## Project Structure
- Root: Node workspace and Python scripts (simulation, orchestration, AWS helpers)
- `mcp-bridge/`: WebSocket bridge for Unreal MCP to telemetry
- `web-interface/`: Express-based web interface and assets
- `viewer/`: Static viewer pages and media
- `aws/`: CloudFormation templates and scripts
- `docs/`: Documentation and runbooks
- `character_files/`: Character folders (intentionally empty in git; only structure is tracked)

## Prerequisites
- Node.js: v18+ (see `.nvmrc`)
- npm: v9+ (npm v10+ recommended)
- Python: 3.11+ (for tooling and scripts)

## Setup
Install dependencies (workspace-aware):
```bash
# Use Node 18 if you have nvm
nvm use || true

# Install root + workspaces
npm install
```

## Development Workflow
Typical commands:
```bash
# Run control server
npm start

# Lint JS/TS and check formatting
npm run check

# Auto-fix JS issues
npm run lint:fix
npm run format

# Python lint/format checks
npm run py:check
# or separate:
npm run py:lint
npm run py:format
```

Workspace-specific scripts:
```bash
# Web interface (Express)
npm -w web-interface run start

# Bridge
npm -w mcp-bridge run start
```

## Linting and Formatting
- JavaScript: ESLint (flat config) + Prettier
- Python: Ruff + Black
- Editor auto-formatting is encouraged. See `.editorconfig`, `.prettierrc.json`, and `pyproject.toml`.

## Testing and CI
- CI runs on GitHub Actions:
  - Node CI: install, lint, format check, optional builds
  - Python CI: Ruff and Black checks
  - CodeQL: Security static analysis
  - Dependabot: Weekly dependency updates
Ensure `npm run check` and Python checks pass before opening a PR.

## Commit Messages
Use clear, conventional messages:
- feat: add new feature
- fix: bug fix
- docs: documentation updates
- chore: tooling or maintenance
- refactor: code changes that neither fix a bug nor add a feature

Example:
```
feat(web): add telemetry status endpoint
```

## Pull Request Process
1. Create a feature branch from `main`.
2. Ensure local checks pass: `npm run check` and `npm run py:check`.
3. Update docs if behavior changes (README, docs/).
4. Request review. Link any related issues.

## Security
Do not include secrets in code or commits. See [SECURITY.md](SECURITY.md) for how to report vulnerabilities.

## License
By contributing, you agree your contributions are licensed under the repository’s [MIT License](LICENSE).
