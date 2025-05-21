from openai import OpenAI

client = OpenAI(api_key="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", 
                base_url="https://openrouter.ai/api/v1")

chat = client.chat.completions.create(
    model = "deepseek/deepseek-r1:free",
    messages = [
        {
            "role": "user",
            "content": "Hello, whats your name?"
        }
    ])

print(chat.choices[0].message.content)