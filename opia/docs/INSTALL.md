# Installation Guide

## Requirements

- **Python 3.11 or later**
- **pip** (or `pipx`, `poetry`, `uv`)

## Quick Install

### From PyPI (when published)

```bash
pip install opia
```

### From Source

```bash
git clone https://github.com/Chieji/opia.git
cd opia
pip install -e ".[dev]"
```

## Platform-Specific Notes

### macOS

No special steps needed. The keyring library will use the macOS Keychain automatically.

### Linux

For secure credential storage, install the D-Bus Secret Service backend:

```bash
# Debian/Ubuntu
sudo apt install libsecret-1-0

# Or use the encrypted file fallback (no extra deps needed)
```

### Windows

The keyring library will use the Windows Credential Manager automatically.

## Verification

After installation, verify it works:

```bash
opia --version
# Output: Opia v0.1.0

opia provider list
# Should show all 9 configured providers
```

## First-Time Setup

1. **Authenticate with a provider:**

```bash
opia login groq
# Enter your API key when prompted
```

2. **Set a default provider:**

```bash
opia provider use groq
```

3. **Start chatting:**

```bash
opia chat "Hello, world!"
```

## Environment Variables

Instead of `opia login`, you can set environment variables:

```bash
export GROQ_API_KEY="sk-..."
export OPENAI_API_KEY="sk-..."
```

Opia will automatically detect these. No `login` needed.

## Upgrade

```bash
pip install --upgrade opia
```

## Uninstall

```bash
pip uninstall opia
# Remove config and credentials
rm -rf ~/.opia
```
