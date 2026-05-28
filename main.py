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

    print(f"\n💡 Idea Summary:")
    print(f"{result['idea_summary']}\n")

    print(f"{'='*70}")
    print(f"\n🎯 Problem Statement:")
    print(f"{result['problem_statement']}\n")

    print(f"{'='*70}")
    print(f"\n👥 Target Audience:")
    print(f"{result['target_audience']}\n")

    print(f"{'='*70}")
    print(f"\n📊 Market Validation:")
    print(f"{result['market_validation']}\n")

    print(f"{'='*70}")
    print(f"\n🔍 Competitor Analysis:")
    print(f"{result['competitor_analysis']}\n")

    print(f"{'='*70}")
    print(f"\n🚀 MVP Recommendation:")
    print(f"{result['mvp_recommendation']}\n")

    print(f"{'='*70}")
    print(f"\n⚠️  Risk Analysis:")
    print(f"{result['risk_analysis']}\n")

    print(f"{'='*70}")
    print(f"\n✅ Final Recommendation: {result['final_recommendation']}")

    print(f"\n{'='*70}\n")

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