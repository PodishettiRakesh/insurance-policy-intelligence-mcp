# Insurance Policy Intelligence - MCP

Backend-only MCP and Agentic AI project for searching, comparing, and analyzing insurance policies using Python, MCP, LangGraph, and LLMs.

## Overview

This project implements a Model Context Protocol (MCP) server with an intelligent LangGraph-based agent that can answer natural language questions about insurance policies. The agent intelligently selects and invokes search, comparison, and eligibility tools, generates grounded answers based on actual tool outputs, and handles missing information by asking clarifying questions.

## Features

### Core Features
- **Pydantic Models**: Structured data validation for insurance policies
- **Policy Catalogue**: 15 sample trade credit insurance policies
- **Search Functionality**: Case-insensitive keyword matching across title, description, coverage, and tags
- **Filters**: Optional category and status filtering
- **Policy Comparison**: Compare 2-5 policies side-by-side across coverage, exclusions, premiums, deductibles, and eligibility
- **Eligibility Checking**: Evaluate whether applicants meet policy eligibility criteria with detailed criterion-by-criterion analysis
- **MCP Server**: Official Python MCP SDK with stdio transport
- **MCP Client**: Tool discovery and invocation support
- **Gradio Chat Interface**: Web-based UI for natural language interaction with the agent
- **Comprehensive Tests**: 105 tests covering models, catalogue, search, comparison, eligibility, server, client, and e2e flows

### LangGraph Agent Features
- **LLM-Powered Intent Analysis**: Uses OpenRouter (OpenAI-compatible) LLM to understand natural language queries
- **Intelligent Tool Selection**: Automatically determines which tools to call (search, compare, eligibility)
- **Multi-Step Workflows**: Supports complex workflows like "search then compare"
- **Grounded Answer Generation**: Generates responses strictly based on tool results with policy ID citations
- **Error Handling**: Graceful error handling with natural error messages
- **Missing Information Detection**: Asks clarifying questions when required information is missing
- **Fallback Mechanisms**: Rule-based fallback when LLM is unavailable

## Technology Stack

- **Python**: 3.11+
- **Data Validation**: Pydantic v2.14.1
- **MCP SDK**: Official Python MCP SDK v2.3.0
- **LangGraph**: v0.2.0+ for agent workflow orchestration
- **LangChain**: v0.3.0+ for LLM integration
- **LLM Provider**: OpenRouter (OpenAI-compatible API)
- **Testing**: pytest v9.2.0
- **Web UI**: Gradio v4.0.0+ for chat interface
- **Transport**: stdio (for local development)

## Project Structure

```
insurance-policy-intelligence-mcp/
├── app/
│   ├── __init__.py
│   ├── models.py          # Pydantic policy models
│   ├── catalogue.py       # Policy catalogue loader
│   ├── search.py          # Search implementation
│   ├── comparison.py      # Policy comparison service
│   ├── eligibility.py     # Eligibility evaluation service
│   ├── server.py          # MCP server
│   ├── llm_config.py      # LLM provider configuration (OpenRouter)
│   ├── mcp_client.py      # MCP client integration layer
│   ├── agent.py           # LangGraph agent workflow
│   └── ui.py              # Gradio chat interface
├── data/
│   └── policies.json      # Sample policy data
├── tests/
│   ├── __init__.py
│   ├── test_models.py     # Model validation tests
│   ├── test_catalogue.py  # Catalogue loading tests
│   ├── test_search.py     # Search logic tests
│   ├── test_comparison.py # Comparison logic tests
│   ├── test_eligibility.py # Eligibility evaluation tests
│   ├── test_mcp_server.py # MCP server tests
│   ├── test_client.py     # MCP client tests
│   └── test_e2e.py        # End-to-end integration tests
├── venv/                  # Virtual environment
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
├── test_mcp_client.py     # MCP client integration test
├── test_agent.py          # LangGraph agent test
├── README.md             # This file
└── .gitignore
```

## Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd insurance-policy-intelligence-mcp
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Configure environment variables:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenRouter API key
# OPENROUTER_API_KEY=your_api_key_here
```

## Running the MCP Server

### Start the Server

```bash
python -m app.server
```

The server starts with stdio transport by default, which is suitable for local development and MCP client connections.

### Manual Testing with JSON-RPC

You can test the server manually by sending JSON-RPC requests:

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"ping"}' | python -m app.server
```

## Gradio Chat Interface

A web-based chat interface is available for interacting with the Insurance Policy Intelligence agent.

### Installation

Ensure Gradio is installed:

```bash
pip install -r requirements.txt
```

### Start the UI

```bash
python -m app.ui
```

The interface will be available at http://127.0.0.1:7860 by default.

### Configuration

You can configure the UI server using environment variables:

- `GRADIO_SERVER_NAME`: Server host (default: `127.0.0.1`)
- `GRADIO_SERVER_PORT`: Server port (default: `7860`)
- `GRADIO_SHARE`: Set to `true` to create a public shareable link (default: `false`)

Example:

```bash
# Set server to listen on all interfaces
GRADIO_SERVER_NAME=0.0.0.0 python -m app.ui

# Use a different port
GRADIO_SERVER_PORT=8080 python -m app.ui
```

### Example Questions

The UI includes example questions you can try:

- **Policy Search**: "Find domestic trade credit insurance policies"
- **Policy Comparison**: "Compare policies TCI-DOM-001 and TCI-DOM-002"
- **Eligibility Check**: "Check eligibility for TCI-DOM-001. I have annual turnover of 15 million, business is 3 years old, and I have financial statements."
- **Unsupported Query**: "What's the weather today?"

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Files

```bash
# Model tests
pytest tests/test_models.py

# Search tests
pytest tests/test_search.py

# Comparison tests
pytest tests/test_comparison.py

# Eligibility tests
pytest tests/test_eligibility.py

# MCP server tests
pytest tests/test_mcp_server.py

# Client tests
pytest tests/test_client.py

# End-to-end tests
pytest tests/test_e2e.py
```

### Run Tests with Verbose Output

```bash
pytest -v
```

## Usage Example

### Using the LangGraph Agent

The LangGraph agent provides a natural language interface for querying insurance policies. Here's how to use it:

```python
from app.agent import InsurancePolicyAgent

# Initialize the agent
agent = InsurancePolicyAgent()

# Search for policies
result = agent.run("Find domestic trade credit insurance policies")
print(result["answer"])

# Compare policies
result = agent.run("Compare policies TCI-DOM-001 and TCI-DOM-002")
print(result["answer"])

# Check eligibility
result = agent.run(
    "Check eligibility for TCI-DOM-001. "
    "I have annual turnover of 15 million, business is 3 years old, and I have financial statements."
)
print(result["answer"])

# Multi-step workflow (search then compare)
result = agent.run("Find domestic policies and compare them")
print(result["answer"])
```

#### Example Agent Responses

**Search Query:**
```
User: Find domestic trade credit insurance policies

Agent: Here are the available domestic trade credit insurance policies:

1. [TCI-DOM-001]: Domestic Trade Credit Insurance - Standard, Premium: 25,000 INR
2. [TCI-DOM-002]: Domestic Trade Credit Insurance - Premium, Premium: 45,000 INR
3. [TCI-DOM-003]: Domestic Trade Credit Insurance - SME, Premium: 12,000 INR

If you need more information about any specific policy, feel free to ask!
```

**Compare Query:**
```
User: Compare policies TCI-DOM-001 and TCI-DOM-002

Agent: Based on the comparison of [TCI-DOM-001] and [TCI-DOM-002]:

[TCI-DOM-001] (Standard) has a premium of 25,000 INR with a 5,000 INR deductible.
[TCI-DOM-002] (Premium) has a higher premium of 45,000 INR but a lower deductible of 3,000 INR.

The Premium policy offers higher coverage (95% vs 90%) and additional risk management services.
```

**Eligibility Query:**
```
User: Check eligibility for TCI-DOM-001 with 15 million turnover and 3 years in business

Agent: Based on the eligibility check for [TCI-DOM-001]:

Status: ELIGIBLE

All 3 criteria have been met:
- Minimum annual turnover requirement: PASSED (15,000,000 meets 10,000,000 minimum)
- Business registration requirement: PASSED (3 years meets 2 year minimum)
- Financial statements requirement: PASSED
```

**Missing Information:**
```
User: Check eligibility for a policy

Agent: I need some additional information to help you:

- Which policy would you like to check? Please provide the policy ID (e.g., TCI-DOM-001).
- Please provide your information such as:
  - Annual turnover (e.g., 15 million)
  - Business age in years (e.g., 3 years)
  - Whether you have financial statements
```

### Using the MCP Client

The project includes test clients that demonstrate how to connect to the server and invoke the search tool. See `tests/test_client.py` and `tests/test_e2e.py` for examples.

### Search Tool Parameters

The `search_policies_tool` accepts the following parameters:

- **query** (required): Text to search for in policy title, description, coverage, and tags
- **category** (optional): Restrict results to a specific policy category
- **status** (optional): Restrict results to "active" or "inactive" policies
- **limit** (optional): Maximum number of results to return (default: 10, max: 50)

### Compare Policies Tool Parameters

The `compare_policies_tool` accepts the following parameters:

- **policy_ids** (required): List of policy IDs to compare (2-5 policies)

The tool returns a detailed comparison including:
- Policy details (title, category, provider, coverage, exclusions, premium, deductible, eligibility)
- Coverage comparison (common items, unique items per policy)
- Exclusions comparison (common items, unique items per policy)
- Premium comparison (amounts, currencies, periods)
- Deductible comparison (amounts, currencies, missing deductibles)
- Eligibility comparison (requirements, structured criteria)
- Missing fields identification

### Check Eligibility Tool Parameters

The `check_eligibility_tool` accepts the following parameters:

- **policy_id** (required): The policy ID to check eligibility for
- **applicant_info** (required): Dictionary containing applicant information for evaluation

The tool returns a detailed eligibility evaluation including:
- Overall status: "eligible", "ineligible", or "undetermined"
- Individual criterion results for each eligibility requirement
- Human-readable summary of the evaluation

Supported applicant information fields include:
- `annual_turnover`, `turnover`, `revenue`: Annual business turnover
- `business_age_years`, `registration_years`, `years_in_business`: Business duration
- `financial_statements`, `audited_financial_statements`: Document availability
- `export_license`, `export_years`: Export-specific information
- `credit_rating`, `buyer_credit_rating`: Credit assessment
- `customer_concentration`, `largest_buyer_percentage`: Customer diversity
- `operating_regions`, `has_domestic_operations`, `has_export_operations`: Regional operations
- `compliance_status`, `regulatory_compliance`: Regulatory compliance
- And many more field variations for different requirement types

### Example Search Requests

**Basic search:**
```json
{
  "name": "search_policies_tool",
  "arguments": {
    "query": "domestic",
    "limit": 5
  }
}
```

**Search with category filter:**
```json
{
  "name": "search_policies_tool",
  "arguments": {
    "query": "insurance",
    "category": "Export Trade Credit",
    "limit": 3
  }
}
```

**Search with status filter:**
```json
{
  "name": "search_policies_tool",
  "arguments": {
    "query": "trade",
    "status": "active",
    "limit": 5
  }
}
```

**Search with combined filters:**
```json
{
  "name": "search_policies_tool",
  "arguments": {
    "query": "credit",
    "category": "Single Buyer",
    "status": "active",
    "limit": 5
  }
}
```

### Example Compare Policies Requests

**Compare two policies:**
```json
{
  "name": "compare_policies_tool",
  "arguments": {
    "policy_ids": ["TCI-DOM-001", "TCI-DOM-002"]
  }
}
```

**Compare three policies:**
```json
{
  "name": "compare_policies_tool",
  "arguments": {
    "policy_ids": ["TCI-DOM-001", "TCI-EXP-001", "TCI-SB-001"]
  }
}
```

### Example Check Eligibility Requests

**Check eligibility - eligible applicant:**
```json
{
  "name": "check_eligibility_tool",
  "arguments": {
    "policy_id": "TCI-DOM-001",
    "applicant_info": {
      "annual_turnover": 15000000,
      "business_age_years": 3,
      "financial_statements": true
    }
  }
}
```

**Check eligibility - ineligible applicant:**
```json
{
  "name": "check_eligibility_tool",
  "arguments": {
    "policy_id": "TCI-DOM-002",
    "applicant_info": {
      "annual_turnover": 30000000,
      "registration_years": 2,
      "audited_financial_statements": true
    }
  }
}
```

**Check eligibility - undetermined (missing information):**
```json
{
  "name": "check_eligibility_tool",
  "arguments": {
    "policy_id": "TCI-EXP-002",
    "applicant_info": {
      "export_years": 4
    }
  }
}
```

**Check eligibility - export policy with multiple criteria:**
```json
{
  "name": "check_eligibility_tool",
  "arguments": {
    "policy_id": "TCI-EXP-002",
    "applicant_info": {
      "annual_turnover": 25000000,
      "export_years": 4,
      "regulatory_compliance": true
    }
  }
}
```

## Sample Data

The project includes 15 sample trade credit insurance policies covering:

- **Domestic Trade Credit** (3 policies): Standard, Premium, SME
- **Export Trade Credit** (3 policies): Basic, Comprehensive, High-Risk Markets
- **Single Buyer** (4 policies): Domestic, Export, Project-Based, Government
- **Whole Turnover** (3 policies): Domestic, Export, Hybrid
- **Legacy** (1 policy): Retired (inactive status)

Each policy includes:
- Policy ID, title, category, provider
- Description and coverage details
- Exclusions
- Premium and deductible information
- Eligibility criteria
- Effective date and status
- Searchable tags

## API Reference

### Policy Model

```python
class Policy(BaseModel):
    policy_id: str
    title: str
    category: str
    provider: str
    description: str
    coverage: List[str]
    exclusions: List[str]
    premium: Premium
    deductible: Optional[Deductible]
    eligibility: Optional[Eligibility]
    effective_date: Optional[date]
    status: PolicyStatus
    tags: List[str]
```

### Search Function

```python
def search_policies(
    query: str,
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10
) -> List[Policy]
```

### Eligibility Check Function

```python
def check_eligibility(
    policy_id: str,
    applicant_info: Dict[str, Any]
) -> EligibilityCheckResult
```

The eligibility checker evaluates criteria patterns including:
- Minimum/maximum turnover requirements
- Business registration duration
- Export business experience
- License and document requirements
- Credit ratings
- Customer diversity (concentration limits)
- Multi-region operations
- Government contract requirements
- Compliance status
- And more specialized criteria

Each criterion returns one of three statuses:
- **passed**: Applicant meets the requirement
- **failed**: Applicant does not meet the requirement
- **undetermined**: Insufficient information to evaluate (never assumes eligibility)

## Testing Coverage

The project includes comprehensive tests across multiple test files:

### Core MCP Tests (105 tests)
- **test_models.py** (13 tests): Pydantic model validation
- **test_catalogue.py** (8 tests): Policy loading and validation
- **test_search.py** (22 tests): Search logic and filters
- **test_comparison.py** (16 tests): Policy comparison logic
- **test_eligibility.py** (30 tests): Eligibility evaluation logic
- **test_mcp_server.py** (3 tests): MCP server configuration
- **test_client.py** (7 tests): MCP client interaction
- **test_e2e.py** (3 tests): End-to-end integration flows

### Agent Integration Tests
- **test_mcp_client.py**: Tests MCP client integration with the server
- **test_agent.py**: Tests LangGraph agent workflow including:
  - Search queries with LLM intent analysis
  - Policy comparison
  - Eligibility checking
  - Missing information handling
  - Multi-step workflows (search → compare)
  - Error handling

### Running Agent Tests

```bash
# Test MCP client integration
python test_mcp_client.py

# Test LangGraph agent
python test_agent.py
```

All core tests (models, catalogue, search, comparison, eligibility) pass successfully.

## Troubleshooting

### Import Errors

If you encounter "ModuleNotFoundError: No module named 'app'", ensure you're running Python with the module syntax:

```bash
python -m app.server  # Correct
python app/server.py  # Incorrect
```

### Virtual Environment Issues

If you have trouble activating the virtual environment on Windows PowerShell, you may need to change the execution policy:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

### MCP Inspector

To use the MCP Inspector for interactive testing, ensure Node.js and `npx` are installed on your PATH. The MCP SDK includes the `[cli]` extra for this purpose.

## Future Enhancements

Potential future enhancements for the project:

- **Chat CLI Interface**: Interactive command-line interface for conversational agent interaction
- **Retrieval-Augmented Generation (RAG)**: Vector-based retrieval for more advanced policy analysis
- **Remote MCP Transport**: Support for SSE or WebSocket transport for remote deployment
- **Persistent Database Storage**: Replace JSON file with proper database backend
- **Advanced Retrieval**: More sophisticated ranking and metadata filtering
- **Authentication & Authorization**: User management and access control
- **Multi-Turn Conversations**: Enhanced conversation history and context retention
- **Policy Recommendations**: Intelligent policy recommendation engine

## License

See LICENSE file for details.

## Contributing

This project is currently in development. Contributions are welcome after the initial milestone is complete.
