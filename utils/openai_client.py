# utils/openai_client.py

from openai import AsyncOpenAI
import os

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROMPT = """
You are an expert ME/CFS biomedical research assistant.

Given an abstract, return structured mechanistic evidence.

Output JSON ONLY with:
- one_sentence: concise mechanistic summary
- mechanisms: list of mechanism categories (immune, metabolic, mitochondrial, vascular, neurologic, infectious, autonomic)
- biomarkers: list of biomarkers mentioned (cytokines, metabolites, cell types, imaging markers)
- confidence: 0-1
- tags: additional relevant classification tags
"""


async def generate_evidence_summary(abstract: str):
    msg = [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": abstract},
    ]

    res = await client.chat.completions.create(
        model="gpt-5",
        messages=msg,
        temperature=0.2,
        response_format={"type": "json_object"}
    )

    return res.choices[0].message.parsed
