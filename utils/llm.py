from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from utils.constants import API_KEY, BASE_URL, MODEL


def get_llm(temperature=0.2):
    return ChatOpenAI(
        model=MODEL,
        base_url=BASE_URL,
        api_key=SecretStr(API_KEY),
        temperature=temperature,
    )
