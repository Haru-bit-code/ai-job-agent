# ──────────────────────────────────────────────────────────────
# PURPOSE: Single place to create and configure the Groq client
# Every other file imports from here — not directly from groq
#
# WHY: If Groq changes their API or you switch providers,
#      you only change ONE file, not every file in the project
#      This is called the "single responsibility principle"
# ──────────────────────────────────────────────────────────────

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()  # reads your .env file


def get_groq_client() -> Groq:
    """
    Creates and returns a configured Groq client.
    Fails clearly if API key is missing.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found in .env file.\n"
            "Get your free key at: console.groq.com"
        )

    return Groq(api_key=api_key)


def ask_groq(system_prompt: str, user_prompt: str, model: str = "llama-3.3-70b-versatile") -> str:
    """
    Sends a prompt to Groq and returns the response text.
    
    Two prompts explained:
    
    system_prompt → sets the personality and rules for the LLM
                    "You are a strict job relevance scorer..."
                    Think: job description for the AI
                    
    user_prompt   → the actual question or task
                    "Score this job for this candidate..."
                    Think: the actual work request
                    
    model         → llama-3.3-70b-versatile
                    - Free on Groq
                    - 70 billion parameters
                    - Excellent at reasoning and scoring tasks
    """

    client = get_groq_client()

    # messages is a list of turns in the conversation
    # role "system"    → instructions to the LLM
    # role "user"      → input from the user
    # role "assistant" → previous LLM responses (for multi-turn)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        temperature=0.2,
        # temperature controls randomness:
        # 0.0 = fully deterministic, same answer every time
        # 1.0 = creative and varied
        # 0.2 = mostly consistent, slight variation
        # For scoring tasks: low temperature = reliable scores
    )

    # Extract just the text from the response object
    return response.choices[0].message.content


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Groq connection...\n")

    response = ask_groq(
        system_prompt="You are a helpful assistant. Reply concisely.",
        user_prompt="Say hello and confirm you are working correctly. One sentence only."
    )

    print(f"Groq response: {response}")
    print("\n✅ Groq connection successful!")