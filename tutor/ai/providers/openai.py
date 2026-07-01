from tutor.ai.base import AIProvider
from tutor.ai.openai_client import call_openai_chat


class OpenAIProvider(AIProvider):
    def generate(
        self,
        system_prompt: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        model_name: str,
    ) -> str:
        user_parts = [
            str(message.get("content", "")).strip()
            for message in messages
            if str(message.get("content", "")).strip()
        ]
        prompt = "\n\n".join(user_parts)
        result = call_openai_chat(
            prompt,
            system_prompt=system_prompt or None,
            model=model_name,
            json_mode=False,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return result["content"]
