
import os
import time
import traceback

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load API key from .env
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from .env")

# Initialize Gemini client
client = genai.Client(
    api_key=API_KEY,
    http_options=types.HttpOptions(
        timeout=30000,
        retry_options=types.HttpRetryOptions(
            attempts=1
        )
    )
)

print("Starting independent Gemini test...", flush=True)

start_time = time.perf_counter()

try:
    response = client.interactions.create(
        model="gemini-3.5-flash-lite",
        input="List five technical skills for a software developer.",
        generation_config={
            "thinking_level": "low"
        },
        timeout=30
    )

    elapsed = time.perf_counter() - start_time

    print("\nGemini response:", flush=True)
    print(response.output_text, flush=True)
    print(f"\nGeneration time: {elapsed:.2f} seconds", flush=True)

except Exception as error:
    elapsed = time.perf_counter() - start_time

    print("\nGemini API error:", flush=True)
    print(type(error).__name__, flush=True)
    print(str(error), flush=True)
    print(f"Time before error: {elapsed:.2f} seconds", flush=True)

    traceback.print_exc()

finally:
    client.close()
