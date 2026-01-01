# app.py
import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

# CrewAI imports
from crewai import Agent, Task, Crew

# ----------------------------
# Setup / Config
# ----------------------------
st.set_page_config(page_title="Insurance Letter Generator", layout="wide")

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    st.warning("Missing OPENAI_API_KEY. Set it in your environment or .env file.")

# Some CrewAI versions use env var OPENAI_API_KEY directly.
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


def load_canonical_instructions(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Canonical instruction file not found: {p.resolve()}")
    return p.read_text(encoding="utf-8")


# ----------------------------
# UI
# ----------------------------
st.title("📄 Insurance Letter Generator (CrewAI)")
st.caption("Uses your canonical instruction set + 3 agents (Generator → Formatter → Compliance).")

with st.sidebar:
    st.header("Settings")
    model_name = st.text_input("Model", value=DEFAULT_MODEL)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.05)

    st.markdown("---")
    st.subheader("Canonical Instructions")
    instr_path = st.text_input(
        "Path to canonical .txt",
        value="canonical_insurance_letter_instructions.txt",
        help="Example: canonical_insurance_letter_instructions_20251228_074512.txt",
    )

    show_instructions = st.checkbox("Preview canonical instructions", value=False)

col1, col2 = st.columns(2)

with col1:
    letter_type = st.selectbox(
        "Letter Type",
        ["Coverage Decision", "Denial Letter", "Request for Additional Information"],
        index=1,
    )
    company_name = st.text_input("Company Name", value="Cascade Assurance")
    insured_name = st.text_input("Insured Name", value="Ananya Brown")

with col2:
    policy_number = st.text_input("Policy Number", value="P-4903497")
    claim_number = st.text_input("Claim Number", value="C-8627060")
    contact_phone = st.text_input("Claims Dept Phone (optional)", value="1-800-555-1234")
    response_deadline_days = st.number_input("Response Deadline (days)", min_value=1, max_value=90, value=30)

st.markdown("---")
custom_notes = st.text_area(
    "Optional Notes / Context (will be included as additional instructions)",
    value="",
    placeholder="Example: Include deductible mention. Keep tone empathetic but firm.",
    height=120,
)

run_btn = st.button("🚀 Generate Letter", type="primary")


# ----------------------------
# Crew Builder
# ----------------------------
@st.cache_resource(show_spinner=False)
def build_agents(model: str, temp: float):
    """
    Build agents once per model/temp combo.
    """
    generator = Agent(
        role="Insurance Letter Generator",
        goal="Generate a complete insurance letter using canonical instructions and provided inputs.",
        backstory=(
            "You are a senior insurance correspondence specialist. "
            "You strictly follow the canonical instruction set and produce clear, complete letters."
        ),
        llm=model,
        verbose=True,
    )

    formatter = Agent(
        role="Insurance Letter Formatter",
        goal="Ensure the letter is cleanly formatted with consistent headings, spacing, and sections.",
        backstory=(
            "You are an expert in professional insurance document formatting. "
            "You preserve content but improve structure and readability."
        ),
        llm=model,
        verbose=True,
    )

    compliance = Agent(
        role="Insurance Compliance Reviewer",
        goal="Ensure the letter includes required compliance/regulatory language and correct references.",
        backstory=(
            "You are an insurance compliance officer. "
            "You check for regulatory notice, appeal rights, timelines, and that identifiers are present."
        ),
        llm=model,
        verbose=True,
    )

    return generator, formatter, compliance


def build_crew(canonical_instructions: str, model: str, temp: float):
    # NOTE: temperature is managed by your LLM configuration; CrewAI 'llm' accepts model string in many setups.
    # If your CrewAI version supports passing an LLM object, you can wire temperature there.
    generator_agent, formatter_agent, compliance_agent = build_agents(model, temp)

    generate_task = Task(
        description=(
            "You MUST follow the canonical instruction set below.\n\n"
            "CANONICAL INSTRUCTIONS:\n"
            f"{canonical_instructions}\n\n"
            "INPUTS:\n"
            "- Letter Type: {letter_type}\n"
            "- Company Name: {company_name}\n"
            "- Insured Name: {insured_name}\n"
            "- Policy Number: {policy_number}\n"
            "- Claim Number: {claim_number}\n"
            "- Claims Dept Phone: {contact_phone}\n"
            "- Response Deadline (days): {response_deadline_days}\n"
            "- Additional Notes: {custom_notes}\n\n"
            "TASK:\n"
            "Generate a complete insurance letter with required sections, placeholders resolved, "
            "and type-specific content. Include compliance/regulatory notice per canonical instructions."
        ),
        expected_output="A complete insurance letter draft (raw draft).",
        agent=generator_agent,
    )

    format_task = Task(
        description=(
            "Take the previous draft and format it professionally.\n"
            "Requirements:\n"
            "- Clear header block (company/address/date if required)\n"
            "- Subject line\n"
            "- Section headings and separators\n"
            "- Consistent spacing\n"
            "- Keep all content; do not remove compliance language.\n"
            "Return the formatted letter only."
        ),
        expected_output="A professionally formatted insurance letter.",
        agent=formatter_agent,
    )

    compliance_task = Task(
        description=(
            "Review the formatted letter for compliance.\n"
            "Checklist:\n"
            "- Company name, policy number, claim number present\n"
            "- Correct letter type cues present\n"
            "- Compliance/regulatory notice present\n"
            "- Appeal/reconsideration language present when applicable\n"
            f"- Mentions response deadline of { { 'response_deadline_days' } } days and contact phone\n\n"
            "If anything is missing or weak, add/strengthen it while staying professional.\n"
            "Return ONLY the final compliant letter."
        ),
        expected_output="A final compliant insurance letter.",
        agent=compliance_agent,
    )

    return Crew(
        agents=[generator_agent, formatter_agent, compliance_agent],
        tasks=[generate_task, format_task, compliance_task],
        verbose=True,
    )


# ----------------------------
# Preview Canonical Instructions
# ----------------------------
if show_instructions:
    try:
        canon = load_canonical_instructions(instr_path)
        st.subheader("Canonical Instructions Preview")
        st.code(canon[:6000] + ("\n...\n" if len(canon) > 6000 else ""), language="text")
    except Exception as e:
        st.error(str(e))


# ----------------------------
# Run
# ----------------------------
if run_btn:
    try:
        canonical = load_canonical_instructions(instr_path)
    except Exception as e:
        st.error(f"Could not load canonical instructions: {e}")
        st.stop()

    inputs = {
        "letter_type": letter_type,
        "company_name": company_name,
        "insured_name": insured_name,
        "policy_number": policy_number,
        "claim_number": claim_number,
        "contact_phone": contact_phone.strip() or "N/A",
        "response_deadline_days": int(response_deadline_days),
        "custom_notes": custom_notes.strip() or "None",
    }

    with st.spinner("Running CrewAI agents (Generator → Formatter → Compliance)..."):
        crew = build_crew(canonical, model_name, temperature)
        result = crew.kickoff(inputs=inputs)

    st.success("Done!")
    st.subheader("✅ Final Letter")
    st.text_area("Final Output", value=str(result), height=500)

    # Download button
    st.download_button(
        "⬇️ Download letter as .txt",
        data=str(result).encode("utf-8"),
        file_name=f"{letter_type.replace(' ', '_').lower()}_{policy_number}_{claim_number}.txt",
        mime="text/plain",
    )

st.markdown("---")
