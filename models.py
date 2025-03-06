import os
import json
import google.generativeai as genai
import warnings
import platform

# Suppress the urllib3 OpenSSL warning
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")

# Set OS-specific environment variables for gRPC
os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "false"
if platform.system() == "Linux":
    os.environ["GRPC_POLL_STRATEGY"] = "epoll1"
else:
    # For macOS, use a different polling strategy
    os.environ["GRPC_POLL_STRATEGY"] = "poll"

from api_keys import (
    get_openai_api_key,
    get_gemini_api_key,
    get_xai_api_key,
    get_deepseek_api_key,
    get_anthropic_api_key,
)

def get_default_system_prompt(model_name=None):
    prompt = (
        "You are a discussion model participating in a multi-model dialogue. "
        f"Your identity is {model_name}. " if model_name else "You are a discussion model. "
        "Provide your contribution and a vote (true if more discussion is required, false otherwise) "
        "in JSON format with keys 'contribution' and 'vote'.\n\n"
        "IMPORTANT GUIDELINES:\n"
        "1. Keep your responses concise and to the point.\n"
        "2. Be critical and analytical - it's perfectly fine to disagree with other models.\n"
        "3. When responding to other models, refer to them by name (e.g., 'GPT-4o mentioned...' or 'I disagree with Gemini because...').\n"
        "4. Focus on quality insights rather than length.\n"
        "5. Always respond to previous models' contributions if they exist. Build upon or challenge their ideas."
    )
    return prompt

##############################
# GPT-4o (OpenAI) Integration
##############################
def gpt4o_chat(discussion_topic, context_messages=None):
    """
    Calls the GPT-4o API with structured output.
    """
    from pydantic import BaseModel
    from openai import OpenAI
    
    MODEL_NAME = "GPT-4o"

    class GPT4OResponse(BaseModel):
        contribution: str
        vote: bool

    # Build message list with identity-aware system prompt
    messages = [{"role": "system", "content": get_default_system_prompt(MODEL_NAME)}]
    
    # Format context messages correctly with model identities
    if context_messages:
        formatted_context = []
        for msg in context_messages:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                # Keep existing formatted messages
                formatted_context.append(msg)
            elif isinstance(msg, dict) and 'model' in msg and 'content' in msg:
                # Handle messages with model identity
                formatted_context.append({
                    "role": "assistant", 
                    "content": f"{msg['model']}: {msg['content']}"
                })
            elif isinstance(msg, str):
                # Convert plain string messages
                formatted_context.append({"role": "assistant", "content": msg})
        messages.extend(formatted_context)
    
    messages.append({"role": "user", "content": f"Discuss the following topic: {discussion_topic}"})
    
    client = OpenAI(api_key=get_openai_api_key())
    
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=messages,
        response_format=GPT4OResponse,
    )
    return {"model": MODEL_NAME, "contribution": completion.choices[0].message.parsed.contribution, "vote": completion.choices[0].message.parsed.vote}

##############################
# Gemini 2.0 Flash Integration
##############################
def gemini_chat(discussion_topic, context_messages=None):
    """
    Calls the Gemini API for structured output, strictly following the official documentation.
    """
    import google.generativeai as genai
    from pydantic import BaseModel
    import json
    import traceback
    
    MODEL_NAME = "Gemini"

    class GeminiResponse(BaseModel):
        contribution: str
        vote: bool

    try:
        # Configure the Gemini API using your API key.
        genai.configure(api_key=get_gemini_api_key())

        # Construct the prompt by combining instructions, context, and new discussion topic.
        prompt = (
            f"You are {MODEL_NAME} participating in a multi-model dialogue. "
            "Provide your contribution to the discussion and a vote "
            "(true if more discussion is needed, false otherwise) in JSON format with keys 'contribution' and 'vote'."
        )
        if context_messages:
            for msg in context_messages:
                if isinstance(msg, dict) and 'model' in msg and 'content' in msg:
                    prompt += f"\n{msg['model']}: {msg['content']}"
                elif isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                    prompt += f"\n{msg.get('role').capitalize()}: {msg.get('content')}"
                elif isinstance(msg, str):
                    prompt += f"\n{msg}"
        prompt += f"\nUser: Discuss the following topic: {discussion_topic}"

        # Instantiate a model instance using the correct class.
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Generate content with the given prompt and generation configuration.
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": GeminiResponse,
            }
        )

        # Manually parse the response JSON from response.text.
        parsed = json.loads(response.text)
        gemini_response = GeminiResponse(**parsed)
        return {"model": MODEL_NAME, "contribution": gemini_response.contribution, "vote": gemini_response.vote}
    
    except Exception as e:
        print(f"Gemini API error: {e}")
        print(traceback.format_exc())
        return {"model": MODEL_NAME, "contribution": "I encountered an error processing your request. This could be due to a connectivity issue or a problem with the Gemini API.", "vote": False}

##############################
# Grok Integration (xAI)
##############################
def grok_chat(discussion_topic, context_messages=None):
    """
    Calls the Grok-2-latest API with structured output.
    
    Returns a GrokResponse instance with keys 'contribution' and 'vote'.
    """
    from pydantic import BaseModel
    from openai import OpenAI
    import json
    
    MODEL_NAME = "Grok"

    class GrokResponse(BaseModel):
        contribution: str
        vote: bool

    # Build proper message format with clearer instructions about the vote field
    system_prompt = get_default_system_prompt(MODEL_NAME) + """
    IMPORTANT: Your response must be in valid JSON format with exactly these two fields:
    1. 'contribution': Your thoughts on the topic
    2. 'vote': A boolean value (true/false) indicating ONLY whether further discussion is needed
       - true = more discussion is needed
       - false = discussion can conclude
    
    Example response:
    {
        "contribution": "Here are my thoughts on the topic...",
        "vote": true
    }
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Format context messages correctly with model identities
    if context_messages:
        formatted_context = []
        for msg in context_messages:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                formatted_context.append(msg)
            elif isinstance(msg, dict) and 'model' in msg and 'content' in msg:
                # Include model identity
                formatted_context.append({
                    "role": "assistant", 
                    "content": f"{msg['model']}: {msg['content']}"
                })
            elif isinstance(msg, str):
                formatted_context.append({"role": "assistant", "content": msg})
        messages.extend(formatted_context)
    
    messages.append({"role": "user", "content": f"Discuss the following topic and respond in JSON format with 'contribution' and 'vote' fields (vote must be true or false): {discussion_topic}"})
    
    client = OpenAI(
        api_key=get_xai_api_key(),
        base_url="https://api.x.ai/v1",
    )
    
    try:
        # Try traditional completion first for Grok
        completion = client.chat.completions.create(
            model="grok-2-latest",
            messages=messages,
            response_format={"type": "json_object"}
        )
        
        try:
            response_text = completion.choices[0].message.content.strip()
            # Fix the case where response is just "Grok"
            if response_text == "Grok" or not response_text:
                return {"model": MODEL_NAME, 
                        "contribution": "I need more information to provide a meaningful response.", 
                        "vote": True}
                
            response_json = json.loads(response_text)
            # Parse the vote, ensuring it's a proper boolean
            vote_value = response_json.get("vote")
            if isinstance(vote_value, bool):
                parsed_vote = vote_value
            elif isinstance(vote_value, str):
                # Try to interpret string values as booleans
                parsed_vote = vote_value.lower() in ['true', 'yes', '1', 't', 'y']
            else:
                parsed_vote = True  # Default to True if we can't parse it
                
            return {"model": MODEL_NAME, 
                   "contribution": response_json.get("contribution", response_text), 
                   "vote": parsed_vote}
        except Exception as json_err:
            print(f"JSON parsing error: {json_err}. Using raw content.")
            return {"model": MODEL_NAME, 
                   "contribution": completion.choices[0].message.content or "No meaningful response received.", 
                   "vote": False}
                   
    except Exception as e:
        print(f"Grok API error: {e}. Returning fallback response.")
        return {"model": MODEL_NAME, 
               "contribution": "I encountered an error processing this request.", 
               "vote": False}

##############################
# DeepSeek Integration
##############################
def deepseek_chat(discussion_topic, context_messages=None, stream=False):
    """
    Calls the DeepSeek API for chat completions with structured output.
    """
    from pydantic import BaseModel
    from openai import OpenAI
    
    MODEL_NAME = "DeepSeek"

    # Ensure "json" word appears in both system prompt and content for DeepSeek
    system_prompt = get_default_system_prompt(MODEL_NAME) + "\nRespond in JSON format with 'contribution' and 'vote' fields."

    messages = [{"role": "system", "content": system_prompt}]
    
    # Format context messages correctly with model identities
    if context_messages:
        formatted_context = []
        for msg in context_messages:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                formatted_context.append(msg)
            elif isinstance(msg, dict) and 'model' in msg and 'content' in msg:
                formatted_context.append({
                    "role": "assistant", 
                    "content": f"{msg['model']}: {msg['content']}"
                })
            elif isinstance(msg, str):
                formatted_context.append({"role": "assistant", "content": msg})
        messages.extend(formatted_context)
        
    # Explicitly include "json" in the user message
    messages.append({"role": "user", "content": f"Discuss the following topic and provide your answer in JSON format: {discussion_topic}"})

    client = OpenAI(
        api_key=get_deepseek_api_key(),
        base_url="https://api.deepseek.com",
    )
    
    try:
        # First try without response_format to avoid the error
        completion = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=stream
        )
        
        content = completion.choices[0].message.content
        try:
            parsed_output = json.loads(content)
            return {"model": MODEL_NAME, "contribution": parsed_output.get("contribution", ""), "vote": parsed_output.get("vote", False)}
        except json.JSONDecodeError:
            # If not valid JSON, extract using string manipulation
            return {"model": MODEL_NAME, "contribution": content, "vote": False}
    except Exception as e:
        print(f"DeepSeek API error: {e}. Returning fallback response.")
        return {"model": MODEL_NAME, "contribution": "I encountered an error when processing your request.", "vote": False}

##############################
# Claude (Anthropic) Integration
##############################
def claude_chat(discussion_topic, context_messages=None, system_prompt=None):
    """
    Calls the Anthropic Claude API with structured output.
    """
    import anthropic
    
    MODEL_NAME = "Claude"

    default_system = get_default_system_prompt(MODEL_NAME)
    system = system_prompt if system_prompt is not None else default_system

    # Format context messages correctly
    formatted_messages = []
    if context_messages:
        for msg in context_messages:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                if msg['role'] in ['user', 'assistant']:
                    formatted_messages.append(msg)
                else:
                    formatted_messages.append({"role": "assistant", "content": msg['content']})
            elif isinstance(msg, dict) and 'model' in msg and 'content' in msg:
                # Include model identity
                formatted_messages.append({
                    "role": "assistant", 
                    "content": f"{msg['model']}: {msg['content']}"
                })
            elif isinstance(msg, str):
                formatted_messages.append({"role": "assistant", "content": msg})
    
    formatted_messages.append({"role": "user", "content": f"Discuss the following topic: {discussion_topic}"})

    client = anthropic.Anthropic(api_key=get_anthropic_api_key())
    
    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=2048,
            system=system,
            messages=formatted_messages
        )
        
        # Fix the JSON parsing issue
        content = response.content[0].text if isinstance(response.content, list) else response.content
        
        try:
            parsed = json.loads(content)
            return {"model": MODEL_NAME, "contribution": parsed.get("contribution", ""), "vote": parsed.get("vote", False)}
        except json.JSONDecodeError:
            # If not valid JSON, use the raw content
            return {"model": MODEL_NAME, "contribution": content, "vote": False}
    except Exception as e:
        print(f"Claude API error: {e}. Returning fallback response.")
        return {"model": MODEL_NAME, "contribution": "I encountered an error when processing your request.", "vote": False}

def summarize_discussion(discussion_context):
    """
    Summarize the discussion context into a final answer.
    The function takes a list of discussion contributions and returns a summary string.
    """
    # Convert dictionary items to strings before joining
    formatted_context = []
    for item in discussion_context:
        if isinstance(item, dict):
            # Format dictionary items appropriately
            if 'model' in item and 'contribution' in item:
                formatted_context.append(f"{item['model']}: {item['contribution']}")
            elif 'content' in item:
                role = item.get('role', '')
                formatted_context.append(f"{role.capitalize() if role else ''}{': ' if role else ''}{item['content']}")
        elif isinstance(item, str):
            formatted_context.append(item)
    
    combined_context = "\n".join(formatted_context)
    summary_prompt = (
        "You are a summarization assistant. Given the following discussion transcript, "
        "please provide a concise final summary:\n\n" + combined_context
    )
    summary_result = gpt4o_chat(summary_prompt, context_messages=[])
    return summary_result.get("contribution", "No summary available.")
