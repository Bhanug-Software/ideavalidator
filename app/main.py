from app.agent.validator_agent import ValidatorAgent
from app.utils.logger import logger
from app.utils.user_guidance import user_guidance

def main():
    """Validator agent - interactive mode"""

    # Show user guidance
    user_guidance.show_format()

    # Get project idea from user
    project_idea = input("\n> ").strip()

    # Create agent
    agent = ValidatorAgent()

    # Step 1: Starting validation
    print("\n" + "=" * 80)
    print("STEP 1: STARTING VALIDATION")
    print("=" * 80)
    print(f"Project Idea: {project_idea}\n")

    # Step 2: Sending to Claude
    print("=" * 80)
    print("STEP 2: SENDING PROJECT IDEA TO CLAUDE")
    print("=" * 80)
    print("Analyzing project idea...\n")

    # Validate the idea
    result = agent.validate_idea(project_idea)

    # Step 3: Raw response from Claude
    print("\n" + "=" * 80)
    print("STEP 3: RAW RESPONSE FROM CLAUDE")
    print("=" * 80)
    print(result['raw_response'])
    print()

    # Step 4: Parsed results
    print("=" * 80)
    print("STEP 4: PARSED RESULTS")
    print("=" * 80)
    print(f"\n📊 Viability Score: {result['score']}/100")
    print(f"\n💡 Reasoning:\n{result['reasoning']}")
    print(f"\n✅ Recommendation: {result['recommendation']}")
    print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    main()
