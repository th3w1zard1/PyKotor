# Security Policy

## Supported Versions

We actively support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.8.x   | :white_check_mark: |
| 1.7.x   | :white_check_mark: |
| < 1.7   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

### Preferred Method: GitHub Security Advisories
1. Go to [Security Advisories](https://github.com/th3w1zard1/PyKotor/security/advisories/new)
2. Click "New draft security advisory"
3. Fill out the form with details about the vulnerability

### Alternative: Email
If you prefer not to use GitHub's security advisory system, you can email security concerns to:
- **Email**: halomastar@gmail.com
- **Subject**: [SECURITY] PyKotor Vulnerability Report

## What to Include

When reporting a vulnerability, please include:

- **Description**: A clear description of the vulnerability
- **Impact**: What could an attacker do with this vulnerability?
- **Affected Packages**: Which PyKotor packages are affected?
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Proof of Concept**: If possible, provide a minimal proof of concept
- **Suggested Fix**: If you have ideas on how to fix it, please share them

## Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity, typically:
  - **Critical**: 24-48 hours
  - **High**: 1-2 weeks
  - **Medium**: 2-4 weeks
  - **Low**: Next release cycle

## Security Best Practices

### For Users

1. **Keep dependencies updated**: Regularly update PyKotor and its dependencies
2. **Use virtual environments**: Isolate your project dependencies
3. **Review code**: When using PyKotor in production, review the code you're using
4. **Report issues**: If you find a security issue, report it responsibly

### For Contributors

1. **Security reviews**: All code changes should be reviewed for security implications
2. **Dependency updates**: Keep dependencies updated and review security advisories
3. **Input validation**: Always validate and sanitize user input
4. **Secure defaults**: Use secure defaults in all configurations

## Security Considerations

### File Handling
- PyKotor processes game files which may come from untrusted sources
- Always validate file paths and content before processing
- Be cautious when extracting or writing files

### XML Processing
- Use the `secure_xml` extra to enable defusedxml for secure XML parsing
- Never parse XML from untrusted sources without defusedxml

### Encoding
- Use the `encodings` extra for charset-normalizer when processing untrusted text
- Always validate encoding before processing text data

## Disclosure Policy

- We follow responsible disclosure practices
- Vulnerabilities will be disclosed after a fix is available
- Credit will be given to reporters (unless they prefer to remain anonymous)
- A CVE will be requested for significant vulnerabilities

## Security Updates

Security updates will be:
- Released as patch versions (e.g., 1.8.0 → 1.8.1)
- Documented in release notes
- Tagged with security labels on GitHub
- Announced via GitHub releases

## Thank You

We appreciate your help in keeping PyKotor secure. Thank you for responsibly reporting vulnerabilities!

