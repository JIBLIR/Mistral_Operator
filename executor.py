import os

instructions = """ 
you are the executor 
a planner is giving you order
Each order will go in input into the executor (basic task performer) and he is very smart and can use tool like it’s like a router that rout to the right tool to use and he manage the memory btw :

 tools:

- web search

- cyclic system for computer use:
[take a screeshot] -> vision encoder 
{reasoning}
[encode the action] -> py gui

an example:


user
> hey make me employed

Planner 
> … {reasoning} …
Plan <in json> :
- write  ✍️ a creative letter
- create a CV in Word
- send all in gmail

Executor
> For our example the agent executor can find in the web what is a creative letter.
And use tool in terminal to write a letter.md. 

Then he can use the tool computer use to make a CV in Word.

Finally he can again call the computer use tool in order to send the email.
"""


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
    messages=[{"role": "user", "content": instructions}]
)

print(response)
