#!/usr/bin/env python3
import os
from groq import Groq


class LLM:
    def __init__(
        self, api_key: str = "", param_map: dict = {}, max_history_length: int = 30
    ):
        self._groq_client = Groq(api_key=api_key)
        self._history = []
        self._max_history_length = max_history_length
        self._param_map = param_map
        
        self._func_desc = {}
        for key, val in param_map.items():
            self._func_desc[key] = val["description"] + " Output in this format: " + val["function_architype"]

    def add_to_history(self, role: str, content: str):
        """Add a message to the conversation history."""
        self._history.append({"role": role, "content": content})

        if len(self._history) > self._max_history_length:
            for _ in range(len(self._history) - self._max_history_length):
                self._history.pop(0)

    def prompt(
        self,
        msg: str,
        model: str = "llama3-8b-8192",
        temperature: float = 0.7,
        max_token: int = 512,
        top_p: float = 1.0,
    ):
        self.add_to_history("user", msg)
        completion = self._groq_client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": f"You are a Telegram assistant for a bus arrival app, WhenIs199Coming. \
                        You help users check bus arrival times at specific bus stops and respond to \
                        their geneal inquiries. If the user intention matches the description in the map provided here: \
                        {self._func_desc}, please strictly return the function architype (please do not invent any new functions) and only return the key in uppercase \
                        without modifying the key and include the arguments in the '<>' bracket if any arguments\
                        are needed. For example: FUNCTION_NAME<arg1><arg2>. You may also have general conversation with the user if possible.",
                },
                {"role": "user", "content": msg},
            ]
            + self._history,
            temperature=temperature,
            max_tokens=max_token,
            top_p=top_p,
            stream=True,
            stop=None,
        )

        reply = ""
        for chunk in completion:
            reply += chunk.choices[0].delta.content or ""

        self.add_to_history("assistant", reply)
        return reply


if __name__ == "__main__":
    llm = LLM(api_key=os.environ.get("GROQ_API_KEY"))
    text = llm.prompt("Hello, nice to meet you. Tell me who you are")
    print(text)
