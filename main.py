import re
from app.agent.validator_agent import ValidatorAgent
from app.utils.user_guidance import user_guidance

def validate_email(email):
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def main():
    """Interactive project idea validator"""

    # Show user guidance
    user_guidance.show_format()

    # Get user input at runtime
    project_idea = input("\n> ").strip()

    # Create agent
    agent = ValidatorAgent()

    # Validate that user provided input
    if not project_idea:
        print("\n❌ Error: Please enter a project idea!")
        return

    print("\n" + "=" * 70)
    print(f"Checking: {project_idea}")
    print("=" * 70)
    print("\n🔍 Analyzing your idea...\n")

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

    # Analysis already streamed above, just add separator
    print(f"\n{'='*70}\n")

    # Ask if user wants to send analysis to email
    send_email = input("Do you want to send this analysis to your email? (yes/no): ").strip().lower()

    if send_email == "yes" or send_email == "y":
        email_address = input("Enter your email address: ").strip()

        if validate_email(email_address):
            print("\nSending analysis to your email...\n")

            # Call the email tool through the agent
            email_result = agent.send_analysis_via_email(email_address, result)

            print(email_result)
        else:
            print("\n❌ Invalid email address format. Please use: user@example.com\n")


if __name__ == "__main__":
    main()