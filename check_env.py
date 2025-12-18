import google.generativeai as genai
import os
from dotenv import load_dotenv

# Explicitly tell it where the .env file is to avoid the error
load_dotenv(".env")

print("✅ Libraries installed successfully!")
api_key = os.getenv('GOOGLE_API_KEY')

if api_key:
    print(f"✅ API Key found: {api_key[:5]}...")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Google AI Model configured.")
    except Exception as e:
        print(f"⚠️ API Key Error: {e}")
else:
    print("❌ GOOGLE_API_KEY not found in environment.")