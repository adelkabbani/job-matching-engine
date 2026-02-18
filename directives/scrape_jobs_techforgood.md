# Directive: Scrape Tech Jobs for Good

## Goal
Extract job listings from `techjobsforgood.com` related to software engineering.

## Inputs
- `keywords`: (e.g., "Software Engineer", "Frontend")
- `output_file`: Path to save the extracted data.

## Tools/Scripts
- `execution/scrape_techforgood.py`: Scraper script.

## Outputs
- JSON file containing:
  - `title`
  - `company`
  - `location`
  - `link`
  - `tags`

## Instructions
1. Run `execution/scrape_techforgood.py` with the provided keywords.
2. If the script fails, check the site structure and update the script.
3. Validate the output JSON format.
