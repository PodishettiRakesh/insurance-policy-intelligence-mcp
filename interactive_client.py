"""Interactive CLI for testing the MCP server."""

import json
import subprocess
import sys
from pathlib import Path


def send_request(proc, method, params=None):
    """Send a JSON-RPC request and get response."""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method
    }
    if params:
        request["params"] = params

    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    response_line = proc.stdout.readline()
    if response_line:
        return json.loads(response_line)
    return None


def extract_result_text(response):
    """Extract the actual result text from MCP response format."""
    result = response.get("result", {})
    if isinstance(result, dict) and "content" in result:
        return result["content"][0]["text"]
    return result


def start_server():
    """Start the MCP server."""
    base_dir = Path(__file__).parent
    proc = subprocess.Popen(
        [sys.executable, "-m", "app.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(base_dir)
    )

    # Initialize the server
    send_request(proc, "initialize", {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "interactive-cli", "version": "1.0.0"}
    })
    send_request(proc, "notifications/initialized")

    return proc


def search_policies(proc, query, category=None, status=None, limit=10):
    """Search policies using the MCP tool."""
    arguments = {
        "query": query,
        "limit": limit
    }
    if category:
        arguments["category"] = category
    if status:
        arguments["status"] = status

    response = send_request(proc, "tools/call", {
        "name": "search_policies_tool",
        "arguments": arguments
    })

    if response:
        result_text = extract_result_text(response)
        return json.loads(result_text)
    return None


def display_results(result):
    """Display search results in a readable format."""
    if not result["success"]:
        print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
        return

    count = result["count"]
    policies = result["results"]

    print(f"\n✓ Found {count} policy(ies):\n")

    for i, policy in enumerate(policies, 1):
        print(f"{i}. {policy['title']}")
        print(f"   ID: {policy['policy_id']}")
        print(f"   Category: {policy['category']}")
        print(f"   Provider: {policy['provider']}")
        print(f"   Status: {policy['status']}")
        print(f"   Description: {policy['description']}")
        if policy.get('tags'):
            print(f"   Tags: {', '.join(policy['tags'])}")
        print()


def main():
    """Run the interactive CLI."""
    print("=" * 60)
    print("Insurance Policy Intelligence - Interactive Search")
    print("=" * 60)
    print("\nCommands:")
    print("  search <query>                    - Search policies")
    print("  search <query> --cat <category>   - Search with category filter")
    print("  search <query> --status <status>  - Search with status filter")
    print("  help                              - Show this help")
    print("  quit                              - Exit")
    print("\nCategories: Domestic Trade Credit, Export Trade Credit, Single Buyer, Whole Turnover")
    print("Status: active, inactive")
    print("=" * 60)

    # Start the server
    print("\nStarting MCP server...")
    proc = start_server()
    print("Server ready!\n")

    try:
        while True:
            try:
                user_input = input(">>> ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nGoodbye!")
                    break

                if user_input.lower() == 'help':
                    print("\nCommands:")
                    print("  search <query>                    - Search policies")
                    print("  search <query> --cat <category>   - Search with category filter")
                    print("  search <query> --status <status>  - Search with status filter")
                    print("  help                              - Show this help")
                    print("  quit                              - Exit")
                    print("\nCategories: Domestic Trade Credit, Export Trade Credit, Single Buyer, Whole Turnover")
                    print("Status: active, inactive")
                    continue

                # Parse search command
                if user_input.lower().startswith('search '):
                    parts = user_input[7:].strip().split('--')
                    query = parts[0].strip()
                    category = None
                    status = None
                    limit = 5

                    for part in parts[1:]:
                        part = part.strip()
                        if part.startswith('cat '):
                            category = part[4:].strip()
                        elif part.startswith('status '):
                            status = part[7:].strip()
                        elif part.startswith('limit '):
                            limit = int(part[6:].strip())

                    if not query:
                        print("❌ Please provide a search query")
                        continue

                    print(f"\nSearching for: '{query}'")
                    if category:
                        print(f"Category: {category}")
                    if status:
                        print(f"Status: {status}")

                    result = search_policies(proc, query, category, status, limit)
                    display_results(result)
                else:
                    print("❌ Unknown command. Type 'help' for available commands.")

            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'quit' to exit.")
            except Exception as e:
                print(f"❌ Error: {e}")

    finally:
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    main()
