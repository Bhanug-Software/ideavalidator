import re
from app.agent.validator_agent import ValidatorAgent
from app.utils.user_guidance import user_guidance
from app.memory.memory_store import (
    save_conversation,
    save_message,
    load_conversations,
    load_conversation_messages,
    update_conversation_status
)


def validate_email(email):
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def show_previous_conversations():
    """Show previous conversations and let user choose to continue or start new"""
    conversations = load_conversations()

    if not conversations:
        return None  # No previous conversations

    print("\n" + "=" * 70)
    print("PREVIOUS CONVERSATIONS")
    print("=" * 70)

    for i, conv in enumerate(conversations, 1):
        idea = conv['project_idea'][:50]
        status = conv['status']
        date = conv['created_at'].strftime("%Y-%m-%d %H:%M") if hasattr(conv['created_at'], 'strftime') else conv['created_at']
        print(f"{i}. {idea}... ({status}) - {date}")

    print(f"{len(conversations) + 1}. Start new conversation")
    print("=" * 70)

    choice = input("\nChoose an option (number): ").strip()

    try:
        choice_num = int(choice)
        if 1 <= choice_num <= len(conversations):
            return conversations[choice_num - 1]['id']  # Return conversation_id
        elif choice_num == len(conversations) + 1:
            return None  # Start new
        else:
            print("Invalid choice")
            return show_previous_conversations()  # Ask again
    except:
        print("Invalid input")
        return show_previous_conversations()  # Ask again

def main():
    """Interactive project idea validator with multi-turn conversation and persistent memory"""

    # Check for previous conversations
    conversation_id = show_previous_conversations()

    # If continuing previous conversation
    if conversation_id:
        print(f"\n[*] Loading previous conversation...\n")
        loaded_messages = load_conversation_messages(conversation_id)

        # Format messages for Claude
        messages = [{"role": msg['role'], "content": msg['content']} for msg in loaded_messages]
        conversation_history = messages.copy()
        project_idea = messages[0]['content'] if messages else "Unknown"

        print(f"Loaded {len(loaded_messages)} previous messages")
        print("=" * 70)
        print("You can now ask follow-up questions about this idea\n")

    else:
        # New conversation
        user_guidance.show_format()
        project_idea = input("\n> ").strip()

        if not project_idea:
            print("\n❌ Error: Please enter a project idea!")
            return

        print("\n" + "=" * 70)
        print(f"Checking: {project_idea}")
        print("=" * 70)
        print("\n[*] Analyzing your idea...\n")

        # Create agent
        agent = ValidatorAgent()

        # Validate the idea
        result = agent.validate_idea(project_idea)

        # Check if validation failed
        if result.get('validation_failed'):
            print(f"\n\n{'='*70}")
            print(f"YOUR PROJECT ANALYSIS")
            print(f"{'='*70}\n")
            error_msg = result.get('reasoning', result.get('final_recommendation', 'Validation error'))
            print(f"❌ {error_msg}\n")
            print(f"{'='*70}\n")
            return

        # Save conversation to database
        try:
            conversation_id = save_conversation(
                project_idea,
                result.get('final_recommendation', 'No recommendation')
            )
            print(f"\n[DB] Conversation saved (ID: {conversation_id})")
        except Exception as e:
            print(f"\n⚠️  Could not save to database: {e}")
            conversation_id = None

        # Save initial user message and analysis
        if conversation_id:
            try:
                save_message(conversation_id, "user", project_idea)
                save_message(conversation_id, "assistant", result.get('raw_response', ''))
            except Exception as e:
                print(f"⚠️  Could not save messages: {e}")

        # Analysis already streamed above, just add separator
        print(f"\n{'='*70}\n")

        # Multi-turn conversation loop
        messages = [{"role": "user", "content": project_idea}] + [{"role": "assistant", "content": result.get('raw_response', '')}]
        conversation_history = [
            {"role": "user", "content": project_idea},
            {"role": "assistant", "content": result.get('raw_response', '')}
        ]

    # Multi-turn conversation loop (for both new and continued conversations)
    while True:
        follow_up = input("Do you have a follow-up question? (yes/no): ").strip().lower()

        if follow_up not in ["yes", "y"]:
            break

        question = input("\nYour question: ").strip()

        if not question:
            print("❌ Please enter a question\n")
            continue

        print("\n[*] Processing your question...\n")

        # Save user question to database
        if conversation_id:
            try:
                save_message(conversation_id, "user", question)
            except Exception as e:
                print(f"⚠️  Could not save question: {e}")

        # Create agent for follow-ups (moved inside loop)
        agent = ValidatorAgent()

        # Process follow-up question
        follow_up_result = agent.ask_follow_up(question, messages, conversation_history)

        # Check if follow-up failed
        if follow_up_result.get('validation_failed'):
            print(f"\n❌ {follow_up_result.get('reasoning', 'Failed to process question')}\n")
            continue

        # Save assistant response to database
        assistant_response = follow_up_result.get('follow_up_response', '')
        if conversation_id and assistant_response:
            try:
                save_message(conversation_id, "assistant", assistant_response)
            except Exception as e:
                print(f"⚠️  Could not save response: {e}")

        # Update conversation state
        messages = follow_up_result.get('messages', messages)
        conversation_history = follow_up_result.get('conversation_history', conversation_history)

        print(f"\n{'='*70}\n")

    # Mark conversation as completed
    if conversation_id:
        try:
            update_conversation_status(conversation_id, "completed")
            print(f"\n[DB] Conversation marked as completed")
        except Exception as e:
            print(f"⚠️  Could not update status: {e}")

    # Ask if user wants to send analysis to email
    send_email = input("Do you want to send this analysis to your email? (yes/no): ").strip().lower()

    if send_email == "yes" or send_email == "y":
        email_address = input("Enter your email address: ").strip()

        if validate_email(email_address):
            print("\nSending analysis to your email...\n")

            # For new conversations, we have result; for continued ones, we need to format it
            if 'result' in locals():
                email_result = agent.send_analysis_via_email(email_address, result)
                print(email_result)
            else:
                print("⚠️  Cannot send email for continued conversation (feature coming soon)\n")
        else:
            print("\n❌ Invalid email address format. Please use: user@example.com\n")


if __name__ == "__main__":
    main()