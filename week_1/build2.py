import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

def run_chatbot():
    """
    A terminal chatbot that holds a coherent multi-turn conversation.

    Your implementation should:
    - Start with a system message that sets the assistant's behaviour.
    - Maintain a `messages` list with alternating user/assistant turns.
    - Append the assistant's reply to `messages` after each call.
    - Resend the full history on every API call.
    - Allow the user to type 'exit' or 'quit' to end the session.

    Stretch:
    - Add a '/reset' command that clears history so you can feel context loss live.
    - Add a '/tokens' command that prints response.usage after the last call.
    """
    
    messages = [
        {"role": "system", "content": "You are Clanker, a sharp engineering assistant from IIT Delhi. Keep answers short and direct."}
    ]

    last_usage = {"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0}

    print("Chat started. Type 'exit' to quit.\n")

    while True:
        # TODO: take user input
        user_input = input("[YOU]: ")
        
        if user_input.strip().lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
            
        if user_input.strip() == '/reset':
            messages = [{"role": "system", "content": "You are Clanker, a sharp engineering assistant from IIT Delhi. Keep answers short and direct."}]
            print(" Context cleared! Memory reset done.\n")
            continue
            
        if user_input.strip() == '/tokens':
            print(f"Last Call Usage -> Total: {last_usage['total_tokens']}, Prompt: {last_usage['prompt_tokens']}, Completion: {last_usage['completion_tokens']}\n")
            continue

        if last_usage['total_tokens'] > 1000: 
            print("\n[COMPACTION] Token limit crossed! Summarizing older conversation...")
            compaction_response = client.chat.completions.create(
                model="openrouter/free",
                messages=messages + [{"role": "user", "content": "Summarize our entire conversation so far in 2-3 sentences, preserving vital technical choices."}]
            )
            # CRITICAL FIX: Explicitly locking identity variables (Disha, IIT Delhi) into the system prompt framework
            # This prevents open-weight models from wiping state parameters during rolling window resets.
            summary_text = compaction_response.choices[0].message.content
            
            # Re-initializing the message state with tightly bound context injection
            messages = [
                {"role": "system", "content": "You are Clanker, a sharp engineering assistant at IIT Delhi. "},
                {"role": "system", "content": f"Summary of earlier conversation (CRITICAL CONTEXT): {summary_text}"}
            ]
            
            print(" Compaction done!\n")

        # TODO: append the user turn to messages
        messages.append({"role": "user", "content": user_input})

        try:
            # TODO: call the API with the full messages list
            response = client.chat.completions.create(
                model="openrouter/free",
                messages=messages,
            )

            # TODO: extract the assistant's reply
            reply = response.choices[0].message.content

            last_usage['total_tokens'] = response.usage.total_tokens
            last_usage['prompt_tokens'] = response.usage.prompt_tokens
            last_usage['completion_tokens'] = response.usage.completion_tokens

            # TODO: append the assistant turn to messages
            messages.append({"role": "assistant", "content": reply})

            # TODO: print the reply
            print(f"[MODEL]: {reply}\n")
            
        except Exception as e:
            print(f"Error occurred: {e}\n")

if __name__ == "__main__":
    run_chatbot()