# Changelog
All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [Unreleased]

## [1.0.0] - 2025-09-11
### Added
- LICENSE with MIT license and standardized license fields across packages
- Repository metadata and workspaces in root package.json
- ESLint (flat config) and Prettier configuration
- Python tooling configs: Black and Ruff via pyproject.toml
- Editor and repo configs: .editorconfig, .gitattributes, .nvmrc, .prettierrc.json
- GitHub Actions:
  - Node CI (lint/format checks and optional workspace builds)
  - Python CI (Ruff and Black checks)
  - CodeQL static analysis for JavaScript/TypeScript and Python
- Dependabot configuration for npm and GitHub Actions
- Community and security docs: CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md
- .gitkeep files to preserve character_files subdirectory structure

### Changed
- Updated .gitignore to allow committing lockfiles
- Enriched mcp-bridge and web-interface package.json with repo metadata, engines, and license

### Notes
- Lockfiles are now expected to be committed. Run npm install at the repository root to generate a workspace lockfile.
