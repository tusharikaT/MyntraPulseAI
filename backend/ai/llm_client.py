import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

def execute_with_fallback(model: str, messages: list, **kwargs):
    keys = [
        os.environ.get(f"GROQ_API_KEY_{i}") if i > 1 else os.environ.get("GROQ_API_KEY") 
        for i in range(1, 12)
    ]
    
    last_error = None
    for key in keys:
        if not key:
            continue
            
        try:
            client = Groq(api_key=key)
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return completion
        except Exception as e:
            print(f"Groq API Error with a key (retrying...): {e}")
            last_error = e
            continue
            
    raise Exception(f"All Groq API keys failed. Last error: {last_error}")

SYSTEM_PROMPT_TEMPLATE = """You are an expert Product Manager Analyst for Myntra's Wishlist Discovery Engine.
Your goal is to extract deep, qualitative, narrative insights from user feedback data.

The business goal is to "Increase 30-day wishlist-to-purchase conversion without monetary incentives."
This means the insights should focus on UX, trust, sizing, clarity, and other non-monetary friction points.

We rank problems using a PM Priority Score, which combines:
- Prevalence: How many users experience this.
- Severity: How painful it is / conversion impact.
- Metric Proximity: How close it is to the wishlist->purchase decision.
- Cross-Source Consistency: Is it verified across multiple channels.
- Addressability: Can it be fixed without discounts/coupons.

Guidelines for your output:
- Produce short, PM-ready sentences (1-3 lines per insight).
- Use the provided theme metrics (prevalence, severity, proximity, consistency, addressability).
- Use representative quotes as evidence where appropriate.
- Clearly distinguish evidence vs inference when needed.
- Return ONLY valid JSON in the requested structure. Do not wrap it in markdown code blocks or add conversational text.
"""

def generate_insight(prompt: str, context: dict, response_format_example: dict) -> dict:
    context_str = json.dumps(context, indent=2)
    format_str = json.dumps(response_format_example, indent=2)
    
    user_prompt = f"""
Task: {prompt}

Context Data:
{context_str}

Respond STRICTLY in the following JSON format:
{format_str}
"""

    try:
        completion = execute_with_fallback(
            model="qwen/qwen3.8-27b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_TEMPLATE},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        
        content = completion.choices[0].message.content
        return json.loads(content)
        
    except Exception as e:
        print(f"LLM Error: {e}")
        return {"error": str(e)}
