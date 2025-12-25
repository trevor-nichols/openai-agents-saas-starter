# Starter Providers

Cloud provider SDK helpers shared across the backend and the Starter Console.

This package intentionally hosts concrete SDK clients (AWS Secrets Manager,
Azure Key Vault, Infisical) so `starter_contracts` can stay dependency-light
and import-safe.
