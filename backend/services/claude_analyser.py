"""Claude API integration for AI-powered company analysis."""

import json
import os

ANALYSIS_PROMPT = """You are an expert agricultural industry analyst. Research the company at this URL and return a structured JSON analysis for evaluating them as a strategic partner for Stimblue+, a kelp-based biostimulant product.

Company URL: {url}

Return ONLY valid JSON with this exact structure:
{{
  "company_name": "string",
  "hq_country": "string",
  "regions": ["string"],
  "business_type": "string (e.g. 'Integrated fresh produce producer')",
  "revenue_usd": number or null,
  "revenue_year": number or null,
  "main_crops": [
    {{"crop": "string", "estimated_hectares": number, "countries": ["string"]}}
  ],
  "total_hectares_controlled": number,
  "countries_with_farms": ["string"],
  "key_decision_makers": [
    {{"name": "string", "title": "string"}}
  ],
  "sustainability": {{
    "sbti_status": "string (Committed/Target Set/Not committed/Unknown)",
    "csrd_applicable": boolean,
    "scope3_reporting": boolean,
    "key_commitments": ["string"],
    "farm_practices": ["string"],
    "biostimulant_use": {{
      "currently_using": boolean,
      "products": ["string"],
      "scale": "string",
      "openness_to_alternatives": "string (High/Medium/Low/Unknown)"
    }}
  }},
  "matrix_scores": {{
    "integration": number (0-5),
    "integration_rationale": "string",
    "high_value_crop": number (0-5),
    "high_value_crop_rationale": "string",
    "registration_ease": number (0-5),
    "registration_ease_rationale": "string",
    "scale_potential": number (0-5),
    "scale_potential_rationale": "string",
    "strategic_leverage": number (0-5),
    "strategic_leverage_rationale": "string",
    "penalty_complexity": number (-2 to 0),
    "penalty_complexity_rationale": "string"
  }}
}}

Scoring guide:
- Integration (0-5): Does the company own/control farmland? 5 = owns 10K+ ha, direct control. 0 = pure buyer/retailer.
- High-Value Crop (0-5): Are their crops high-value? 5 = berries, avocado, grapes. 1 = bulk commodity only.
- Registration Ease (0-5): Can Stimblue+ be easily registered in their operating countries? 5 = EU/developed markets. 1 = complex regulatory.
- Scale Potential (0-5): How many hectares could they treat? 5 = 50K+ ha. 1 = <1K ha.
- Strategic Leverage (0-5): Would this partnership open doors? 5 = global brand, flagship reference. 1 = small/unknown.
- Penalty Complexity (-2 to 0): Procurement complexity. 0 = simple direct. -2 = complex multi-layer.

Be thorough but realistic. If information isn't available, use your best estimate and note it."""


async def analyse_company(url: str) -> dict:
    """Call Claude API to analyse a company from its website URL."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not set. Add it to backend/.env"}

    try:
        import httpx
    except ImportError:
        return {"error": "httpx not installed. Run: pip install httpx"}

    prompt = ANALYSIS_PROMPT.format(url=url)

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}],
            },
        )

    if response.status_code != 200:
        return {"error": f"Claude API error: {response.status_code} - {response.text}"}

    data = response.json()
    content = data.get("content", [{}])[0].get("text", "")

    # Extract JSON from response
    try:
        # Try direct parse
        result = json.loads(content)
    except json.JSONDecodeError:
        # Try to find JSON block in response
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                result = json.loads(content[start:end])
            except json.JSONDecodeError:
                return {"error": "Failed to parse Claude response as JSON", "raw": content}
        else:
            return {"error": "No JSON found in Claude response", "raw": content}

    return result
