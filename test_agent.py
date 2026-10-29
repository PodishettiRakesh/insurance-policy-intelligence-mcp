"""Test script to verify LangGraph agent workflow."""

from app.agent import InsurancePolicyAgent

def test_agent():
    """Test the LangGraph agent with various queries."""
    print("Testing LangGraph Agent...")
    print("=" * 60)

    # Test 1: Search query
    print("\nTest 1: Search for domestic policies")
    print("-" * 60)
    agent1 = InsurancePolicyAgent()
    result1 = agent1.run("Find domestic trade credit insurance policies")
    print(f"Answer:\n{result1['answer']}")
    print(f"\nTool calls: {len(result1['tool_calls'])}")
    print(f"Tool results: {len(result1['tool_results'])}")

    # Test 2: Compare query
    print("\n" + "=" * 60)
    print("\nTest 2: Compare two policies")
    print("-" * 60)
    agent2 = InsurancePolicyAgent()
    result2 = agent2.run("Compare policies TCI-DOM-001 and TCI-DOM-002")
    print(f"Answer:\n{result2['answer']}")
    print(f"\nTool calls: {len(result2['tool_calls'])}")
    print(f"Tool results: {len(result2['tool_results'])}")

    # Test 3: Eligibility query
    print("\n" + "=" * 60)
    print("\nTest 3: Check eligibility")
    print("-" * 60)
    agent3 = InsurancePolicyAgent()
    result3 = agent3.run(
        "Check eligibility for policy TCI-DOM-001. "
        "I have annual turnover of 15 million, business is 3 years old, and I have financial statements."
    )
    print(f"Answer:\n{result3['answer']}")
    print(f"\nTool calls: {len(result3['tool_calls'])}")
    print(f"Tool results: {len(result3['tool_results'])}")

    # Test 4: Missing information
    print("\n" + "=" * 60)
    print("\nTest 4: Query with missing information")
    print("-" * 60)
    agent4 = InsurancePolicyAgent()
    result4 = agent4.run("Check eligibility for a policy")
    print(f"Answer:\n{result4['answer']}")
    print(f"\nMissing info: {result4['missing_info']}")

    # Test 5: Unknown query
    print("\n" + "=" * 60)
    print("\nTest 5: Unknown query")
    print("-" * 60)
    agent5 = InsurancePolicyAgent()
    result5 = agent5.run("What's the weather today?")
    print(f"Answer:\n{result5['answer']}")

    # Test 6: Multi-step workflow (search then compare)
    print("\n" + "=" * 60)
    print("\nTest 6: Multi-step workflow (search then compare)")
    print("-" * 60)
    agent6 = InsurancePolicyAgent()
    result6 = agent6.run("Find domestic policies and compare them")
    print(f"Answer:\n{result6['answer']}")
    print(f"\nTotal tool calls: {len(result6['tool_calls'])}")
    print(f"Total tool results: {len(result6['tool_results'])}")

    print("\n" + "=" * 60)
    print("✅ Agent tests completed!")

if __name__ == "__main__":
    test_agent()
