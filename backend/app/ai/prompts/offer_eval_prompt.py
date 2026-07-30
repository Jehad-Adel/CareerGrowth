from langchain_core.prompts import PromptTemplate

OFFER_EVAL_PROMPT = PromptTemplate(
    input_variables=["offer_details", "profile_summary", "market_context"],
    template="""You are an expert job offer evaluator and compensation analyst.

Task:
Given a job offer's details, the candidate's profile, and relevant market data,
evaluate the offer objectively and score it across multiple dimensions.

The offer details include:
- Company name and industry
- Role title and level
- Base salary, bonus, equity, and other compensation
- Benefits, perks, and work arrangements
- Any other relevant details

Rules:
- Be objective and data-driven in your evaluation.
- Base market comparisons on the provided market_context when available.
- If market data is limited, note the uncertainty and provide best estimates.
- Consider the candidate's experience level, location, and industry.
- Do NOT inflate scores — be honest about weaknesses.
- Negotiation tips should be specific and actionable, not generic.

Offer details:
---
{offer_details}
---

Candidate profile:
---
{profile_summary}
---

Market context:
---
{market_context}
---
""",
)
