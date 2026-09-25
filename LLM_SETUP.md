# Configuring LLM Endpoints in LoomFlow

LoomFlow's Synthesizer feature is built to be flexible and provider-agnostic. By default, it supports local models (like Ollama or LM Studio) and Google Gemini, but you can configure it to work with *any* OpenAI-compatible API (such as OpenRouter, Groq, Together AI, or vLLM).

## Option 1: Configuring via the UI (Recommended for Custom Models)

When using the LoomFlow Synthesizer in the canvas:
1. Open the Synthesizer Drawer (🪄 icon in the header).
2. Under **Model Provider**, select **Custom OpenAI-Compatible Endpoint**.
3. Fill in the following fields:
   - **Base URL**: The base URL of the API (e.g., `https://openrouter.ai/api/v1` or `https://api.groq.com/openai/v1`).
   - **API Key**: Your API key for the service.
   - **Model Name**: The specific model string you want to use (e.g., `anthropic/claude-3.5-sonnet` or `llama3-70b-8192`).

This method allows you to quickly swap between different cloud models without restarting the backend.

## Option 2: Configuring via `.env` (Global Defaults)

If you have a default local or custom OpenAI-compatible server that you want to always use when "Local Model" is selected, you can configure it in `backend/.env`.

```env
DEFAULT_LLM_PROVIDER=local
LOCAL_LLM_BASE_URL="http://localhost:1234/v1" # e.g. LM Studio
LOCAL_LLM_API_KEY="not-needed"
LOCAL_LLM_MODEL="local-model"

# For Gemini 2.5 Pro
GEMINI_API_KEY="your-gemini-api-key"
```

### Examples for `.env` Defaults:

#### Ollama (Local)
```env
LOCAL_LLM_BASE_URL="http://localhost:11434/v1"
LOCAL_LLM_API_KEY="ollama"
LOCAL_LLM_MODEL="llama3"
```

#### OpenRouter (Cloud)
```env
LOCAL_LLM_BASE_URL="https://openrouter.ai/api/v1"
LOCAL_LLM_API_KEY="sk-or-v1-..."
LOCAL_LLM_MODEL="anthropic/claude-3.5-sonnet"
```

#### Groq (Cloud)
```env
LOCAL_LLM_BASE_URL="https://api.groq.com/openai/v1"
LOCAL_LLM_API_KEY="gsk_..."
LOCAL_LLM_MODEL="llama3-70b-8192"
```

## Note on Model Compatibility

LoomFlow relies on the LLM's ability to properly adhere to **Tool Calling / Function Calling** schemas.
If you are using a custom endpoint or local model, ensure that the model you select supports function calling. Models like Claude 3.5 Sonnet, GPT-4o, and Llama 3 generally perform very well with the Synthesizer. Smaller local models may struggle to produce the correct graph schema.
