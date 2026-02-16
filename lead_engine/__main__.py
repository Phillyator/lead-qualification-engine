"""CLI entry point for the lead qualification engine."""

import argparse
from .config import load_config
from .scorer import read_companies, score_companies
from .writer import write_results, print_summary


def main():
    parser = argparse.ArgumentParser(description="Lead Qualification Engine — Pass 1 Scorer")
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    parser.add_argument("--input", required=True, help="Path to input xlsx workbook")
    parser.add_argument("--output", help="Path to output xlsx (defaults to modifying input file in-place)")
    args = parser.parse_args()

    config = load_config(args.config)
    output_path = args.output or args.input

    companies = read_companies(args.input, config)
    print(f"Read {len(companies)} companies from '{config['input']['sheet_name']}'")

    results = score_companies(companies, config)
    write_results(output_path, results, config)
    print_summary(results)
    print(f"\nResults written to '{config['output']['sheet_name']}' in {output_path}")


if __name__ == "__main__":
    main()
