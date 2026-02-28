import os
os.environ["WANDB_MODE"] = "offline"

import weave
weave.init("my-projet")

from mistralai import Mistral

api_key = os.environ.get("MISTRAL_API_KEY")  
if not api_key or api_key == "MISTRAL_API_KEY":
    raise ValueError("api not loaded")

client = Mistral(api_key=api_key)

response = client.chat.complete(
    model="ministral-3b-2512",
    messages=[{"role": "user", "content": "you're the agent 6, orchestrate the system with the 5 others agents that are under your control "}]
)

print(response)
