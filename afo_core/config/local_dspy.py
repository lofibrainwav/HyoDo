import dspy


def configure_local_dspy() -> None:
    """
    AFO Kingdom Local DSPy/Ollama Configuration.
    Prioritizes local OLLAMA over remote OpenAI for 'Goodness/Serenity'.
    """
    from AFO.config.settings import settings

    ollama_model = settings.OLLAMA_MODEL
    ollama_base_url = settings.OLLAMA_BASE_URL

    print(f"[DSPy][LOCAL] Configuring Ollama: model={ollama_model}, url={ollama_base_url}")

    try:
        lm = dspy.OllamaLocal(model=ollama_model, base_url=ollama_base_url)
        dspy.settings.configure(lm=lm)
        return True
    except Exception as e:
        print(f"[DSPy][LOCAL][ERROR] Failed to configure Ollama: {e}")
        return False


if __name__ == "__main__":
    configure_local_dspy()
