"""Pass 2 enrichment — web search + LLM signal extraction for top leads."""

import json
import time

from ddgs import DDGS
from anthropic import Anthropic


def search_company(name: str, industry: str, config: dict) -> list[dict]:
    """Search DuckDuckGo for company signals. Returns list of {title, url, snippet}."""
    enr = config["enrichment"]
    query = enr["search_query_template"].replace("{name}", name)

    try:
        results = DDGS().text(query, max_results=enr.get("search_max_results", 5))
    except Exception as e:
        print(f"  ⚠ Search failed for '{name}': {e}")
        return []

    return [{"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")} for r in results]


EXTRACTION_PROMPT = """\
You are analyzing web search snippets about a company to extract HR and organizational signals.

Company: {company_name}
Industry: {industry}

Search results:
{snippets}

Extract the following signals from these snippets. Only extract what is clearly supported by the text — do not guess.

Return a JSON object with exactly these fields:
- "num_locations": integer or null — how many offices/sites/locations does this company have?
- "employee_sentiment": one of "positive", "negative", "neutral", "unknown" — any evidence of employee satisfaction or dissatisfaction?
- "hr_initiatives": boolean — any evidence of HR transformation, people programs, employer branding, or talent initiatives?
- "competitor_tools": list of strings — any employee engagement, survey, or feedback tools mentioned (e.g., Gallup, Qualtrics, Peakon, Culture Amp)? Empty list if none found.
- "decentralized": boolean — evidence the org is distributed, decentralized, or operates across multiple regions/cantons?
- "summary": string — 1-2 sentence summary of the most relevant enrichment findings.

Return ONLY valid JSON, no other text."""


def extract_signals(company_name: str, industry: str, search_results: list[dict], config: dict) -> dict:
    """Use Claude to extract structured signals from search snippets."""
    if not search_results:
        return _empty_signals()

    enr = config["enrichment"]
    snippets_text = "\n\n".join(
        f"[{i+1}] {r['title']}\n{r['url']}\n{r['snippet']}"
        for i, r in enumerate(search_results)
    )

    prompt = EXTRACTION_PROMPT.format(
        company_name=company_name,
        industry=industry or "Unknown",
        snippets=snippets_text,
    )

    client = Anthropic()
    try:
        response = client.messages.create(
            model=enr.get("llm_model", "claude-haiku-4-5-20251001"),
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3].strip()
        signals = json.loads(text)
    except Exception as e:
        print(f"  ⚠ LLM extraction failed for '{company_name}': {e}")
        return _empty_signals()

    # Normalize types
    signals.setdefault("num_locations", None)
    signals.setdefault("employee_sentiment", "unknown")
    signals.setdefault("hr_initiatives", False)
    signals.setdefault("competitor_tools", [])
    signals.setdefault("decentralized", False)
    signals.setdefault("summary", "")
    return signals


def _empty_signals() -> dict:
    return {
        "num_locations": None,
        "employee_sentiment": "unknown",
        "hr_initiatives": False,
        "competitor_tools": [],
        "decentralized": False,
        "summary": "No search results available.",
    }


def score_enrichment(signals: dict, config: dict) -> tuple[int, list[str]]:
    """Map extracted signals to bonus/penalty points. Returns (points, signal_names)."""
    enr = config["enrichment"]
    bonus_cap = enr.get("bonus_cap", 20)
    total = 0
    matched = []

    for rule in enr.get("bonus_rules", []):
        hit = _evaluate_rule(rule["condition"], signals)
        if hit:
            total += rule["points"]
            matched.append(rule["signal"])

    total = max(min(total, bonus_cap), -bonus_cap)
    return total, matched


def _evaluate_rule(condition: str, signals: dict) -> bool:
    """Evaluate a simple rule condition against signals."""
    if "num_locations >= " in condition:
        threshold = int(condition.split(">=")[1].strip())
        return (signals.get("num_locations") or 0) >= threshold
    if "employee_sentiment == " in condition:
        expected = condition.split("==")[1].strip()
        return signals.get("employee_sentiment") == expected
    if "hr_initiatives == true" in condition:
        return bool(signals.get("hr_initiatives"))
    if "decentralized == true" in condition:
        return bool(signals.get("decentralized"))
    if "competitor_tools is empty" in condition:
        return len(signals.get("competitor_tools", [])) == 0
    if "competitor_tools is not empty" in condition:
        return len(signals.get("competitor_tools", [])) > 0
    return False


def enrich_companies(pass1_results: list[dict], config: dict) -> list[dict]:
    """Run Pass 2 enrichment on top companies from Pass 1."""
    from .scorer import assign_tier

    enr = config["enrichment"]
    top_n = enr.get("top_n", 50)
    delay = enr.get("search_delay_seconds", 2)

    # Filter to non-disqualified, take top N by score
    eligible = [r for r in pass1_results if r["tier"] != "Disqualified"]
    eligible.sort(key=lambda x: x["total_score"], reverse=True)
    to_enrich = eligible[:top_n]
    skipped = eligible[top_n:]

    print(f"\nEnriching top {len(to_enrich)} companies (of {len(eligible)} eligible)...\n")

    enriched = []
    for i, company in enumerate(to_enrich):
        name = company["name"]
        industry = company.get("industry", "")
        print(f"[{i+1}/{len(to_enrich)}] {name}")

        # Search
        results = search_company(name, industry, config)
        print(f"  → {len(results)} search results")

        # Extract
        signals = extract_signals(name, industry, results, config)
        print(f"  → Signals: sentiment={signals['employee_sentiment']}, "
              f"locations={signals['num_locations']}, "
              f"HR={signals['hr_initiatives']}, "
              f"competitors={signals['competitor_tools']}")

        # Score
        bonus, signal_names = score_enrichment(signals, config)
        pass2_score = company["total_score"] + bonus
        pass2_tier = assign_tier(pass2_score, config)

        print(f"  → Bonus: {bonus:+d} ({', '.join(signal_names) or 'none'}) → "
              f"Pass 2 score: {pass2_score} ({pass2_tier})")

        enriched.append({
            **company,
            "enrichment_bonus": bonus,
            "enrichment_signals": signal_names,
            "enrichment_summary": signals.get("summary", ""),
            "enrichment_raw": signals,
            "search_snippets": "; ".join(r["snippet"][:100] for r in results[:3]),
            "pass2_score": pass2_score,
            "pass2_tier": pass2_tier,
        })

        if i < len(to_enrich) - 1:
            time.sleep(delay)

    # Add skipped companies (no enrichment, pass-through scores)
    for company in skipped:
        enriched.append({
            **company,
            "enrichment_bonus": 0,
            "enrichment_signals": [],
            "enrichment_summary": "Not enriched (outside top N)",
            "enrichment_raw": {},
            "search_snippets": "",
            "pass2_score": company["total_score"],
            "pass2_tier": company["tier"],
        })

    enriched.sort(key=lambda x: x["pass2_score"], reverse=True)
    return enriched
