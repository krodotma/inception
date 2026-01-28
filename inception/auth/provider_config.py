# Auth Provider Configuration
# This file defines the authentication strategy for LLM providers in Inception.

# =============================================================================
# GENERAL RULE: NO API KEYS
# =============================================================================
# Default policy: Use subscription-based OAuth, NOT pay-per-token API keys.
# This ensures we use existing Claude Max, Gemini Ultra, GPT Plus subscriptions.

# =============================================================================
# API KEYS WHITELIST (Exceptions)
# =============================================================================
# Some providers ONLY support API keys (no OAuth/subscription option).
# These are explicitly whitelisted exceptions to the "no API keys" rule.

API_KEYS_WHITELIST = [
    "kimi",           # Moonshot AI - only supports MOONSHOT_API_KEY or KIMI_API_KEY
    "openrouter",     # OpenRouter - fallback aggregator, requires OPENROUTER_API_KEY
    "deepseek",       # DeepSeek - only supports DEEPSEEK_API_KEY
    "qwen",           # Qwen/Alibaba - only supports API key auth
]

# =============================================================================
# SUBSCRIPTION PROVIDERS (Primary - NO API keys)
# =============================================================================
# These providers support subscription OAuth via CLI tools.
# NEVER use API keys for these - use subscription auth instead.

SUBSCRIPTION_PROVIDERS = [
    "claude",         # Claude Max via `claude` CLI (Anthropic subscription)
    "gemini",         # Gemini Ultra via `gemini` CLI (Google subscription)
    "codex",          # Codex via `codex` CLI (OpenAI subscription)
    "chatgpt",        # ChatGPT Plus via subscription
]

# =============================================================================
# PROVIDER PRIORITY ORDER
# =============================================================================
# When auto-selecting a provider, try in this order:

PROVIDER_PRIORITY = [
    # 1. Subscription-based (FREE via subscription)
    "claude",         # Claude Opus 4.5 via subscription
    "gemini",         # Gemini 2.5 Flash via subscription
    "codex",          # Codex via subscription
    
    # 2. API key whitelist (when subscription not available)
    "kimi",           # Kimi k1.5 (API key from KIMI_API_KEY)
    
    # 3. Fallback aggregator
    "openrouter",     # OpenRouter (API key fallback)
]

# =============================================================================
# ENV VAR MAPPING
# =============================================================================
# For whitelisted API key providers, these are the expected env vars:

API_KEY_ENV_VARS = {
    "kimi": ["KIMI_API_KEY", "MOONSHOT_API_KEY"],
    "openrouter": ["OPENROUTER_API_KEY"],
    "deepseek": ["DEEPSEEK_API_KEY"],
    "qwen": ["QWEN_API_KEY", "DASHSCOPE_API_KEY"],
}
