# Security Policy

## Supported Versions

Specifically, for security updates, only the latest major release (1.x) is currently supported.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of `alembic-autoscan` seriously. If you discover a security vulnerability within this project, please do not report it publicly through the GitHub issue tracker.

Instead, please report it via one of the following methods:

1. **GitHub Private Vulnerability Reporting**: Use the [GitHub Security Advisory](https://github.com/tonlls/alembic-autoscan/security/advisories/new) feature to report the vulnerability privately.
2. **Email**: Send an email to [tonlls@users.noreply.github.com](mailto:tonlls@users.noreply.github.com) with a detailed description of the vulnerability and steps to reproduce it.

### What to expect

- We will acknowledge receipt of your report within 48 hours.
- We will provide an estimated timeline for a fix.
- Once a fix is verified, it will be released in a new version, and you will be credited for the discovery (unless you prefer to remain anonymous).

## Security Measures

To ensure the security of this project, we employ the following automated tools in our CI/CD pipeline:

- **Bandit**: Scans for common security issues in Python code.
- **Safety**: Checks for known vulnerabilities in dependencies.
- **Ruff**: Enforces high-quality code standards with security rules enabled.
- **Mypy**: Performs static type checking to prevent type-related bugs.

Every Pull Request is automatically scanned before being merged to the `main` or `development` branches.
