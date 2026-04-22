from crewai import LLM

from ..utils.constants import API_KEY, BASE_URL, LLM_PROVIDER, MODEL


def get_llm(temperature: float = 0.2) -> LLM:
    return LLM(
        model=MODEL,
        provider=LLM_PROVIDER,
        base_url=BASE_URL,
        api_key=API_KEY,
        temperature=temperature,
    )
