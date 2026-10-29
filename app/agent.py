"""LangGraph agent for insurance policy intelligence."""

import json
from typing import Any, Dict, List, Optional, TypedDict, Annotated
from operator import add

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from app.llm_config import get_llm
from app.mcp_client import MCPClient


# Define the agent state
class AgentState(TypedDict):
    """State for the LangGraph agent workflow."""
    user_query: str
    conversation_history: Annotated[List[Dict], add]
    tool_calls: Annotated[List[Dict], add]
    tool_results: Annotated[List[Dict], add]
    final_answer: Optional[str]
    missing_info: Annotated[List[str], add]


class InsurancePolicyAgent:
    """
    LangGraph-based agent for answering insurance policy questions.

    The agent analyzes user queries, determines which MCP tools to call,
    executes those tools, and generates grounded answers based on the results.
    """

    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        Initialize the agent.

        Args:
            llm: Optional LLM instance (will use default if not provided)
        """
        self.llm = llm or get_llm(temperature=0.7)
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.

        Returns:
            Compiled StateGraph ready for execution
        """
        # Create the state graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("analyze_intent", self._analyze_intent)
        workflow.add_node("call_tools", self._call_tools)
        workflow.add_node("generate_answer", self._generate_answer)

        # Set entry point
        workflow.set_entry_point("analyze_intent")

        # Add edges
        workflow.add_edge("analyze_intent", "call_tools")
        workflow.add_edge("call_tools", "generate_answer")
        workflow.add_edge("generate_answer", END)

        # Compile the graph
        return workflow.compile()

    def _analyze_intent(self, state: AgentState) -> AgentState:
        """
        Analyze the user query to determine which tools to call.

        Args:
            state: Current agent state

        Returns:
            Updated state with tool_calls populated
        """
        user_query = state["user_query"]
        print(f"\n[Agent] Analyzing intent for query: {user_query}")

        # Simple rule-based intent analysis (will be enhanced with LLM in Step 3.4)
        tool_calls = []

        query_lower = user_query.lower()

        # Determine which tools to call based on keywords
        if "search" in query_lower or "find" in query_lower or "look for" in query_lower:
            # Search intent
            tool_calls.append({
                "tool": "search_policies",
                "arguments": self._extract_search_params(user_query)
            })

        if "compare" in query_lower:
            # Compare intent - need policy IDs
            # For now, we'll try to extract policy IDs or ask for them
            policy_ids = self._extract_policy_ids(user_query)
            if policy_ids:
                tool_calls.append({
                    "tool": "compare_policies",
                    "arguments": {"policy_ids": policy_ids}
                })
            else:
                # Add to missing info
                state["missing_info"] = ["policy_ids for comparison"]

        if "eligibility" in query_lower or "eligible" in query_lower:
            # Eligibility intent - need policy ID and applicant info
            policy_id = self._extract_policy_id(user_query)
            applicant_info = self._extract_applicant_info(user_query)

            if policy_id and applicant_info:
                tool_calls.append({
                    "tool": "check_eligibility",
                    "arguments": {
                        "policy_id": policy_id,
                        "applicant_info": applicant_info
                    }
                })
            else:
                if not policy_id:
                    state["missing_info"] = ["policy_id for eligibility check"]
                if not applicant_info:
                    state["missing_info"] = ["applicant information (age, turnover, etc.) for eligibility check"]

        # If no tools identified, add to tool_calls as empty to proceed
        if not tool_calls:
            tool_calls.append({
                "tool": "none",
                "arguments": {}
            })

        print(f"[Agent] Determined tool calls: {len(tool_calls)}")
        for tc in tool_calls:
            print(f"  - {tc['tool']}: {tc['arguments']}")

        state["tool_calls"] = tool_calls
        return state

    def _extract_search_params(self, query: str) -> Dict[str, Any]:
        """
        Extract search parameters from user query.

        Args:
            query: User's natural language query

        Returns:
            Dictionary with search parameters
        """
        params = {"query": query, "limit": 10}

        query_lower = query.lower()

        # Extract category if mentioned
        categories = ["domestic", "export", "single buyer", "whole turnover"]
        for category in categories:
            if category in query_lower:
                params["category"] = category.title() if " " not in category else category.title()
                break

        # Extract status if mentioned
        if "active" in query_lower:
            params["status"] = "active"
        elif "inactive" in query_lower:
            params["status"] = "inactive"

        return params

    def _extract_policy_ids(self, query: str) -> Optional[List[str]]:
        """
        Extract policy IDs from user query.

        Args:
            query: User's natural language query

        Returns:
            List of policy IDs or None
        """
        # Look for policy ID patterns (e.g., TCI-DOM-001)
        import re
        pattern = r'TCI-[A-Z]{3}-\d{3}'
        matches = re.findall(pattern, query.upper())
        return matches if matches else None

    def _extract_policy_id(self, query: str) -> Optional[str]:
        """
        Extract a single policy ID from user query.

        Args:
            query: User's natural language query

        Returns:
            Policy ID or None
        """
        policy_ids = self._extract_policy_ids(query)
        return policy_ids[0] if policy_ids else None

    def _extract_applicant_info(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Extract applicant information from user query.

        Args:
            query: User's natural language query

        Returns:
            Dictionary with applicant info or None
        """
        import re

        applicant_info = {}

        # Extract age
        age_match = re.search(r'(\d+)\s*years?\s*old', query.lower())
        if age_match:
            applicant_info["age"] = int(age_match.group(1))

        # Extract turnover
        turnover_match = re.search(r'([\d,]+)\s*(?:million|billion|thousand)?\s*(?:turnover|revenue)', query.lower())
        if turnover_match:
            applicant_info["annual_turnover"] = int(turnover_match.group(1).replace(',', ''))

        # Extract business age
        business_age_match = re.search(r'business\s*(?:for\s*)?(\d+)\s*years?', query.lower())
        if business_age_match:
            applicant_info["business_age_years"] = int(business_age_match.group(1))

        return applicant_info if applicant_info else None

    def _call_tools(self, state: AgentState) -> AgentState:
        """
        Execute the selected MCP tools.

        Args:
            state: Current agent state with tool_calls populated

        Returns:
            Updated state with tool_results populated
        """
        tool_calls = state["tool_calls"]
        tool_results = []

        print(f"\n[Agent] Executing {len(tool_calls)} tool call(s)...")

        try:
            with MCPClient() as client:
                for tool_call in tool_calls:
                    tool_name = tool_call["tool"]
                    arguments = tool_call["arguments"]

                    print(f"[Agent] Calling tool: {tool_name}")

                    if tool_name == "search_policies":
                        result = client.search_policies(**arguments)
                        tool_results.append({
                            "tool": tool_name,
                            "arguments": arguments,
                            "result": result
                        })

                    elif tool_name == "compare_policies":
                        result = client.compare_policies(**arguments)
                        tool_results.append({
                            "tool": tool_name,
                            "arguments": arguments,
                            "result": result
                        })

                    elif tool_name == "check_eligibility":
                        result = client.check_eligibility(**arguments)
                        tool_results.append({
                            "tool": tool_name,
                            "arguments": arguments,
                            "result": result
                        })

                    elif tool_name == "none":
                        # No tools to call
                        tool_results.append({
                            "tool": "none",
                            "arguments": {},
                            "result": {"message": "No tools were called"}
                        })

        except Exception as e:
            print(f"[Agent] Error calling tools: {e}")
            tool_results.append({
                "tool": "error",
                "arguments": {},
                "result": {"error": str(e)}
            })

        print(f"[Agent] Completed {len(tool_results)} tool execution(s)")
        state["tool_results"] = tool_results
        return state

    def _generate_answer(self, state: AgentState) -> AgentState:
        """
        Generate a response based on tool results.

        Args:
            state: Current agent state with tool_results populated

        Returns:
            Updated state with final_answer populated
        """
        tool_results = state["tool_results"]
        missing_info = state["missing_info"]

        print(f"\n[Agent] Generating answer from {len(tool_results)} result(s)...")

        # Check if there's missing information
        if missing_info:
            clarifying_questions = []
            for info in missing_info:
                if "policy_id" in info:
                    clarifying_questions.append("Which policy would you like to check? Please provide the policy ID.")
                elif "applicant" in info:
                    clarifying_questions.append("Please provide your information such as age, annual turnover, and years in business.")

            final_answer = "I need some additional information to help you:\n\n" + "\n".join(f"- {q}" for q in clarifying_questions)
            state["final_answer"] = final_answer
            return state

        # Generate answer based on tool results
        if not tool_results or tool_results[0]["tool"] == "none":
            final_answer = "I'm not sure how to help with that query. You can ask me to:\n- Search for insurance policies\n- Compare policies\n- Check eligibility for a policy"
            state["final_answer"] = final_answer
            return state

        # Build answer from tool results
        answer_parts = []

        for tool_result in tool_results:
            tool_name = tool_result["tool"]
            result = tool_result["result"]

            if tool_name == "search_policies":
                if result.get("success") and result.get("count", 0) > 0:
                    answer_parts.append(f"Found {result['count']} policies:")
                    for policy in result["results"][:5]:  # Limit to 5 for readability
                        answer_parts.append(f"\n- {policy['title']} ({policy['policy_id']})")
                        answer_parts.append(f"  Category: {policy['category']}")
                        answer_parts.append(f"  Provider: {policy['provider']}")
                        answer_parts.append(f"  Premium: {policy['premium']['amount']} {policy['premium']['currency']}")
                else:
                    answer_parts.append("No policies found matching your search.")

            elif tool_name == "compare_policies":
                if result.get("success"):
                    answer_parts.append(f"Comparison of {len(result.get('policies', []))} policies:")
                    for policy in result["policies"]:
                        answer_parts.append(f"\n- {policy['title']} ({policy['policy_id']})")
                        answer_parts.append(f"  Premium: {policy['premium']['amount']} {policy['premium']['currency']}")
                        answer_parts.append(f"  Coverage: {', '.join(policy['coverage'][:3])}...")
                else:
                    answer_parts.append(f"Comparison failed: {result.get('error', 'Unknown error')}")

            elif tool_name == "check_eligibility":
                if result.get("success"):
                    answer_parts.append(f"Eligibility check for {result['policy_title']}:")
                    answer_parts.append(f"\nStatus: {result['overall_status'].upper()}")
                    answer_parts.append(f"\n{result['summary']}")
                else:
                    answer_parts.append(f"Eligibility check failed: {result.get('error', 'Unknown error')}")

            elif tool_name == "error":
                answer_parts.append(f"An error occurred: {result.get('error', 'Unknown error')}")

        final_answer = "\n".join(answer_parts)
        state["final_answer"] = final_answer

        print(f"[Agent] Generated answer")
        return state

    def run(self, user_query: str) -> Dict[str, Any]:
        """
        Run the agent with a user query.

        Args:
            user_query: Natural language query from the user

        Returns:
            Dictionary with the agent's response
        """
        # Initialize state
        initial_state: AgentState = {
            "user_query": user_query,
            "conversation_history": [],
            "tool_calls": [],
            "tool_results": [],
            "final_answer": None,
            "missing_info": []
        }

        # Run the graph
        final_state = self.graph.invoke(initial_state)

        return {
            "answer": final_state["final_answer"],
            "tool_calls": final_state["tool_calls"],
            "tool_results": final_state["tool_results"],
            "missing_info": final_state["missing_info"]
        }
