from app.agent.validator_agent import ValidatorAgent
from app.utils.user_guidance import user_guidance
from app.utils.cost_tracker import cost_tracker

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
    print("\nPlease wait, I am analyzing your idea...\n")

    # Validate the idea
    result = agent.validate_idea(project_idea)

    # Check if validation failed
    if result.get('validation_failed'):
        print(f"\n\n{'='*70}")
        print(f"YOUR PROJECT ANALYSIS")
        print(f"{'='*70}\n")
        print(f"Score: {result['score']} out of 100\n")
        print(f"❌ {result['reasoning']}\n")
        print(f"{'='*70}\n")
        return

    # Print analysis results
    print(f"\n\n{'='*70}")
    print(f"YOUR PROJECT ANALYSIS")
    print(f"{'='*70}\n")

    print(f"Score: {result['score']} out of 100")
    print(f"\n{'='*70}")

    print(f"\nMarket Opportunity (Is there real demand?):")
    print(f"{result['market_opportunity']}\n")

    print(f"{'='*70}")
    print(f"\nHow Hard Is It To Build?")
    print(f"{result['feasibility']}\n")

    print(f"{'='*70}")
    print(f"\nWhat You Will Need:")
    print(f"{result['resources_required']}\n")

    print(f"{'='*70}")
    print(f"\nThings To Do:")
    print(f"{result['dos']}\n")

    print(f"{'='*70}")
    print(f"\nThings To Avoid:")
    print(f"{result['donts']}\n")

    print(f"{'='*70}")
    print(f"\nProblems That Could Happen:")
    print(f"{result['key_risks']}\n")

    print(f"{'='*70}")
    print(f"\nHow Long Will It Take?")
    print(f"{result['timeline']}\n")

    print(f"{'='*70}")
    print(f"\nWhat To Do First:")
    print(f"{result['next_step']}\n")

    print(f"{'='*70}")
    print(f"\nMy Recommendation: {result['recommendation']}")

    # Show changes required if recommendation is "Consider changes"
    if result['recommendation'] == "Consider changes":
        print(f"\n{'='*70}")
        print(f"\nHow To Fix It:")
        if result['changes_required'] and result['changes_required'] != "N/A":
            print(f"{result['changes_required']}\n")
        else:
            print(f"See the 'Things To Do' and 'Things To Avoid' sections above for guidance.\n")

    print(f"{'='*70}\n")

    # Ask if user wants to send analysis to email
    send_email = input("Do you want to send this analysis to your email? (yes/no): ").strip().lower()

    if send_email == "yes" or send_email == "y":
        email_address = input("Enter your email address: ").strip()

        if "@" in email_address:
            print("\nSending analysis to your email...\n")

            # Call the email tool through the agent
            email_result = agent.send_analysis_via_email(email_address, result)

            print(email_result)
        else:
            print("\n❌ Invalid email address. Please try again.\n")

    # Show cost summary
    cost_tracker.print_summary()
    

if __name__ == "__main__":
    main()