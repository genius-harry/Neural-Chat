import api_keys
import config
from config import MAX_DISCUSSION_ROUNDS
import atexit
from models import (
    gpt4o_chat,
    gemini_chat,
    grok_chat,
    deepseek_chat,
    claude_chat,
    summarize_discussion
)

def get_result_values(result):
    """
    Helper function to extract 'model', 'contribution' and 'vote' from the result.
    """
    try:
        # For Pydantic models or dictionary results with model info
        model = result.get("model", result.__class__.__name__)
        contribution = result.get("contribution", getattr(result, "contribution", ""))
        vote = result.get("vote", getattr(result, "vote", False))
    except AttributeError:
        # Fallback
        model = "Unknown Model"
        contribution = result.get("contribution", "")
        vote = result.get("vote", False)
    return model, contribution, vote

def cleanup():
    """Clean up resources when the program exits."""
    # Force cleanup of any outstanding gRPC connections
    try:
        import grpc
        grpc.experimental.aio.shutdown_asyncio_engine()
    except (ImportError, AttributeError):
        pass

# Register the cleanup function to run at exit
atexit.register(cleanup)

def main():
    # Initialize an empty list to store the discussion context.
    discussion_context = []

    # Ask the user for the initial topic/message/question.
    topic = input("Enter the discussion topic/message/question: ")

    # List of model functions in the order of discussion.
    model_functions = [
        gpt4o_chat,
        gemini_chat,
        grok_chat,
        deepseek_chat,
        claude_chat
    ]

    current_round = 0
    continue_discussion = True

    while continue_discussion and current_round < config.MAX_DISCUSSION_ROUNDS:
        print(f"\n--- Discussion Round {current_round + 1} ---")
        round_votes = []

        # Iterate through each model.
        for i, model_fn in enumerate(model_functions):
            # Call the model with the topic and the full discussion context
            is_first_turn = current_round == 0 and i == 0
            
            # Pass the first model indicator to ensure proper prompting
            result = model_fn(topic, context_messages=discussion_context)
            
            # Ensure we get valid responses
            if isinstance(result, dict):
                model_name = result.get("model", "Unknown Model")
                contribution = result.get("contribution", "No contribution provided")
                vote = result.get("vote", False)
            else:
                # Fallback for non-dictionary results
                model_name = getattr(result, "model", model_fn.__name__.replace("_chat", "").capitalize())
                contribution = getattr(result, "contribution", "No contribution provided") 
                vote = getattr(result, "vote", False)

            # Display the model's contribution and vote
            print(f"\n{model_name} contributed:\n{contribution}")
            print(f"Vote for further discussion: {vote}")

            # Append to discussion context with model identity
            discussion_context.append({"model": model_name, "content": contribution})
            round_votes.append(vote)

        # Count votes: True means further discussion.
        true_votes = sum(1 for vote in round_votes if vote)
        false_votes = len(round_votes) - true_votes

        print(f"\nRound {current_round + 1} votes -> Further discussion: {true_votes}, Stop: {false_votes}")

        # Continue discussion if more models voted for further discussion.
        if true_votes > false_votes:
            print("Proceeding to the next discussion round...\n")
            continue_discussion = True
        else:
            print("Ending discussion based on votes.\n")
            continue_discussion = False

        current_round += 1

    # After the discussion ends, output the full discussion transcript.
    print("\n--- Final Discussion Transcript ---")
    for idx, entry in enumerate(discussion_context, 1):
        print(f"{idx}. {entry}")

    # Summarize the discussion using the summarize_discussion function.
    final_summary = summarize_discussion(discussion_context)
    print("\n--- Final Summary ---")
    print(final_summary)


if __name__ == "__main__":
    main()