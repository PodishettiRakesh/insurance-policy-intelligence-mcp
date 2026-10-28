# Insurance Policy Intelligence - MCP

Backend-only MCP and Agentic AI project for searching, comparing, and analyzing insurance policies using Python, MCP, and LangGraph.

## Overview

This project implements a Model Context Protocol (MCP) server that allows clients to search and compare insurance policies. The server exposes tools for searching policies with filters and comparing multiple policies side-by-side.

## Features

- **Pydantic Models**: Structured data validation for insurance policies
- **Policy Catalogue**: 15 sample trade credit insurance policies
- **Search Functionality**: Case-insensitive keyword matching across title, description, coverage, and tags
- **Filters**: Optional category and status filtering
- **Policy Comparison**: Compare 2-5 policies side-by-side across coverage, exclusions, premiums, deductibles, and eligibility
- **MCP Server**: Official Python MCP SDK with stdio transport
- **MCP Client**: Tool discovery and invocation support
- **Comprehensive Tests**: 75 tests covering models, catalogue, search, comparison, server, client, and e2e flows

## Technology Stack

- **Python**: 3.11+
- **Data Validation**: Pydantic v2.14.1
- **MCP SDK**: Official Python MCP SDK v2.3.0
- **Testing**: pytest v9.2.0
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
│   └── server.py          # MCP server
├── data/
│   └── policies.json      # Sample policy data
├── tests/
│   ├── __init__.py
│   ├── test_models.py     # Model validation tests
│   ├── test_catalogue.py  # Catalogue loading tests
│   ├── test_search.py     # Search logic tests
│   ├── test_comparison.py # Comparison logic tests
│   ├── test_mcp_server.py # MCP server tests
│   ├── test_client.py     # MCP client tests
│   └── test_e2e.py        # End-to-end integration tests
├── venv/                  # Virtual environment
├── requirements.txt       # Python dependencies
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

## Testing Coverage

The project includes 56 tests across 6 test files:

- **test_models.py** (13 tests): Pydantic model validation
- **test_catalogue.py** (8 tests): Policy loading and validation
- **test_search.py** (22 tests): Search logic and filters
- **test_mcp_server.py** (3 tests): MCP server configuration
- **test_client.py** (7 tests): MCP client interaction
- **test_e2e.py** (3 tests): End-to-end integration flows

All tests pass successfully.

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

While the current milestone focuses on the MCP server and client foundation, future stages may include:

- LangGraph integration for natural-language policy questions
- Retrieval-augmented generation (RAG)
- Frontend or chat interface
- Persistent database storage
- Advanced retrieval, ranking, and metadata filtering
- Authentication, authorization, and deployment

## License

See LICENSE file for details.

## Contributing

This project is currently in development. Contributions are welcome after the initial milestone is complete.
