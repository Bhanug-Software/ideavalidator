from app.agent.validator_agent import ValidatorAgent

def main():
    """Test the validator agent"""

    # Create agent
    agent = ValidatorAgent()

    # Test with a project idea
    project_idea = "i want to build a AI-Powered Study Companion for Medical Students"

    print("=" * 60)
    print(f"Validating: {project_idea}")
    print("=" * 60)

    # Validate the idea
    result = agent.validate_idea(project_idea)

    # Print parsed results
    print(f"\n\nPARSED RESULTS:")
    print("=" * 60)
    print(f"Score: {result['score']}/100")
    print("=" * 60)
    print(f"Reasoning: {result['reasoning']}")
    print("=" * 60)
    print(f"Recommendation: {result['recommendation']}")
    

if __name__ == "__main__":
    main()