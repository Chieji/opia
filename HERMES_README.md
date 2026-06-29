# Opia — Hermes Integration Notes

## Architecture
- `opia/providers/`: Pluggable provider implementations (Anthropic, OpenAI, Gemini, Mistral, Groq, etc.) with async support for both sync and async APIs.
- `opia/router/`: Chat router that selects and invokes providers based on models/routing rules.
- `opia/auth/`: Authentication layer that stores, validates, and manages credentials per provider.

## Auth Flow
1. `login <provider>` — validates credentials via provider API and stores them securely through `CredentialStorage`.
2. `logout` — removes stored credentials from the active provider or all providers.
3. `validate` — re-checks stored credentials against the provider before a request.
4. Session tracking (`SessionManager`) keeps track of active provider/model and auth status for future requests.

## Entrypoints
- `opia/__init__.py`: package metadata.
- Tests live under `opia/tests/`.
