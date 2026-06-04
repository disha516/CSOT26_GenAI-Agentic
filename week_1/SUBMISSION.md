# Assignment Submission: Week 1 (LLM API Integration & Chatbot Memory)

# Key Design Decisions & Learnings

>1. Model-Agnostic Setup via OpenRouter

**DECISION** : Integrated the OpenRouter API using the standard OpenAI Python SDK client, pointing the `base_url` to OpenRouter's endpoint.
**WHY**: This fulfills the mentor instruction to keep the setup model-agnostic. By using `model="openrouter/free"`, the script dynamically routes requests to optimal free models without changing a single line of core orchestration code.


>2. Message Object Extraction Logic (`build1.py`)

**DECISION** : Extracted response text using `response.choices[0].message.content`.
**WHY** : The OpenAI structure returns a complex nested object containing metadata and alternate completion paths. Grabbing index `0` ensures we process the primary generated turn while dropping unnecessary engine payloads.


>3. State Management & Rolling Memory (`build2.py`)

**DECISION**: Maintained interaction history via a persistent Python `messages` list, injecting a clear initial role definition inside `{"role": "system"}` as the first element instead of initializing it within the generative model arguments.
**WHY* : Modern chat models don't naturally store history. Resending the growing alternating list of `user` and `assistant` messages on every turn forces coherent conversational memory.

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
[YOU]: My name is Disha and I study Electrical Engineering at IIT Delhi. Keep your answers technical.
[MODEL]: Got it, Disha. Technical responses for Electrical Engineering it is. What's your query?
 
>STEP 2 : TO CHECK THE /tokens COMMAND
[YOU]: /tokens
Last Call Usage -> Total: 206, Prompt: 47, Completion: 159

>STEP 3 : TECHNICAL EVALUATION AND ROLLING BUFFER
[YOU]: Briefly explain why an inductor behaves as a short circuit to DC and an open circuit to high-frequency AC.

[COMPACTION] Token limit crossed! Summarizing older conversation...
 Compaction done!

[MODEL]: 
An inductor's opposition to current is governed by its **inductive reactance**:  
$$X_L = 2\pi f L$$  

- **DC (f = 0):**  
  $X_L = 0$ → Zero opposition. Inductor acts as a **short circuit**. Steady DC current flows unopposed (energy oscillates between the magnetic field and source, but no net opposition).

- **High-frequency AC (f → ∞):**  
  $X_L \to \infty$ → Infinite opposition. Inductor acts as an **open circuit**. Rapid current changes induce a counter-EMF (via Faraday's law and Lenz's law), severely limiting current flow.

**Physics:** Inductors resist *changes* in current. DC is unchanging (no resistance), while high-frequency AC changes rapidly (maximum resistance).

>STEP 4 : MEMORY CHECK AFTER SUMMARIZE THE DATA
[YOU]: Based on our earlier chat, what is my name and core branch?

[COMPACTION] Token limit crossed! Summarizing older conversation...
 Compaction done!

[MODEL]: Your name is Disha and you’re an Electrical Engineering student (core branch: Electrical Engineering) at IIT Delhi.

>STEP 5: to check  /reset  command
[YOU]: /reset
🧹 Context cleared! Memory reset done

>STEP 6: AFTER MEMORY RESTET
[YOU]: What is my name?
[MODEL]: I don't know your name.

>STEP 7: TO CLOSE THE CONVERSATION
[YOU]: exit
Goodbye!

>Note on Verification Parameters: > For simulation and quick turnaround testing of the [COMPACTION] logic without waiting to reach high volumetric token traffic, the threshold constraint in build2.py was temporarily dropped to **100** tokens during the active evaluation run. This allowed deterministic verification of the rolling buffer compression before restoring the default constraint to **1000** tokens for the final repository deployment.