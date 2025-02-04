import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the API key for Google Generative AI from environment variable
api_key = os.getenv("GENAI_API_KEY")
genai.configure(api_key=api_key)

def generate_response(user_query):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(user_query)
    return response.text