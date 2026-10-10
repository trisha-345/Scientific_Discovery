from typing import Dict
from app.services.llm_client import call_llm_json


SYSTEM_PROMPT = """You are a research methodology expert.
Given a research hypothesis, generate a complete, rigorous experimental design.
Return ONLY a JSON object with this exact shape:

{
  "design_type": "between-subjects RCT | within-subjects | quasi-experimental | factorial | ...",
  "participants": {
    "population": "target population description",
    "sample_size": "estimated N with brief justification (power analysis)",
    "inclusion_criteria": ["criterion 1", "criterion 2"],
    "exclusion_criteria": ["criterion 1", "criterion 2"],
    "recruitment": "how to recruit participants"
  },
  "design": {
    "conditions": ["condition 1", "condition 2"],
    "randomization": "how participants are assigned",
    "blinding": "single / double / none + who is blinded",
    "duration": "total study duration (e.g. 12 weeks)"
  },
  "procedure": [
    "Step 1: ...",
    "Step 2: ...",
    "Step 3: ..."
  ],
  "variables": {
    "independent": ["IV 1 with operational definition"],
    "dependent": ["DV 1 with how measured"],
    "controls": ["control 1", "control 2"],
    "confounds_to_watch": ["confound 1"]
  },
  "instruments": [
    {"name": "instrument name", "purpose": "what it measures", "source": "where to find it"}
  ],
  "statistical_analysis": {
    "primary_test": "e.g. independent-samples t-test",
    "secondary_tests": ["test 1", "test 2"],
    "significance_level": "0.05",
    "power": "0.80",
    "effect_size_estimate": "medium (d=0.5)"
  },
  "expected_outcome": "what result would support the hypothesis",
  "null_outcome": "what result would refute it",
  "threats_to_validity": ["threat 1", "threat 2"],
  "ethical_considerations": ["IRB approval", "informed consent", "..."],
  "timeline": [
    {"phase": "Recruitment", "duration": "4 weeks"},
    {"phase": "Intervention", "duration": "8 weeks"},
    {"phase": "Data collection", "duration": "2 weeks"},
    {"phase": "Analysis", "duration": "2 weeks"}
  ]
}

Be specific. Reference the actual variables in the hypothesis.
Do not invent generic placeholders.
"""


def generate_experiment_plan(hypothesis: Dict) -> Dict:
    """Call Groq to design an experiment for the given hypothesis."""
    text = hypothesis.get("text", "")
    null_hyp = hypothesis.get("null_hypothesis") or ""
    iv = hypothesis.get("independent_var") or ""
    dv = hypothesis.get("dependent_var") or ""
    controls = hypothesis.get("control_vars") or []
    score = hypothesis.get("overall_score", 0)

    user_prompt = f"""Hypothesis:
{text}

Null hypothesis:
{null_hyp}

Independent variable:
{iv}

Dependent variable:
{dv}

Controls:
{', '.join(controls) if controls else 'none specified'}

Overall score: {score}

Design a complete, executable experiment to test this hypothesis.
Return the structured JSON only."""

    plan = call_llm_json(SYSTEM_PROMPT, user_prompt)

    # Normalize: ensure all keys exist with fallbacks
    normalized = {
        "design_type": plan.get("design_type", "unspecified"),
        "participants": plan.get("participants", {}),
        "design": plan.get("design", {}),
        "procedure": plan.get("procedure", []),
        "variables": plan.get("variables", {}),
        "instruments": plan.get("instruments", []),
        "statistical_analysis": plan.get("statistical_analysis", {}),
        "expected_outcome": plan.get("expected_outcome", ""),
        "null_outcome": plan.get("null_outcome", ""),
        "threats_to_validity": plan.get("threats_to_validity", []),
        "ethical_considerations": plan.get("ethical_considerations", []),
        "timeline": plan.get("timeline", []),
    }

    return normalized


def plan_to_markdown(plan: Dict, hypothesis_text: str) -> str:
    """Render the plan as Markdown for download."""
    p = plan
    parts = []

    parts.append(f"# Experiment Plan\n")
    parts.append(f"**Hypothesis:** {hypothesis_text}\n")
    parts.append(f"**Design type:** {p.get('design_type', 'N/A')}\n")

    parts.append("## Participants\n")
    participants = p.get("participants", {})
    if participants:
        parts.append(f"- **Population:** {participants.get('population', 'N/A')}")
        parts.append(f"- **Sample size:** {participants.get('sample_size', 'N/A')}")
        if participants.get("inclusion_criteria"):
            parts.append(f"- **Inclusion criteria:**")
            for c in participants["inclusion_criteria"]:
                parts.append(f"  - {c}")
        if participants.get("exclusion_criteria"):
            parts.append(f"- **Exclusion criteria:**")
            for c in participants["exclusion_criteria"]:
                parts.append(f"  - {c}")
        if participants.get("recruitment"):
            parts.append(f"- **Recruitment:** {participants['recruitment']}")
    parts.append("")

    parts.append("## Design\n")
    design = p.get("design", {})
    if design:
        if design.get("conditions"):
            parts.append(f"- **Conditions:** {', '.join(design['conditions'])}")
        for k in ("randomization", "blinding", "duration"):
            if design.get(k):
                parts.append(f"- **{k.capitalize()}:** {design[k]}")
    parts.append("")

    if p.get("procedure"):
        parts.append("## Procedure\n")
        for step in p["procedure"]:
            parts.append(f"1. {step}")
        parts.append("")

    variables = p.get("variables", {})
    if variables:
        parts.append("## Variables\n")
        for k in ("independent", "dependent", "controls", "confounds_to_watch"):
            if variables.get(k):
                parts.append(f"**{k.replace('_', ' ').title()}:**")
                for v in variables[k]:
                    parts.append(f"- {v}")
                parts.append("")

    if p.get("instruments"):
        parts.append("## Instruments\n")
        for inst in p["instruments"]:
            parts.append(f"- **{inst.get('name', 'Unknown')}** — {inst.get('purpose', '')} ({inst.get('source', '')})")
        parts.append("")

    stats = p.get("statistical_analysis", {})
    if stats:
        parts.append("## Statistical Analysis\n")
        for k, v in stats.items():
            parts.append(f"- **{k.replace('_', ' ').title()}:** {v}")
        parts.append("")

    if p.get("expected_outcome"):
        parts.append(f"## Expected Outcome (if H1 is true)\n\n{p['expected_outcome']}\n")
    if p.get("null_outcome"):
        parts.append(f"## Null Outcome (if H0 is true)\n\n{p['null_outcome']}\n")

    if p.get("threats_to_validity"):
        parts.append("## Threats to Validity\n")
        for t in p["threats_to_validity"]:
            parts.append(f"- {t}")
        parts.append("")

    if p.get("ethical_considerations"):
        parts.append("## Ethical Considerations\n")
        for e in p["ethical_considerations"]:
            parts.append(f"- {e}")
        parts.append("")

    if p.get("timeline"):
        parts.append("## Timeline\n")
        parts.append("| Phase | Duration |")
        parts.append("|-------|----------|")
        for t in p["timeline"]:
            parts.append(f"| {t.get('phase', '')} | {t.get('duration', '')} |")
        parts.append("")

    return "\n".join(parts)