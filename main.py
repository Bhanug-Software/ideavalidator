from app.agent.validator_agent import ValidatorAgent

def main():
    """Interactive project idea validator"""

    # Create agent
    agent = ValidatorAgent()

    # Display welcome message
    print("\n" + "=" * 70)
    print("PROJECT IDEA VALIDATOR")
    print("=" * 70)
    print("\nHi! I will help you check if your project idea is good.")
    print("\nTell me your project idea:")
    print("(What do you want to build and for whom?)\n")

    # Get user input at runtime
    project_idea = input("Your project idea: ").strip()

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
    if result['recommendation'] == "Consider changes" and result['changes_required'] != "N/A":
        print(f"\n{'='*70}")
        print(f"\nHow To Fix It:")
        print(f"{result['changes_required']}\n")

    print(f"{'='*70}\n")
    

if __name__ == "__main__":
    main()