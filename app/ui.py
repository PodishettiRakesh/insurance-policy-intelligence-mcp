"""Modern Gradio chat interface for Insurance Policy Intelligence."""

import os
import gradio as gr

from app.agent import InsurancePolicyAgent


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

SERVER_NAME = os.getenv("GRADIO_SERVER_NAME", "127.0.0.1")
SERVER_PORT = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
SHARE = os.getenv("GRADIO_SHARE", "false").lower() == "true"


# ---------------------------------------------------------
# Custom styling
# ---------------------------------------------------------

CUSTOM_CSS = """
/* Overall application */
.gradio-container {
    max-width: 1500px !important;
    margin: auto !important;
}

/* Header */
.app-header {
    padding: 22px 28px;
    border-radius: 16px;
    background: linear-gradient(120deg, #eff6ff, #ffffff);
    border: 1px solid #dbeafe;
    margin-bottom: 16px;
}

.app-title {
    font-size: 27px !important;
    font-weight: 750 !important;
    color: #173b70 !important;
    margin-bottom: 5px !important;
}

.app-subtitle {
    color: #64748b !important;
    font-size: 14px !important;
}

.status-badge {
    background: #dcfce7;
    color: #166534;
    padding: 7px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    display: inline-block;
}

/* Sidebar */
.sidebar-panel {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 16px !important;
}

.sidebar-heading {
    font-size: 16px !important;
    font-weight: 700 !important;
    color: #1e3a5f !important;
    margin-bottom: 12px !important;
}

.question-button {
    text-align: left !important;
    white-space: normal !important;
    border: 1px solid #e2e8f0 !important;
    background: white !important;
    border-radius: 10px !important;
    margin-bottom: 7px !important;
    transition: all 0.2s ease;
}

.question-button:hover {
    border-color: #93c5fd !important;
    background: #eff6ff !important;
}

/* Main chat panel */
.chat-panel {
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 12px !important;
    background: white;
}

/* Chat messages */
.message {
    font-size: 14px !important;
    line-height: 1.7 !important;
}

/* Input area */
.input-panel {
    border: 1px solid #dbeafe;
    border-radius: 14px;
    padding: 10px !important;
    background: #ffffff;
    margin-top: 10px;
}

/* Buttons */
.send-button {
    min-width: 100px !important;
    font-weight: 600 !important;
}

.clear-button {
    color: #64748b !important;
}

/* Footer */
.app-footer {
    text-align: center;
    color: #94a3b8;
    font-size: 12px;
    padding: 14px;
}

/* Responsive layout */
@media (max-width: 768px) {
    .app-title {
        font-size: 22px !important;
    }

    .app-header {
        padding: 16px;
    }
}
"""


# ---------------------------------------------------------
# Agent integration
# ---------------------------------------------------------

def format_response(user_query: str) -> str:
    """Run the existing agent and format its answer with sources."""

    try:
        agent = InsurancePolicyAgent()
        result = agent.run(user_query)

        answer = result.get("answer", "No response generated.")

        tool_results = result.get("tool_results", [])
        sources = []

        for tool_result in tool_results:
            if not isinstance(tool_result, dict):
                continue

            if not tool_result.get("success"):
                continue

            result_data = tool_result.get("result", {})

            if not isinstance(result_data, dict):
                continue

            evidence = result_data.get("evidence_metadata", {})

            if not isinstance(evidence, dict):
                continue

            if not evidence.get("has_evidence"):
                continue

            for source in evidence.get("sources", []):
                if not isinstance(source, dict):
                    continue

                policy_id = source.get("policy_id", "unknown")
                field = source.get("field", "unknown")
                value = (
                    source.get("display_value")
                    or source.get("value")
                    or "Not specified"
                )

                source_line = (
                    f"- **{policy_id}** · `{field}`: {value}"
                )

                if source_line not in sources:
                    sources.append(source_line)

        if sources:
            answer += "\n\n---\n\n### 📚 Supporting evidence\n\n"
            answer += "\n".join(sources)

        return answer

    except ValueError as exc:
        if "OPENROUTER_API_KEY" in str(exc):
            return (
                "### Configuration error\n\n"
                "The OpenRouter API key is missing or incorrectly configured. "
                "Please check your environment configuration."
            )

        return f"### Error\n\n{exc}"

    except Exception:
        # Avoid exposing internal exceptions or configuration secrets.
        return (
            "### Something went wrong\n\n"
            "The agent could not process this question. "
            "Please try again or check the application logs."
        )


def respond(message: str, history: list):
    """Process a chat message and update the conversation."""

    history = list(history or [])

    if not message or not message.strip():
        return history, ""

    history.append({
        "role": "user",
        "content": message.strip(),
    })

    answer = format_response(message.strip())

    history.append({
        "role": "assistant",
        "content": answer,
    })

    return history, ""


def fill_question(question: str):
    """Populate the input box with an example question."""
    return question


# ---------------------------------------------------------
# Example questions
# ---------------------------------------------------------

EXAMPLE_QUESTIONS = [
    (
        "🔎 Search policies",
        "Find domestic trade credit insurance policies",
    ),
    (
        "⚖️ Compare policies",
        "Compare policies TCI-DOM-001 and TCI-DOM-002",
    ),
    (
        "✅ Check eligibility",
        (
            "Check eligibility for TCI-DOM-001. "
            "I have annual turnover of 15 million, "
            "business is 3 years old, and I have financial statements."
        ),
    ),
    (
        "🛡️ Coverage and exclusions",
        "What are the coverage and exclusions of TCI-DOM-001?",
    ),
    (
        "❓ Unsupported question",
        "What's the weather today?",
    ),
]


# ---------------------------------------------------------
# Build the UI
# ---------------------------------------------------------

def main():

    theme = gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="slate",
        neutral_hue="slate",
        radius_size="lg",
        spacing_size="md",
    )

    with gr.Blocks(
        title="Insurance Policy Intelligence",
    ) as demo:

        # Header
        with gr.Row(elem_classes=["app-header"]):

            with gr.Column(scale=5):
                gr.Markdown(
                    "# 🛡️ Insurance Policy Intelligence",
                    elem_classes=["app-title"],
                )

                gr.Markdown(
                    "Search policies · Compare coverage · Check eligibility",
                    elem_classes=["app-subtitle"],
                )

            with gr.Column(scale=1, min_width=150):
                gr.Markdown(
                    '<div style="text-align:right">'
                    '<span class="status-badge">'
                    "● Agent Interface"
                    "</span></div>"
                )

        # Main layout
        with gr.Row(equal_height=False):

            # Sidebar
            with gr.Column(
                scale=1,
                min_width=260,
                elem_classes=["sidebar-panel"],
            ):

                gr.Markdown(
                    "### 💡 Example questions",
                    elem_classes=["sidebar-heading"],
                )

                question_buttons = []

                for label, question in EXAMPLE_QUESTIONS:
                    button = gr.Button(
                        label,
                        variant="secondary",
                        elem_classes=["question-button"],
                    )
                    question_buttons.append((button, question))

                gr.Markdown("---")

                gr.Markdown(
                    "### ⚙️ Available capabilities"
                )

                gr.Markdown(
                    """
                    **🔎 Policy search**

                    Find relevant insurance policies.

                    **⚖️ Policy comparison**

                    Compare premiums, coverage, exclusions and eligibility.

                    **✅ Eligibility checks**

                    Evaluate applicants against supported rules.

                    **📚 Evidence-based answers**

                    Trace available answers to policy data.
                    """
                )

            # Conversation area
            with gr.Column(
                scale=3,
                elem_classes=["chat-panel"],
            ):

                chatbot = gr.Chatbot(
                    value=[
                        {
                            "role": "assistant",
                            "content": (
                                "## Welcome!\n\n"
                                "I'm your Insurance Policy Intelligence assistant. "
                                "I can help you search policies, compare options, "
                                "and evaluate eligibility using the available "
                                "insurance data.\n\n"
                                "**Try an example from the sidebar to get started.**"
                            ),
                        }
                    ],
                    height=540,
                    show_label=False,
                    elem_classes=["message"],
                )

                # Message input
                with gr.Row(elem_classes=["input-panel"]):

                    message_input = gr.Textbox(
                        placeholder=(
                            "Ask about insurance policies, coverage, "
                            "premiums or eligibility..."
                        ),
                        show_label=False,
                        lines=2,
                        max_lines=5,
                        scale=5,
                        container=False,
                    )

                    send_button = gr.Button(
                        "➤ Send",
                        variant="primary",
                        scale=1,
                        min_width=90,
                        elem_classes=["send-button"],
                    )

                with gr.Row():
                    clear_button = gr.Button(
                        "🗑️ Clear conversation",
                        variant="secondary",
                        elem_classes=["clear-button"],
                    )

        gr.Markdown(
            "Powered by LangGraph + MCP · Insurance information "
            "is limited to the available policy catalogue.",
            elem_classes=["app-footer"],
        )

        # Send by clicking the button or pressing Enter.
        send_button.click(
            fn=respond,
            inputs=[message_input, chatbot],
            outputs=[chatbot, message_input],
        )

        message_input.submit(
            fn=respond,
            inputs=[message_input, chatbot],
            outputs=[chatbot, message_input],
        )

        # Example buttons populate the input field.
        for button, question in question_buttons:
            button.click(
                fn=fill_question,
                inputs=gr.State(question),
                outputs=message_input,
            )

        # Reset the conversation.
        clear_button.click(
            fn=lambda: ([], ""),
            inputs=None,
            outputs=[chatbot, message_input],
        )

    # Launch
    demo.launch(
        server_name=SERVER_NAME,
        server_port=SERVER_PORT,
        share=SHARE,
        show_error=True,
        theme=theme,
        css=CUSTOM_CSS,
    )


if __name__ == "__main__":
    main()