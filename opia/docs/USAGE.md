# Usage Guide

## Table of Contents

- [Authentication](#authentication)
- [Provider Management](#provider-management)
- [Model Discovery](#model-discovery)
- [Session](#session)
- [Chat](#chat)
- [Tools](#tools)
- [Plugins](#plugins)
- [Configuration](#configuration)

---

## Authentication

### Login

Authenticate with an AI provider and store credentials securely:

```bash
# Interactive login (prompts for API key)
opia login groq

# Login with inline key
opia login groq --key sk-xxxxxxxx

# Login using environment variable (no prompt)
export GROQ_API_KEY="sk-..."
opia login groq
```

### Logout

Remove stored credentials:

```bash
# Logout from a specific provider
opia logout groq

# Logout from ALL providers
opia logout
```

### Check Status

```bash
opia whoami
```

Output:
```
┌─ Opia Session ─┐
│ Provider: groq │
│ Model:    default
│ Status:   authenticated
│ Last used: 2025-06-30T02:45:00+00:00
└────────────────┘
```

---

## Provider Management

### List Providers

```bash
opia provider list
```

Output:
```
┌──────────────┬──────────────┬──────┬──────────────────────────┬───────┐
│ Provider     │ Display Name │ Auth │ Default Model            │ OAuth │
├──────────────┼──────────────┼──────┼──────────────────────────┼───────┤
│ * groq       │ Groq         │ ✓    │ llama-3.3-70b-versatile │ —     │
│   openai     │ OpenAI       │ ✗    │ gpt-4o                   │ —     │
│   anthropic  │ Anthropic    │ ✗    │ claude-3-opus-20240229   │ —     │
│   ...        │ ...          │ ...  │ ...                      │ ...   │
└──────────────┴──────────────┴──────┴──────────────────────────┴───────┘
```

`*` = active provider

### Set Active Provider

```bash
opia provider use openai
```

### Show Provider Details

```bash
opia provider show groq
```

---

## Model Discovery

### List All Models

```bash
opia models list
```

### List Models for a Specific Provider

```bash
opia models list --provider groq
```

### Show Model Details

```bash
opia models show llama-3.3-70b-versatile
```

---

## Session

### Show Session

```bash
opia session show
```

### Clear Session

```bash
opia session clear
```

> Note: This clears the active session but does **not** delete stored credentials.

---

## Chat

### Single Message

```bash
opia chat "What is the meaning of life?"
```

### With a Specific Provider

```bash
opia chat "Explain Python decorators" --provider openai
```

### With a Specific Model

```bash
opia chat "Write a haiku" --model gpt-4o
```

### With a File Attachment

```bash
opia chat "Review this code" --file main.py
```

### Streaming Response

```bash
opia chat "Write a short story" --stream
```

### Interactive REPL

```bash
opia chat --interactive
# or just
opia chat
```

REPL commands:
- `:quit`, `:exit` — Leave the chat
- `:clear` — Clear conversation history
- `:help` — Show help

---

## Tools

### List Tools

```bash
opia tool list
```

### Execute a Tool

```bash
opia tool filesystem read=README.md
opia tool terminal execute="ls -la"
```

---

## Plugins

### List Plugins

```bash
opia plugin list
```

### Install a Plugin

```bash
opia plugin install /path/to/plugin
opia plugin install https://github.com/user/opia-plugin
```

### Load/Unload

```bash
opia plugin load my-plugin
opia plugin unload my-plugin
```

---

## Configuration

### Get Config

```bash
opia config get                    # Show all config
opia config get provider.default   # Get specific value
```

### Set Config

```bash
opia config set provider.default groq
opia config set chat.temperature 0.8
opia config set chat.max_tokens 4096
```

### Config File

Config is stored at `~/.opia/config.toml`:

```toml
[provider]
default = "groq"

[chat]
temperature = 0.8
max_tokens = 4096
```
