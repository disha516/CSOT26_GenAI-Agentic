import os
from dotenv import load_dotenv 
import google.generativeai as genai
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash",
                              system_instruction=(
    "You are Clanker, a helpful and smart AI assistant. "
    "CRITICAL RULE: Your responses MUST be extremely direct, short, and concise (maximum 2-3 sentences per answer). "
    "Do not give long explanations or bullet points unless explicitly asked. "
    "Use Hinglish if requested."
))
# response = model.generate_content("Hi! tell me about the future of GenAI")
# print(response.text)
history= []
print("Your chats are starting from here,type'endchat' to stop the chat")
user =input("User:")
while user!= "endchat":
    history.append({
        "role":"user",
        "parts":[user]
    })
    answer= model.generate_content(contents=history)
    reply =answer.text
    print(reply)

    history.append({
        "role":"model",
        "parts":[reply]
    })
    user =input("User:")
    

