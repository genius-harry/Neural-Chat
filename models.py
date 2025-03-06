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
from config import RESPONSE_LENGTH

def get_default_system_prompt(model_name=None, response_length=RESPONSE_LENGTH):
    participant_models = ["GPT-4o", "Gemini", "DeepSeek", "Grok", "Claude"]
    
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
        "5. Always respond to previous models' contributions if they exist. Build upon or challenge their ideas.\n"
        f"6. RESPONSE LENGTH: Target around {response_length} words. Your response MUST NOT exceed {int(response_length * 1.3)} words. Shorter, more focused responses are preferred.\n"
        "7. Unless you are the first to respond, you MUST refer to at least one previous response from another model.\n"
        "8. You can ask questions to other models to encourage further discussion.\n"
        "9. You can challenge or critique other models' reasoning if you find flaws in their arguments.\n"
        "10. Do NOT focus too much on repeating what has already been discussed. Instead, add new insights, information, or perspectives.\n"
        "    Brief summaries when agreeing with or critiquing others are acceptable, but avoid lengthy rehashing of previous points.\n"
        "    Focus on moving the discussion forward with new contributions rather than just echoing what's already been said.\n\n"
        f"You are participating in a dialogue with the following models(including yourself({model_name})): {', '.join(participant_models)}."
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
    system_prompt = get_default_system_prompt(MODEL_NAME) + """
    IMPORTANT REMINDER: You MUST refer to at least one previous model by their exact name (e.g., "Gemini mentioned..." or "I disagree with Claude's point about..."). 
    Use conversational language as if you are directly speaking to the other models in a group chat. 
    If there are no previous responses, you can start the discussion with your own perspective.
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    
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
    
    CRITICAL INSTRUCTION: You MUST refer to other models by their exact names (e.g., "GPT-4o", "Claude", "Gemini", etc.) 
    when responding to their points. Use conversational language as if you're talking directly to them in a chat.
    
    Example response:
    {
        "contribution": "I see what GPT-4o is saying about X, but I think Claude's perspective on Y makes more sense because...",
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
    import re
    
    MODEL_NAME = "DeepSeek"

    # Make the instructions more explicit about boolean values and addressing other models
    system_prompt = get_default_system_prompt(MODEL_NAME) + """
    Respond in JSON format with 'contribution' and 'vote' fields. The 'vote' field MUST be a boolean value (true or false, not 'Yes' or 'No').
    
    CRITICAL INSTRUCTION: You MUST refer to at least one previous model by their exact name (GPT-4o, Gemini, Grok, or Claude) when responding. 
    Use conversational language as if you're directly talking to them in a group chat.
    
    Example:
    {"contribution": "I agree with what GPT-4o said about X, but Claude's point about Y makes me think...", "vote": true}
    """

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
        
    # Explicitly mention boolean values in the user message
    messages.append({"role": "user", "content": f"Discuss the following topic and provide your answer in JSON format. The 'vote' field MUST be a boolean value (true or false, not 'Yes' or 'No'): {discussion_topic}"})

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
            # Check if the content is inside JSON code block
            if "```json" in content:
                # Extract JSON from code block
                json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
            
            parsed_output = json.loads(content)
            
            # Convert string votes to boolean values
            vote = parsed_output.get("vote", False)
            if isinstance(vote, str):
                # Convert string votes like "Yes", "No", "True", "False" to boolean values
                normalized_vote = vote.lower()
                if normalized_vote in ["true", "yes", "y", "1"]:
                    vote = True
                else:
                    vote = False
            
            return {"model": MODEL_NAME, "contribution": parsed_output.get("contribution", ""), "vote": vote}
        except json.JSONDecodeError:
            # If not valid JSON, check for vote:true or vote:false in the text
            if '"vote": true' in content or '"vote":true' in content:
                vote = True
            else:
                vote = False
            return {"model": MODEL_NAME, "contribution": content, "vote": vote}
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

    default_system = get_default_system_prompt(MODEL_NAME) + """
    CRITICAL INSTRUCTION: You MUST refer to at least one previous model by their exact name (GPT-4o, Gemini, Grok, or DeepSeek) when responding.
    Use conversational language as if you're directly talking to them in a group chat. For example: "I see GPT-4o's point about X, but I think..."
    """
    
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

def summarize_discussion(discussion_context, discussion_topic=None):
    """
    Summarize the discussion context into a final answer.
    The function takes a list of discussion contributions and returns a summary string.
    
    Args:
        discussion_context: List of discussion contributions
        discussion_topic: Original topic provided by the user (optional)
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
    
    # Add the original discussion topic to the summary prompt if provided
    topic_context = f"Original discussion topic: {discussion_topic}\n\n" if discussion_topic else ""
    
    summary_prompt = (
        "You are a summarization assistant. "
        f"{topic_context}"
        "Given the following discussion transcript, "
        "please provide a concise final summary that directly addresses the original topic:\n\n" + combined_context
    )
    
    summary_result = gpt4o_chat(summary_prompt, context_messages=[])
    return summary_result.get("contribution", "No summary available.")
