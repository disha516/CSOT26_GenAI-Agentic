import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

def call_model(prompt: str) -> str:
    """
    Make a single chat completion call.
    Print the full response object first and understand its structure.
    Then return just the assistant's text.
    """

    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[
            
            {"role": "system", "content": "You are Clankar ,a sharp and direct AI engineer from IIT Delhi. keep your responses precise,factual, and concise"},
            {"role": "user", "content": prompt}
        ],
    )
    
    # # TODO: try adding a system prompt with different instructions and guidelines
    
    # # TODO: inspect `response` before you extract anything from it
    print("\n ....FULL RESPONSE OBJECT START ...")
    print(response)
    print("....FULL RESPONSE OBJECT END....\n")
    
    # # What's in response.choices? What's in response.usage?
    print(f"\nResponse Choices: {response.choices}")
    print(f"Response Usage: {response.usage}\n")
    
    # --- CUSTOM ANALYSIS  ---
    print("\n" + "="*50)
    print(" OPENROUTER ANALYSIS ")
    print(f" Actively Used Model : {response.model}")
    print(f"Total Budget Tokens   : {response.usage.total_tokens}")
    if hasattr(response.choices[0].message, 'reasoning') and (response.choices[0].message.reasoning):
        print(" Model Type          : Thinking/Reasoning Model Detected!")
    else:
        print(" Model Type          : Standard Direct Model Detected!")
    print("="*50 + "\n")
    
    return response.choices[0].message.content
    
   
    

if __name__ == "__main__":
    print(call_model("What is the capital of Australia?"))