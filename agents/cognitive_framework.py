"""Hardcoded cognitive rules injected into every expert agent's system prompt.

These rules are never generated or modified by any LLM.  The backend
orchestrator appends them programmatically after the Recruiter returns
each agent's base_persona.
"""

from __future__ import annotations

COGNITIVE_FRAMEWORK_RULES: str = (
    "CRITICAL RULE: You MUST identify at least one logical flaw, unstated "
    "assumption, or potential risk in the previous message before adding your "
    "own analysis. Polite agreement without substantive critique is strictly "
    "forbidden. Your value comes from rigorous, independent thinking — not "
    "from consensus. Always explain *why* you disagree or what edge-case the "
    "prior speaker overlooked."
)


def build_system_prompt(base_persona: str) -> str:
    """Combine Recruiter-generated persona with hardcoded cognitive rules."""
    return f"{base_persona}\n\n{COGNITIVE_FRAMEWORK_RULES}"
