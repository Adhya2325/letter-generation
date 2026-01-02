📨 Insurance Letter Generator (CrewAI + Canonical Instructions)

This project generates professional, compliant insurance letters using a canonical instruction set distilled from real insurance correspondence.
It uses CrewAI with multiple specialized agents and a Streamlit UI for interactive use.

✨ Features

Canonical Instruction–Driven
Uses a single, deduplicated instruction set covering:
Coverage Decision letters
Denial letters
Requests for Additional Information

Multi-Agent Architecture (CrewAI)
Letter Generator Agent – drafts the letter using canonical instructions
Formatter Agent – ensures professional structure and layout
Compliance Agent – validates regulatory language, identifiers, and rights

Streamlit Web App

Simple UI for entering policy details
One-click letter generation
Download final letter as .txt

LLM-agnostic

Works with OpenAI models (default: gpt-4o-mini)
Easy to swap models via environment variables

🔐 Environment Setup

Create a .env file:
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
CrewAI reads OPENAI_API_KEY directly from environment variables.

📦 Installation
pip install streamlit crewai crewai-tools openai python-dotenv
▶️ Running the App
streamlit run app.py
Then open the browser at:
http://localhost:8501

🧾 Inputs

The UI collects:

Letter Type
Coverage Decision
Denial Letter
Request for Additional Information
Company Name
Insured Name
Policy Number
Claim Number
Claims Department Phone (optional)
Response Deadline (days)
Optional contextual notes

📤 Output

A fully drafted insurance letter
Professionally formatted

Includes:

Subject line
Claim references
Compliance and regulatory notices
Appeal / reconsideration language when applicable
Downloadable as a .txt file
