import os
from dotenv import load_dotenv

load_dotenv()

def get_openai_api_key():
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise Exception("Please set your OPENAI_API_KEY environment variable.")
    return key

def get_gemini_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise Exception("Please set your GEMINI_API_KEY environment variable.")
    return key

def get_xai_api_key():
    key = os.environ.get("XAI_API_KEY")
    if not key:
        raise Exception("Please set your XAI_API_KEY environment variable.")
    return key

def get_deepseek_api_key():
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise Exception("Please set your DEEPSEEK_API_KEY environment variable.")
    return key

def get_anthropic_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise Exception("Please set your ANTHROPIC_API_KEY environment variable.")
    return key

