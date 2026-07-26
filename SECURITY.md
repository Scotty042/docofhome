# Security Policy

## Supported versions

JARVIS is currently pre-alpha. Only the newest commit is supported.

## Intended deployment

Version 1 has no authentication and is designed for a trusted private network only. Do not expose it directly to the public internet.

## Reporting a vulnerability

Please report vulnerabilities privately to the repository maintainer rather than opening a public issue. Never include real tokens, credentials, private URLs, IP addresses, database files, or backups in reports.

## Secrets

Secrets must not be committed to Git. The repository ignores `.env`, databases, tokens, keys, certificates, runtime data, logs, and backups. Integrations must redact credentials from API responses and logs.
