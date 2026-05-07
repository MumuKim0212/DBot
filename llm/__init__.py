import os

def get_llm():
    provider = os.getenv("LLM_PROVIDER", "openai")

    if provider == "claude":
        from .claude_provider import ClaudeProvider
        return ClaudeProvider()

    elif provider == "openai":
        from .openai_provider import OpenAIProvider
        return OpenAIProvider() 

    else:
        raise ValueError(f"Unknown LLM provider: {provider}")