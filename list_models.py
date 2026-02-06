import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Kein API Key gefunden.")
    exit(1)

client = genai.Client(api_key=api_key)

print("Verfügbare Modelle:")
try:
    for m in client.models.list():
        print(f"- {m.name}")
except Exception as e:
    print(f"Fehler beim Listen der Modelle: {e}")
