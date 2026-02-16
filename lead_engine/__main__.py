"""CLI entry point for the lead qualification engine."""

import argparse
from .config import load_config
from .scorer import read_companies, score_companies
from .writer import write_results, write_enrichment_results, print_summary, print_enrichment_summary


def main():
    parser = argparse.ArgumentParser(description="Lead Qualification Engine")
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    parser.add_argument("--input", required=True, help="Path to input xlsx workbook")
    parser.add_argument("--output", help="Path to output xlsx (defaults to modifying input file in-place)")
    parser.add_argument("--mode", choices=["pass1", "pass2"], default="pass1",
                        help="Run mode: pass1 (scoring) or pass2 (web enrichment)")
    args = parser.parse_args()

    config = load_config(args.config)
    output_path = args.output or args.input

    if args.mode == "pass1":
        companies = read_companies(args.input, config)
        print(f"Read {len(companies)} companies from '{config['input']['sheet_name']}'")

        results = score_companies(companies, config)
        write_results(output_path, results, config)
        print_summary(results)
        print(f"\nResults written to '{config['output']['sheet_name']}' in {output_path}")

    elif args.mode == "pass2":
        from .enricher import enrich_companies
        from .scorer import read_pass1_results

        pass1_results = read_pass1_results(args.input, config)
        print(f"Read {len(pass1_results)} Pass 1 results from '{config['output']['sheet_name']}'")

        enriched = enrich_companies(pass1_results, config)
        write_enrichment_results(output_path, enriched, config)
        print_enrichment_summary(enriched, config)

        enr = config.get("enrichment", {})
        rs = enr.get("region_split")
        if rs and rs.get("enabled"):
            sheets = rs.get("output_sheets", {})
            names = ", ".join(f"'{v}'" for v in sheets.values())
            print(f"\nEnrichment results written to {names} in {output_path}")
        else:
            sheet_name = enr.get("output_sheet", "Pass 2 — Enriched")
            print(f"\nEnrichment results written to '{sheet_name}' in {output_path}")


if __name__ == "__main__":
    main()
