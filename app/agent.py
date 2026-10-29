"""LangGraph agent for insurance policy intelligence."""

import json
import re
from typing import Any, Dict, List, Optional, TypedDict, Annotated
from operator import add

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.llm_config import get_llm
from app.mcp_client import MCPClient
from app.evidence_tracker import EvidenceTracker


# Define the agent state
class AgentState(TypedDict):
    """State for the LangGraph agent workflow."""
    user_query: str
    conversation_history: List[Dict]
    tool_calls: List[Dict]
    tool_results: List[Dict]
    final_answer: Optional[str]
    missing_info: List[str]
    continue_decision: Optional[str]
    step_count: int


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
        workflow.add_node("should_continue", self._should_continue)
        workflow.add_node("generate_answer", self._generate_answer)

        # Set entry point
        workflow.set_entry_point("analyze_intent")

        # Add edges
        workflow.add_edge("analyze_intent", "call_tools")
        workflow.add_edge("call_tools", "should_continue")

        # Conditional edge: decide whether to continue or generate answer
        workflow.add_conditional_edges(
            "should_continue",
            self._route_continue,
            {
                "continue": "analyze_intent",
                "end": "generate_answer"
            }
        )

        workflow.add_edge("generate_answer", END)

        # Compile the graph
        return workflow.compile()

    def _analyze_intent(self, state: AgentState) -> AgentState:
        """
        Analyze the user query using LLM to determine which tools to call.

        Args:
            state: Current agent state

        Returns:
            Updated state with tool_calls populated
        """
        user_query = state["user_query"]
        step_count = state.get("step_count", 0)

        print(f"\n[Agent] Analyzing intent for query: {user_query} (Step {step_count + 1})")

        # Use LLM to analyze intent and extract parameters
        intent_prompt = f"""You are an intelligent assistant for insurance policy intelligence. Analyze the user's query and determine which tools to call.

Available tools:
1. search_policies - Search for insurance policies with filters
   Parameters: query (required), category (optional), status (optional), limit (optional)
2. compare_policies - Compare multiple policies side-by-side
   Parameters: policy_ids (required, list of 2-5 policy IDs)
3. check_eligibility - Check if an applicant meets policy eligibility criteria
   Parameters: policy_id (required), applicant_info (required - dict with fields like annual_turnover, business_age_years, financial_statements, etc.)

User query: "{user_query}"

Respond in JSON format with this structure:
{{
    "intent": "search|compare|eligibility|none",
    "tool_calls": [
        {{
            "tool": "tool_name",
            "arguments": {{"param": "value"}}
        }}
    ],
    "missing_info": ["list of missing information if any"]
}}

If policy IDs are mentioned, extract them (they look like TCI-DOM-001, TCI-EXP-002, etc.).
If applicant information is mentioned, extract it (age, turnover, business years, etc.).
If parameters are missing, list them in missing_info.
Only call tools if you have sufficient information. If multiple tools are needed (e.g., search then compare), include all in tool_calls."""

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a helpful assistant that responds only in valid JSON format."),
                HumanMessage(content=intent_prompt)
            ])

            # Parse the LLM response
            response_text = response.content.strip()

            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)

            intent_data = json.loads(response_text)

            tool_calls = intent_data.get("tool_calls", [])
            missing_info = intent_data.get("missing_info", [])

            # Validate and clean tool calls
            valid_tool_calls = []
            for tc in tool_calls:
                tool_name = tc.get("tool")
                arguments = tc.get("arguments", {})

                # Ensure tool names are valid
                if tool_name in ["search_policies", "compare_policies", "check_eligibility"]:
                    valid_tool_calls.append({
                        "tool": tool_name,
                        "arguments": arguments
                    })

            # If no valid tool calls, add none
            if not valid_tool_calls:
                valid_tool_calls.append({
                    "tool": "none",
                    "arguments": {}
                })

            print(f"[Agent] LLM determined intent: {intent_data.get('intent')}")
            print(f"[Agent] Tool calls: {len(valid_tool_calls)}")
            for tc in valid_tool_calls:
                print(f"  - {tc['tool']}: {tc['arguments']}")

            if missing_info:
                print(f"[Agent] Missing info: {missing_info}")

            state["tool_calls"] = valid_tool_calls
            state["missing_info"] = missing_info

        except Exception as e:
            print(f"[Agent] LLM intent analysis failed: {e}, falling back to rule-based")
            # Fallback to rule-based analysis
            tool_calls, missing_info = self._fallback_intent_analysis(user_query)
            state["tool_calls"] = tool_calls
            state["missing_info"] = missing_info

        return state

    def _should_continue(self, state: AgentState) -> AgentState:
        """
        Determine if the agent should continue with additional tool calls.

        This enables multi-step workflows like:
        - Search for policies → Use results to compare specific policies
        - Search → Compare → Check eligibility

        Args:
            state: Current agent state

        Returns:
            Updated state with continue_decision added
        """
        # Safety check: prevent infinite loops (max 3 steps)
        step_count = state.get("step_count", 0)
        if step_count >= 3:
            print(f"[Agent] Maximum steps reached, stopping")
            state["continue_decision"] = "end"
            return state

        tool_results = state["tool_results"]
        print(f"\n[Agent] Deciding whether to continue...")

        # Check if we have search results that could be used for comparison
        has_search_results = any(
            tr["tool"] == "search_policies" and
            tr["result"].get("success") and
            tr["result"].get("count", 0) > 0
            for tr in tool_results
        )

        # Check if user's original query mentioned comparison
        user_query = state["user_query"].lower()
        wants_comparison = "compare" in user_query

        # If we have search results and user wants comparison, extract policy IDs and continue
        if has_search_results and wants_comparison:
            # Find the search result
            search_result = next(
                tr for tr in tool_results
                if tr["tool"] == "search_policies" and tr["result"].get("success")
            )

            # Extract policy IDs from search results (take first 2-3)
            policies = search_result["result"].get("results", [])
            if len(policies) >= 2:
                policy_ids = [p["policy_id"] for p in policies[:3]]
                print(f"[Agent] Continuing with comparison of found policies: {policy_ids}")

                # Add comparison tool call to state and clear previous tool_calls
                state["tool_calls"] = [{
                    "tool": "compare_policies",
                    "arguments": {"policy_ids": policy_ids}
                }]
                state["continue_decision"] = "continue"
                state["step_count"] = step_count + 1
                return state

        # Otherwise, we're done
        print(f"[Agent] Workflow complete, generating final answer")
        state["continue_decision"] = "end"
        return state

    def _route_continue(self, state: AgentState) -> str:
        """
        Route the workflow based on continue decision.

        Args:
            state: Current agent state

        Returns:
            "continue" or "end"
        """
        return state.get("continue_decision", "end")

    def _fallback_intent_analysis(self, query: str) -> tuple:
        """
        Fallback rule-based intent analysis if LLM fails.

        Args:
            query: User's natural language query

        Returns:
            Tuple of (tool_calls, missing_info)
        """
        tool_calls = []
        missing_info = []
        query_lower = query.lower()

        # Determine which tools to call based on keywords
        # Check for combined intents first (search + compare)
        has_search = "search" in query_lower or "find" in query_lower or "look for" in query_lower
        has_compare = "compare" in query_lower
        has_eligibility = "eligibility" in query_lower or "eligible" in query_lower

        if has_search and has_compare:
            # Combined search and compare - only do search first, let should_continue handle comparison
            tool_calls.append({
                "tool": "search_policies",
                "arguments": self._extract_search_params(query)
            })
        elif has_search:
            tool_calls.append({
                "tool": "search_policies",
                "arguments": self._extract_search_params(query)
            })
        elif has_compare:
            policy_ids = self._extract_policy_ids(query)
            if policy_ids:
                tool_calls.append({
                    "tool": "compare_policies",
                    "arguments": {"policy_ids": policy_ids}
                })
            else:
                missing_info.append("policy_ids for comparison")
        elif has_eligibility:
            policy_id = self._extract_policy_id(query)
            applicant_info = self._extract_applicant_info(query)

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
                    missing_info.append("policy_id for eligibility check")
                if not applicant_info:
                    missing_info.append("applicant information (age, turnover, etc.) for eligibility check")

        if not tool_calls:
            tool_calls.append({"tool": "none", "arguments": {}})

        return tool_calls, missing_info

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

        # Extract category if mentioned - map to actual category names
        category_mapping = {
            "domestic": "Domestic Trade Credit",
            "export": "Export Trade Credit",
            "single buyer": "Single Buyer",
            "whole turnover": "Whole Turnover"
        }

        for keyword, category_name in category_mapping.items():
            if keyword in query_lower:
                params["category"] = category_name
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
        applicant_info = {}
        query_lower = query.lower()

        # Extract age (personal age, not business age)
        age_match = re.search(r'(\d+)\s*years?\s*old', query_lower)
        if age_match:
            applicant_info["age"] = int(age_match.group(1))

        # Extract annual turnover/revenue with multipliers
        turnover_patterns = [
            (r'(\d+(?:,\d+)*)\s*million\s*(?:turnover|revenue)', True),  # True = multiply by million
            (r'(\d+(?:,\d+)*)\s*(?:turnover|revenue)\s*of\s*(\d+(?:,\d+)*)\s*million', True),
            (r'annual\s*turnover\s*(?:of\s*)?(\d+(?:,\d+)*)', False),
            (r'revenue\s*(?:of\s*)?(\d+(?:,\d+)*)', False),
        ]

        for pattern, is_million in turnover_patterns:
            match = re.search(pattern, query_lower)
            if match:
                value = match.group(1).replace(',', '')
                if is_million:
                    applicant_info["annual_turnover"] = int(value) * 1_000_000
                else:
                    applicant_info["annual_turnover"] = int(value)
                break

        # Extract business age/registration years
        business_age_patterns = [
            r'business\s*(?:for\s*)?(\d+)\s*years?',
            r'(\d+)\s*years?\s*(?:in\s*business|registered)',
            r'business\s*age\s*(?:of\s*)?(\d+)',
        ]

        for pattern in business_age_patterns:
            match = re.search(pattern, query_lower)
            if match:
                applicant_info["business_age_years"] = int(match.group(1))
                break

        # Extract financial statements
        if 'financial statements' in query_lower or 'audited' in query_lower:
            applicant_info["financial_statements"] = True

        # Extract export years
        export_match = re.search(r'(\d+)\s*years?\s*(?:in\s*)?export', query_lower)
        if export_match:
            applicant_info["export_years"] = int(export_match.group(1))

        return applicant_info if applicant_info else None

    def _call_tools(self, state: AgentState) -> AgentState:
        """
        Execute the selected MCP tools with enhanced error handling.

        Args:
            state: Current agent state with tool_calls populated

        Returns:
            Updated state with tool_results populated
        """
        tool_calls = state["tool_calls"]
        new_tool_results = []

        print(f"\n[Agent] Executing {len(tool_calls)} tool call(s)...")

        try:
            with MCPClient() as client:
                for tool_call in tool_calls:
                    tool_name = tool_call["tool"]
                    arguments = tool_call["arguments"]

                    print(f"[Agent] Calling tool: {tool_name}")

                    try:
                        if tool_name == "search_policies":
                            result = client.search_policies(**arguments)
                            new_tool_results.append({
                                "tool": tool_name,
                                "arguments": arguments,
                                "result": result,
                                "success": result.get("success", False)
                            })

                        elif tool_name == "compare_policies":
                            result = client.compare_policies(**arguments)
                            new_tool_results.append({
                                "tool": tool_name,
                                "arguments": arguments,
                                "result": result,
                                "success": result.get("success", False)
                            })

                        elif tool_name == "check_eligibility":
                            result = client.check_eligibility(**arguments)
                            new_tool_results.append({
                                "tool": tool_name,
                                "arguments": arguments,
                                "result": result,
                                "success": result.get("success", False)
                            })

                        elif tool_name == "none":
                            # No tools to call
                            new_tool_results.append({
                                "tool": "none",
                                "arguments": {},
                                "result": {"message": "No tools were called"},
                                "success": True
                            })

                    except Exception as tool_error:
                        print(f"[Agent] Tool {tool_name} failed: {tool_error}")
                        new_tool_results.append({
                            "tool": tool_name,
                            "arguments": arguments,
                            "result": {"error": str(tool_error)},
                            "success": False
                        })

        except Exception as e:
            print(f"[Agent] MCP client connection error: {e}")
            new_tool_results.append({
                "tool": "error",
                "arguments": {},
                "result": {"error": f"Failed to connect to MCP server: {str(e)}"},
                "success": False
            })

        print(f"[Agent] Completed {len(new_tool_results)} tool execution(s)")
        # Append new results to existing results
        state["tool_results"] = state["tool_results"] + new_tool_results
        return state

    def _generate_answer(self, state: AgentState) -> AgentState:
        """
        Generate a grounded response based on tool results using LLM.

        Args:
            state: Current agent state with tool_results populated

        Returns:
            Updated state with final_answer populated
        """
        tool_results = state["tool_results"]
        missing_info = state["missing_info"]
        user_query = state["user_query"]

        print(f"\n[Agent] Generating grounded answer from {len(tool_results)} result(s)...")

        # Check if there are tool errors
        has_errors = any(not tr.get("success", True) for tr in tool_results if tr["tool"] != "none")

        # Check if there's missing information
        if missing_info:
            final_answer = self._generate_clarifying_questions(missing_info, user_query)
            state["final_answer"] = final_answer
            return state

        # Check if there were errors in tool execution
        if has_errors:
            final_answer = self._handle_tool_errors(tool_results, user_query)
            state["final_answer"] = final_answer
            return state

        # Generate answer based on tool results
        if not tool_results or tool_results[0]["tool"] == "none":
            final_answer = self._generate_fallback_response(user_query)
            state["final_answer"] = final_answer
            return state

        # Prepare context from tool results for LLM
        context_parts = []
        policy_ids_cited = []
        evidence_tracker = EvidenceTracker()

        for tool_result in tool_results:
            tool_name = tool_result["tool"]
            result = tool_result["result"]

            if tool_name == "search_policies":
                if result.get("success") and result.get("count", 0) > 0:
                    policies = result["results"]
                    policy_ids = [p["policy_id"] for p in policies]
                    policy_ids_cited.extend(policy_ids)

                    # Create concise summary for context
                    context_parts.append(f"Search found {result['count']} policies:")
                    for policy in policies[:5]:
                        context_parts.append(f"- {policy['policy_id']}: {policy['title']}")
                        context_parts.append(f"  Category: {policy['category']}, Premium: {policy['premium']['amount']} {policy['premium']['currency']}")
                else:
                    context_parts.append("Search found no matching policies.")

            elif tool_name == "compare_policies":
                if result.get("success"):
                    policies = result["policies"]
                    policy_ids = [p["policy_id"] for p in policies]
                    policy_ids_cited.extend(policy_ids)

                    # Extract evidence metadata if available
                    if result.get("evidence_metadata") and result["evidence_metadata"].get("has_evidence"):
                        sources = result["evidence_metadata"].get("sources", [])
                        for source in sources:
                            context_parts.append(f"Source: {evidence_tracker.format_citation(source)} = {source.get('display_value', source.get('value'))}")

                    context_parts.append(f"Compared {len(policies)} policies:")
                    for policy in policies:
                        context_parts.append(f"- {policy['policy_id']}: {policy['title']}")
                        context_parts.append(f"  Premium: {policy['premium']['amount']} {policy['premium']['currency']}, Deductible: {policy.get('deductible', {}).get('amount', 'N/A')} {policy.get('deductible', {}).get('currency', '')}")
                else:
                    context_parts.append(f"Comparison failed: {result.get('error', 'Unknown error')}")

            elif tool_name == "check_eligibility":
                if result.get("success"):
                    policy_ids_cited.append(result["policy_id"])

                    # Extract evidence metadata if available
                    if result.get("evidence_metadata") and result["evidence_metadata"].get("has_evidence"):
                        sources = result["evidence_metadata"].get("sources", [])
                        for source in sources:
                            context_parts.append(f"Source: {evidence_tracker.format_citation(source)} = {source.get('display_value', source.get('value'))}")

                    context_parts.append(f"Eligibility check for {result['policy_id']} ({result['policy_title']}):")
                    context_parts.append(f"Status: {result['overall_status'].upper()}")
                    context_parts.append(f"Summary: {result['summary']}")

                    if result.get("criteria_results"):
                        context_parts.append("Criteria breakdown:")
                        for criterion in result["criteria_results"]:
                            context_parts.append(f"- {criterion['criterion']}: {criterion['status'].upper()}")
                else:
                    context_parts.append(f"Eligibility check failed: {result.get('error', 'Unknown error')}")

            elif tool_name == "error":
                context_parts.append(f"Error: {result.get('error', 'Unknown error')}")

        # Use LLM to generate grounded answer
        context = "\n".join(context_parts)
        unique_policy_ids = list(set(policy_ids_cited))

        grounded_prompt = f"""You are an insurance policy assistant. Answer the user's question based ONLY on the provided tool results.

User Question: {user_query}

Tool Results:
{context}

Requirements:
1. Answer the question using ONLY the information from the tool results above
2. Do NOT make up or hallucinate any information
3. If information is not available in the tool results, say so explicitly
4. Cite policy IDs using this format: [TCI-DOM-001] when referring to specific policies
5. For specific field values, use field-level citations like: [TCI-DOM-001:premium] = 25000 INR
6. Keep the answer concise and natural
7. Do NOT include full policy details in the answer - only cite policy IDs and specific field values
8. Focus on directly answering the user's question

Policy IDs referenced: {', '.join(unique_policy_ids) if unique_policy_ids else 'None'}

Generate a helpful, grounded answer:"""

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a helpful insurance policy assistant that provides grounded answers based only on provided tool results."),
                HumanMessage(content=grounded_prompt)
            ])

            final_answer = response.content.strip()
            print(f"[Agent] LLM generated grounded answer")

        except Exception as e:
            print(f"[Agent] LLM answer generation failed: {e}, using template-based answer")
            # Fallback to template-based answer
            final_answer = context

        state["final_answer"] = final_answer
        return state

    def _generate_clarifying_questions(self, missing_info: List[str], user_query: str) -> str:
        """
        Generate clarifying questions for missing information.

        Args:
            missing_info: List of missing information items
            user_query: Original user query for context

        Returns:
            Formatted clarifying questions
        """
        # Deduplicate missing info
        unique_missing = list(dict.fromkeys(missing_info))
        clarifying_questions = []

        # Group by type to avoid duplicates
        has_policy_id = any("policy_id" in info for info in unique_missing)
        has_applicant = any("applicant" in info for info in unique_missing)
        has_compare = any("compare" in info.lower() for info in unique_missing)

        if has_policy_id and has_compare:
            clarifying_questions.append("Which policies would you like to compare? Please provide the policy IDs (e.g., TCI-DOM-001, TCI-DOM-002).")
        elif has_policy_id:
            clarifying_questions.append("Which policy would you like to check? Please provide the policy ID (e.g., TCI-DOM-001).")

        if has_applicant:
            clarifying_questions.append("Please provide your information such as:")
            clarifying_questions.append("  - Annual turnover (e.g., 15 million)")
            clarifying_questions.append("  - Business age in years (e.g., 3 years)")
            clarifying_questions.append("  - Whether you have financial statements")

        # Use LLM to generate natural clarifying response
        if self.llm:
            clarifying_prompt = f"""The user asked: "{user_query}"

I need the following information to help them:
{chr(10).join(f"- {q}" for q in clarifying_questions)}

Generate a polite, natural response asking for this information. Keep it concise and helpful."""

            try:
                response = self.llm.invoke([
                    SystemMessage(content="You are a helpful assistant."),
                    HumanMessage(content=clarifying_prompt)
                ])
                return response.content.strip()
            except Exception:
                pass  # Fall through to template

        # Fallback to template
        return "I need some additional information to help you:\n\n" + "\n".join(f"- {q}" for q in clarifying_questions)

    def _handle_tool_errors(self, tool_results: List[Dict], user_query: str) -> str:
        """
        Handle errors from tool execution.

        Args:
            tool_results: List of tool results with errors
            user_query: Original user query

        Returns:
            Error response message
        """
        errors = []
        for tr in tool_results:
            if not tr.get("success", True) and tr["tool"] != "none":
                error_msg = tr.get("result", {}).get("error", "Unknown error")
                errors.append(f"{tr['tool']}: {error_msg}")

        if not errors:
            errors = ["Unknown error occurred"]

        # Use LLM to generate natural error response
        if self.llm:
            error_prompt = f"""The user asked: "{user_query}"

I encountered these errors while trying to help:
{chr(10).join(f"- {e}" for e in errors)}

Generate a polite, helpful response explaining what went wrong and suggesting what the user can do. Keep it concise."""

            try:
                response = self.llm.invoke([
                    SystemMessage(content="You are a helpful assistant."),
                    HumanMessage(content=error_prompt)
                ])
                return response.content.strip()
            except Exception:
                pass  # Fall through to template

        # Fallback to template
        return f"I encountered an error while processing your request:\n\n" + "\n".join(f"- {e}" for e in errors) + "\n\nPlease try again or rephrase your question."

    def _generate_fallback_response(self, user_query: str) -> str:
        """
        Generate a fallback response for unanswerable queries.

        Args:
            user_query: Original user query

        Returns:
            Fallback response message
        """
        fallback_msg = "I'm not sure how to help with that query. You can ask me to:\n"
        fallback_msg += "- Search for insurance policies (e.g., 'Find domestic trade credit insurance')\n"
        fallback_msg += "- Compare policies (e.g., 'Compare TCI-DOM-001 and TCI-DOM-002')\n"
        fallback_msg += "- Check eligibility (e.g., 'Check eligibility for TCI-DOM-001 with 15 million turnover and 3 years in business')"

        return fallback_msg

    def run(self, user_query: str) -> Dict[str, Any]:
        """
        Run the agent with a user query.

        Args:
            user_query: Natural language query from the user

        Returns:
            Dictionary with the agent's response
        """
        # Initialize state with fresh lists
        initial_state: AgentState = {
            "user_query": user_query,
            "conversation_history": [],
            "tool_calls": [],
            "tool_results": [],
            "final_answer": None,
            "missing_info": [],
            "continue_decision": None,
            "step_count": 0
        }

        # Run the graph
        final_state = self.graph.invoke(initial_state)

        return {
            "answer": final_state["final_answer"],
            "tool_calls": final_state["tool_calls"],
            "tool_results": final_state["tool_results"],
            "missing_info": final_state["missing_info"]
        }
