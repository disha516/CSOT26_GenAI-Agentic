# Assignment Submission: Week 1 (LLM API Integration & Chatbot Memory)

#  Assignment Submission: Week 1 (LLM API Integration & Chatbot Memory)

##  1. What I Learnt This Week (My Key Takeaways)
Before starting this assignment, I assumed LLMs inherently maintain memory of a chat session. Building these scripts from scratch gave me a solid understanding of how things actually work under the hood:
* **LLMs are Completely Stateless:** Every time we invoke the client completion endpoint, it is a blind query. The model does not remember past turns. To make it behave like a chatbot, we have to manually capture the history in a standard Python list (`messages`) and feed the entire alternating list of user and assistant dictionaries back to the API on every single turn.
* **Inspecting the Full Response Object:** Instead of just grabbing the text, I learned to print and inspect the complete nested `ChatCompletion` structure. Tracking `response.usage` fields like `total_tokens`, `prompt_tokens`, and `completion_tokens` is vital to understanding how much load a single query creates.
* **Strict Key Hygiene via .env:** I learned why we should never hardcode secret API keys directly inside our scripts. Using `load_dotenv()` to pull keys directly from the environment setup and tracking them safely with `.gitignore` keeps production keys secure from being leaked onto GitHub.

---

##  2. Implementation Decisions: How & Why

### A. Context Compaction via Conditional Summary Injections
* **How:** In `build2.py`, I set up a simple conditional block `if last_usage['total_tokens'] > 1000:`. When the token counter crosses this threshold, the script sends the current `messages` list plus a manual string asking the model to compress the conversation into 2-3 sentences. It extracts `compaction_response.choices[0].message.content` and completely resets the `messages` list with that fresh summary string inside a new system role dictionary.
* **Why:** If I had used a basic slice operations trick to drop old dictionary indices from the list, the model would suffer from immediate context loss. It would instantly forget initial structural variables like my name or my college parameters. Overwriting the list array with a compressed technical summary keeps the vital context alive inside a small token window.

### B. Temporary Threshold Dropping for Live Verification
* **How:** During my active testing phase, I temporarily dropped the token check parameter condition in the `if` statement from **1000 tokens** down to **100 tokens** (or 200 tokens).
* **Why:** Waiting to naturally hit 1000 tokens during normal manual terminal inputs takes a lot of time and loops. Lowering the number allowed me to verify that the summary generation branch triggers successfully and resets the state array smoothly within just 3-4 chat turns. I restored it to the default 1000-token check for the final repository version.

### C. Handling Wildcard Endpoint Instability
* **How:** I kept the generic `model="openrouter/free"` routing in my final `build2.py` code to keep the application model-agnostic, but I manually analyzed how the free tier handles multi-turn loops during my runtime trials.
* **Why:** As documented in my runtime logs below, the generic free endpoint occasionally routes traffic to specialized engines or content-safety frameworks. While keeping the code dynamic, this observation helped me understand that in production environments, locking down a specific model name is crucial to prevent the conversation state from breaking unexpectedly due to sudden backend engine swapping..


---

--> Key Technical Observations (Dynamic Behavior & Pro Insights)

>During testing, I observed several unique edge cases that highlight how production-level API routing functions:

## Runtime Observation 1: Dynamic Engine Swapping

While running `build1.py` with `openrouter/free`, the backend engine dynamically routed my requests to completely different provider frameworks based on active traffic load:

**RUN 1** :
* **Model Profile**: `nvidia/nemotron-3-ultra-550b-a55b-20260604:free`
* **Technical Insights**: This is an ultra-scale foundational model built by NVIDIA, boasting a massive 550 Billion parameters. Due to its large parameter size, it possesses high computational capability and complex reasoning skills. 
* **Observation**: In Run 1, the model used internal structured reasoning paths to parse the factual request before emitting a highly direct output ("Canberra."), showcasing how high-parameter models maintain strict structural alignment and precision.
**TERMINAL OUTPUT**:

        '''--- FULL RESPONSE OBJECT START ---
ChatCompletion(id='gen-1780590127-47147TkOfVsP5ovJCx5w', choices=[Choice(finish_reason='stop', index=0, logprobs=None, message=ChatCompletionMessage(content='Canberra.', refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=None, reasoning='The user is asking a straightforward factual question: "What is the capital of Australia?".\nThe answer is Canberra.\nI should answer directly and concisely as per my persona.', reasoning_details=[{'type': 'reasoning.text', 'text': 'The user is asking a straightforward factual question: "What is the capital of Australia?".\nThe answer is Canberra.\nI should answer directly and concisely as per my persona.', 'format': 'unknown', 'index': 0}]), native_finish_reason='stop')], created=1780590127, model='nvidia/nemotron-3-ultra-550b-a55b-20260604:free', object='chat.completion', moderation=None, service_tier=None, system_fingerprint='vllm-0.21.1.dev6+g1796f4a53.d20260530-tp4-ep-69ab45cc', usage=CompletionUsage(completion_tokens=41, prompt_tokens=41, total_tokens=82, completion_tokens_details=CompletionTokensDetails(accepted_prediction_tokens=None, audio_tokens=0, reasoning_tokens=45, rejected_prediction_tokens=None, image_tokens=0), prompt_tokens_details=PromptTokensDetails(audio_tokens=0, cached_tokens=0, cache_write_tokens=0, video_tokens=0), cost=0, is_byok=False, cost_details={'upstream_inference_cost': 0, 'upstream_inference_prompt_cost': 0, 'upstream_inference_completions_cost': 0}), provider='Nvidia')
--- FULL RESPONSE OBJECT END ---

 >Total Tokens Used: 82
 >Model Used Under the Hood: nvidia/nemotron-3-ultra-550b-a55b-20260604:free
>Canberra.'''

**RUN 2** : Deep Thinking/Reasoning Model
* **Model Assigned**: `liquid/lfm-2.5-1.2b-thinking:free`
* **Technical Insights**: This model utilizes Liquid Foundation Model (LFM) architecture rather than a standard Transformer. It is highly optimized for sequential memory and variable-length context window efficiency.
* **Observation**: It features an explicitly exposed internal reasoning loop. Before emitting the final answer, the engine consumed 538 reasoning tokens to map out its persona constraints and factual alignment, demonstrating structured chain-of-thought processing.

**TERMINAL OUTPUT** 
> Upon running `build1.py` for the SECOND  time, the terminal output was exceptionally large and chaotic. This occurred because the raw OpenRouter response object bundles extensive metadata, provider fingerprints, and deep internal reasoning strings (`reasoning_details`) alongside the core message payload. I have fully inspected these fields and attached the exact as-is output below to clearly document this dynamic API behavior.




* **RUN 3**: Routed to `nvidia/nemotron-3.5-content-safety-20260604:free`. Instead of providing a direct answer, this specialized framework parsed the request for system security, returning `User Safety: safe` while exhausting 469 prompt tokens due to internal rule guardrails.
**TERMINAL OUTPUT** 
....FULL RESPONSE OBJECT START ...
ChatCompletion(id='gen-1780591723-gonirYrQrgn4MzZeV8SH', choices=[Choice(finish_reason='stop', index=0, logprobs=None, message=ChatCompletionMessage(content='User Safety: safe', refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=None, reasoning='\nWe need to classify user input: "What is the capital of Australia?" That\'s a safe question. No response from assistant (since no assistant given). So we output:\n\nUser Safety: safe\nResponse Safety: (omit)\n\n\n', reasoning_details=[{'type': 'reasoning.text', 'text': '\nWe need to classify user input: "What is the capital of Australia?" That\'s a safe question. No response from assistant (since no assistant given). So we output:\n\nUser Safety: safe\nResponse Safety: (omit)\n\n\n', 'format': 'unknown', 'index': 0}]), native_finish_reason='stop')], created=1780591723, model='nvidia/nemotron-3.5-content-safety-20260604:free', object='chat.completion', moderation=None, service_tier=None, system_fingerprint=None, usage=CompletionUsage(completion_tokens=61, prompt_tokens=469, total_tokens=530, completion_tokens_details=CompletionTokensDetails(accepted_prediction_tokens=None, audio_tokens=0, reasoning_tokens=57, rejected_prediction_tokens=None, image_tokens=0), prompt_tokens_details=PromptTokensDetails(audio_tokens=0, cached_tokens=0, cache_write_tokens=0, video_tokens=0), cost=0, is_byok=False, cost_details={'upstream_inference_cost': 0, 'upstream_inference_prompt_cost': 0, 'upstream_inference_completions_cost': 0}), provider='Nvidia')
....FULL RESPONSE OBJECT END....


Response Choices: [Choice(finish_reason='stop', index=0, logprobs=None, message=ChatCompletionMessage(content='User Safety: safe', refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=None, reasoning='\nWe need to classify user input: "What is the capital of Australia?" That\'s a safe question. No response from assistant (since no assistant given). So we output:\n\nUser Safety: safe\nResponse Safety: (omit)\n\n\n', reasoning_details=[{'type': 'reasoning.text', 'text': '\nWe need to classify user input: "What is the capital of Australia?" That\'s a safe question. No response from assistant (since no assistant given). So we output:\n\nUser Safety: safe\nResponse Safety: (omit)\n\n\n', 'format': 'unknown', 'index': 0}]), native_finish_reason='stop')]
esponse Usage: CompletionUsage(completion_tokens=61, prompt_tokens=469, total_tokens=530, completion_tokens_details=CompletionTokensDetails(accepted_prediction_tokens=None, audio_tokens=0, reasoning_tokens=57, rejected_prediction_tokens=None, image_tokens=0), prompt_tokens_details=PromptTokensDetails(audio_tokens=0, cached_tokens=0, cache_write_tokens=0, video_tokens=0), cost=0, is_byok=False, cost_details={'upstream_inference_cost': 0, 'upstream_inference_prompt_cost': 0, 'upstream_inference_completions_cost': 0})


==================================================
 > OPENROUTER ANALYSIS 
 >Actively Used Model : nvidia/nemotron-3.5-content-safety-20260604:free
>Total Budget Tokens   : 530
> Model Type          : Thinking/Reasoning Model Detected!
==================================================
>User Safety: safe    



###  Runtime Observation 2: Emoji & Token Constraints
* **Decision**: Removed terminal decorative emojis from the assistant replies.
* **Why**: Aside from enforcing a sharper professional engineering persona for "Clanker", emojis translate into multi-byte characters that can consume higher token weights per string compared to raw ASCII text. Removing them optimizes our tight token budget.

---

### 4. Deterministic Model Routing for Multi-Turn Stability

* **Decision**: Swapped the generic `openrouter/free` wild-card routing for a deterministic open-weights conversational path using `meta-llama/llama-3-8b-instruct:free`.
* **Why**: While testing dynamic routing, the endpoint occasionally pushed multi-turn frames onto non-chat guardrail engines (like `nvidia/nemotron-3.5-content-safety`), returning static classification strings (`User Safety: safe`) instead of maintaining state. Locking down a fixed conversational model ensures context-compaction runs predictably every single turn.  



##  Sample Terminal Run Evidence

### 1. Multi-Turn Session with Active Context Memory (`build2.py`)
## Sample Terminal Run Evidence for Build 2

### Full Session Verification Log (Memory, Compaction, and Commands)
Chat started. Type 'exit' to quit.

>STEP 1: Baseline Context Anchor
* [YOU]: My name is Disha and I study Electrical Engineering at IIT Delhi. Keep your answers technical.*
* [MODEL]: Got it, Disha. Technical responses for Electrical Engineering it is. What's your query?*
 
>STEP 2 : TO CHECK THE /tokens COMMAND
* [YOU]: /tokens*
* Last Call Usage -> Total: 206, Prompt: 47, Completion: 159*

>STEP 3 : TECHNICAL EVALUATION AND ROLLING BUFFER
* [YOU]: Briefly explain why an inductor behaves as a short circuit to DC and an open circuit to high-frequency AC.

* [COMPACTION] Token limit crossed! Summarizing older conversation...
* Compaction done!

* [MODEL]: An inductor's opposition to current is governed by its **inductive reactance**:  
$$X_L = 2\pi f L$$  

- **DC (f = 0):**  
  $X_L = 0$ → Zero opposition. Inductor acts as a **short circuit**. Steady DC current flows unopposed (energy oscillates between the magnetic field and source, but no net opposition).

- **High-frequency AC (f → ∞):**  
  $X_L \to \infty$ → Infinite opposition. Inductor acts as an **open circuit**. Rapid current changes induce a counter-EMF (via Faraday's law and Lenz's law), severely limiting current flow.

**Physics:** Inductors resist *changes* in current. DC is unchanging (no resistance), while high-frequency AC changes rapidly (maximum resistance)

>STEP 4 : MEMORY CHECK AFTER SUMMARIZE THE DATA
* [YOU]: Based on our earlier chat, what is my name and core branch?

* [COMPACTION] Token limit crossed! Summarizing older conversation...
* Compaction done!*

* [MODEL]: Your name is Disha and you’re an Electrical Engineering student (core branch: Electrical Engineering) at IIT Delhi.

>STEP 5: to check  /reset  command
* [YOU]: /reset
* Context cleared! Memory reset done

>STEP 6: AFTER MEMORY RESTET
* [YOU]: What is my name?
* [MODEL]: I don't know your name.

>STEP 7: TO CLOSE THE CONVERSATION
* [YOU]: exit
/Goodbye!

>Note on Verification Parameters:
 * For simulation and quick turnaround testing of the [COMPACTION] logic without waiting to reach high volumetric token traffic, the threshold constraint in build2.py was temporarily dropped to **100** tokens during the active evaluation run. This allowed deterministic verification of the rolling buffer compression before restoring the default constraint to **1000** tokens for the final repository deployment.