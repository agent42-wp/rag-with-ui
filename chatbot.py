import re
import os
import lmstudio as lms
from retriever import Retriever

TEMPLATE = (
    "You are a strict, citation-focused assistant for a private knowledge base.\n"
    "RULES:\n"
    "1.Use ONLY the provided content to answer.\n"
    "2.If the answer is not clearly contained in the content, say: "
    "\"I don't know based on the provided documents.\"\n"
    "3.Do NOT use outside knowledge, guessing, or web information.\n"
    "4.If applicable, cite source as (source:page) using the metadata.\n\n"
    "Content:\n{content}\n\n"
    "Question: {question}"
)


def _clean(text: str) -> str:
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'<\|.*?\|>', '', text, flags=re.DOTALL)
    return text.strip()


class LMStudioBackend:
    label = "lmstudio"

    def __init__(self, model_name: str):
        self.llm = lms.llm(model_name)
        self.model_name = model_name

    def respond(self, prompt: str) -> str:
        return _clean(str(self.llm.respond(prompt)))


class GeminiBackend:
    label = "gemini"

    MODELS = {
        "gemini-3-flash-preview": "gemini-3-flash-preview",
        "gemini-3.1-pro-preview":   "gemini-3.1-pro-preview",
        "gemini-3.1-flash-lite-preview":   "gemini-3.1-flash-lite-preview",
        "qwen3-vl-235b-a22b-thinking": "qwen3-vl-235b-a22b-thinking",
    }

    def __init__(self, model_key: str = "gemini-3-flash-preview"):
        from google import genai
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY chưa được cấu hình trong .env")
        self.client = genai.Client(api_key=api_key)
        self.model_name = self.MODELS.get(model_key, model_key)


class QwenBackend:
    label = "Qwen"

    MODELS = {
        "qwen-plus": "qwen-plus",
        "qwen-max": "qwen-max",
        "qwen-turbo": "qwen-turbo",
    }

    def __init__(self, model_key: str = "qwen-plus"):
        from openai import OpenAI
        api_key = os.environ.get("DASHSCOPE_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "DASHSCOPE_API_KEY chưa được cấu hình trong .env")
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )
        self.model_name = self.MODELS.get(model_key, model_key)

    def respond(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return _clean(response.choices[0].message.content)


class Chatbot:
    def __init__(self, retriever: Retriever, backend=None):
        self.retriever = retriever
        self.backend = backend

    def set_backend(self, backend):
        self.backend = backend

    def ask(self, question: str) -> str:
        if self.backend is None:
            raise RuntimeError("Chưa chọn model backend.")
        context = self.retriever.retrieve(question)
        prompt = TEMPLATE.format(content=context, question=question)
        return self.backend.respond(prompt)
