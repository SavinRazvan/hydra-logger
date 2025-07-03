# Security Policy

## Supported Versions

Use this section to tell people about which versions of your project are currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability in Hydra-Logger, please follow these steps:

### 🚨 Immediate Steps

1. **DO NOT** create a public GitHub issue for the vulnerability
2. **DO NOT** discuss the vulnerability in public forums or social media
3. **DO** report it privately using one of the methods below

### 📧 Reporting Methods

#### Option 1: Email (Recommended)
Send a detailed report to: **razvan.i.savin@gmail.com**

#### Option 2: Private GitHub Issue
Create a private issue by:
1. Going to the [Issues page](https://github.com/SavinRazvan/hydra-logger/issues)
2. Click "New issue"
3. Select "Security vulnerability" template
4. Fill out the details

### 📋 What to Include

Please include the following information in your report:

- **Description**: Clear description of the vulnerability
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Impact**: Potential impact of the vulnerability
- **Environment**: OS, Python version, Hydra-Logger version
- **Code Example**: Minimal code example demonstrating the issue
- **Suggested Fix**: If you have ideas for fixing the issue

### ⏱️ Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 1 week
- **Fix Timeline**: Depends on severity and complexity
- **Public Disclosure**: After fix is available

## 🔒 Security Best Practices

### For Users

1. **Keep Updated**: Always use the latest stable version
2. **Review Configurations**: Validate your logging configurations
3. **Monitor Logs**: Regularly check log files for sensitive information
4. **Secure File Permissions**: Ensure log files have appropriate permissions
5. **Network Security**: If using remote logging, secure network connections

### For Developers

1. **Input Validation**: Always validate configuration inputs
2. **File Path Security**: Prevent path traversal attacks
3. **Error Handling**: Don't expose sensitive information in error messages
4. **Dependencies**: Keep dependencies updated and scan for vulnerabilities
5. **Code Review**: Review code for security issues before merging

## 🛡️ Security Features

Hydra-Logger includes several security features:

- **Input Validation**: All configuration inputs are validated using Pydantic
- **Path Sanitization**: File paths are validated to prevent traversal attacks
- **Error Handling**: Sensitive information is not exposed in error messages
- **Type Safety**: Type hints help prevent security-related bugs
- **Dependency Management**: Minimal, well-maintained dependencies

## 🔍 Security Scanning

We regularly scan our codebase for security issues:

- **Bandit**: Static analysis for common security issues
- **Safety**: Dependency vulnerability scanning
- **CodeQL**: GitHub's semantic code analysis
- **Manual Review**: Regular security code reviews

## 📚 Security Resources

- [OWASP Python Security](https://owasp.org/www-project-python-security-top-10/)
- [Python Security Best Practices](https://python-security.readthedocs.io/)
- [Common Weakness Enumeration (CWE)](https://cwe.mitre.org/)

## 🤝 Responsible Disclosure

We appreciate security researchers who follow responsible disclosure practices:

1. **Private Reporting**: Report vulnerabilities privately first
2. **Reasonable Timeline**: Allow time for fixes to be developed
3. **Coordinated Disclosure**: Work with us on disclosure timing
4. **No Exploitation**: Don't exploit vulnerabilities in production systems

## 🏆 Recognition

Security researchers who report valid vulnerabilities will be:

- Listed in our [SECURITY.md](SECURITY.md) file
- Acknowledged in release notes
- Given credit in the [CHANGELOG.md](CHANGELOG.md)

## 📞 Contact

For security-related questions or concerns:

- **Security Email**: razvan.i.savin@gmail.com
- **GitHub Issues**: Use the security vulnerability template
- **Documentation**: Check our [security documentation](docs/security.md)

Thank you for helping keep Hydra-Logger secure! 🔒 