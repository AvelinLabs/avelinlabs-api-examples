# Customer Grounding Response Examples

Every `.example.json` file in this directory is an illustrative output fixture, not a live production snapshot. Identifiers, timestamps, counts, evidence text, and error details are synthetic or placeholder values and must not be presented as observed customer results.

The file-ingestion example shows the common response shape for supported TXT, Markdown, PDF, and DOCX uploads; parser metadata varies by format. Error examples illustrate documented failure shapes without preserving raw rejected content.

Executable request fixtures are kept separately in `../requests/`, and synthetic upload inputs are in `../sample-files/`. The live OpenAPI contract is authoritative: https://api.avelinlabs.com/openapi.json.
