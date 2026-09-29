from smolagents import CodeAgent, LiteLLMModel
from tools import BuildWord, BuildPDF
from prompt import PROMPT_SYSTEM
import os


API_KEY_ENV_BY_PROVIDER = {
    "mistral": "MISTRAL_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "zai": "ZAI_API_KEY",
}

OPENROUTER_MODEL_PREFIXES = (
    "anthropic/",
    "deepseek/",
    "google/",
    "meta-llama/",
    "mistralai/",
    "nex-agi/",
    "nvidia/",
    "openai/",
    "qwen/",
    "x-ai/",
)


def normalize_model_id(model_id):
    model_id = (model_id or "").strip()

    if model_id.startswith("o*/"):
        model_id = f"openrouter/{model_id.removeprefix('o*/')}"

    if model_id.startswith("openrouter/"):
        return model_id

    if model_id.startswith(OPENROUTER_MODEL_PREFIXES):
        return f"openrouter/{model_id}"

    return model_id


def get_api_key_for_model(model_id):
    provider = model_id.split("/", 1)[0].lower()
    env_name = API_KEY_ENV_BY_PROVIDER.get(provider)
    if not env_name:
        return None

    api_key = os.getenv(env_name, "").strip()
    if not api_key:
        raise RuntimeError(f"{env_name} est manquant pour le modele {model_id}")

    return api_key


def create_agent(model_id):
    normalized_model_id = normalize_model_id(model_id)
    model_kwargs = {"model_id": normalized_model_id}
    api_key = get_api_key_for_model(normalized_model_id)
    if api_key:
        model_kwargs["api_key"] = api_key

    model = LiteLLMModel(**model_kwargs)
    agent = CodeAgent(
        model=model,
        tools=[
            BuildWord(),
            BuildPDF(),
        ],
        instructions=PROMPT_SYSTEM,
        max_steps=7,
        planning_interval=2
    )

    return agent
