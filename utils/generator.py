import requests
from config import (
    GENERATIVE_ENGINE_API_KEY,
    GENERATIVE_ENGINE_OPENAI_URL,
    DEPLOYMENT_MODEL
)
from utils.prompt import SYSTEM_PROMPT, build_prompt

GENERATIVE_ENGINE_CHAT_URL = f"{GENERATIVE_ENGINE_OPENAI_URL}/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {GENERATIVE_ENGINE_API_KEY}",
    "Content-Type": "application/json"
}


def _call_model(prompt, system_prompt, temperature=0.9, max_tokens=4000, timeout=60):
    payload = {
        "model": DEPLOYMENT_MODEL,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    response = requests.post(
        GENERATIVE_ENGINE_CHAT_URL,
        headers=HEADERS,
        json=payload,
        timeout=timeout
    )
    response.raise_for_status()
    data = response.json()

    return data["choices"][0]["message"]["content"].strip(), data["choices"][0].get("finish_reason")


def generate_pseudocode(test_case):
    try:
        prompt = build_prompt(test_case)
        content, finish_reason = _call_model(prompt, SYSTEM_PROMPT, temperature=0.0, max_tokens=4000, timeout=60)

        if finish_reason == "length" and content:
            continuation_prompt = (
                "The previous response was truncated. Continue the remaining code only. "
                "Do not repeat the already generated content. Return only the missing portion.\n\n"
                f"{content}"
            )
            continuation, _ = _call_model(continuation_prompt, SYSTEM_PROMPT, temperature=0.0, max_tokens=4000, timeout=60)
            if continuation:
                return f"{content}\n{continuation}".strip()

        return content

    except Exception as e:
        print(f"Error generating pseudocode: {e}")
        return f"Generation Failed: {e}"


def generate_complete_automation(test_case, framework="selenium", language="python"):
    """
    One-stop function: Manual Test Case → Pseudocode → Automation Script
    
    Args:
        test_case (dict): Manual test case details
        framework (str): Testing framework
        language (str): Programming language
    
    Returns:
        dict: Contains both pseudocode and automation script
    """
    try:
        # Step 1: Generate pseudocode
        print("Generating pseudocode...")
        pseudocode = generate_pseudocode(test_case)
        
        if not pseudocode:
            return {
                "success": False,
                "error": "Failed to generate pseudocode"
            }
        
        return {
            "success": True,
            "pseudocode": pseudocode,
            "framework": framework,
            "language": language
        }
    
    except Exception as e:
        print(f"Error in complete automation generation: {e}")
        return {
            "success": False,
            "error": str(e)
        }