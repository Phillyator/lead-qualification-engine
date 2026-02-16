"""Keyword signal scanner for lead qualification."""


def scan_keywords(text: str, industry: str, config: dict) -> tuple[int, list[str], list[str]]:
    """
    Scan text for ICP signals based on config.

    Args:
        text: Lowercased combined text (name + description + keywords)
        industry: Industry string from spreadsheet
        config: Full config dict

    Returns:
        (total_points, matched_categories, flags)
    """
    kw_config = config["keyword_signals"]
    cap = kw_config.get("cap", 25)

    total = 0
    matched = []
    flags = []

    # Standard keyword categories
    for category in kw_config["categories"]:
        hits = [t for t in category["terms"] if t in text]
        if hits:
            total += category["points"]
            matched.append(category["name"])

    # Conditional signals
    for signal in config.get("conditional_signals", []):
        condition = signal["condition"]
        industry_match = condition.get("industry_contains", "")
        exclude_cat = condition.get("exclude_if_category_matched", "")

        if industry_match and industry and industry_match in industry:
            if exclude_cat and exclude_cat in matched:
                continue
            hits = [t for t in signal["terms"] if t in text]
            if hits:
                total += signal["points"]
                matched.append(signal["name"])

    # Flags & penalties
    for flag in config.get("flags", []):
        condition = flag["condition"]
        industry_match = condition.get("industry_contains", "")

        if industry_match and industry and industry_match in industry:
            hits = [t for t in flag["terms"] if t in text]
            if hits:
                total -= flag["penalty"]
                flags.append(flag["name"])

    total = min(total, cap)
    return total, matched, flags
