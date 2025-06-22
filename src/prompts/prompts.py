from textwrap import dedent
from pathlib import Path

from src.utils.server_config import mcp



@mcp.tool()
def candidate_details_prompt() -> str:
    """Return the prompt used to format candidate details."""
    return dedent("""
    Use get_candidate tool to get full candidate data.
    You receive a single JSON payload with two top-level keys:  

    * `candidate` – personal and application data  
    * `references` – array that may include the related job offer, pipeline stages, etc.  

    Your task is to extract the most relevant information and present it in **plain text** (no markdown, no code fences).  
    Structure the output into the following sections, using exactly the headings shown (uppercase, followed by a colon).  
    Omit any heading if none of its fields are available.

    ---

    ### GENERAL DETAILS:
    * **Full name:** `<candidate.name>`
    * **Tags:** comma-separated list from `candidate.tags`
    * **CV:** `<candidate.cv_url>` (if available)
    * **Created at:** `<candidate.created_at>` (ISO date)

    ### CONTACT:
    * **Primary email:** first item in `candidate.emails`
    * **Primary phone:** first item in `candidate.phones`
    * **Location:**  
      * From `references` → first object of type `"Offer"` → `location`  
      * If absent, fall back to `candidate.fields.kind=="address"` → first `values[0].text`

    ### APPLICATION INFO:
    * **Position applied for:** `references` object of type `"Offer"` → `title`
    * **Department:** same object → `department`
    * **Current stage:**  
      * In `candidate.placements[0]` → use matching `stage_id` to find stage name in `references` array
    * **Placement status:**  
      * If `candidate.placements[0].disqualified_at` is non-null, show **Disqualified** and quote `disqualify_reason`  
      * Else if `candidate.is_hired` is true, show **Hired**  
      * Else show **Active**

    ### SKILLS & LANGUAGES:
    * **Languages:** list `language_name (level)` from field `kind=="language_skill"`
    * **Skills:** list up to 8 unique entries from field `kind=="skills"`; omit duplicates

    ### SALARY EXPECTATION:
    * If a field named “Salary expectation” exists (`kind=="single_line"` and `name` matches, case-insensitive), print its first value.

    ### COVER LETTER (FIRST 2 LINES):
    Print only the first two newline-separated lines of `candidate.cover_letter` (trim whitespace). Omit if not present.

    ### NOTES:
    Show candidate notes as “Internal notes: X”.

    ---

    **Formatting rules**
    Use markdown formatting. 
    """)


@mcp.tool()
def instructions() -> str:
    """Return the general guidelines for the whole Recruitee MCP server. Should be loaded before using any other tools."""
    return dedent("""
        Don't calculate statistics on your own if they can be fetched from metric tools. 
    """)


@mcp.tool()
def recruitment_report_prompt() -> str:
    """Return the prompt with instructions and a template for a recruitment report."""
    path = Path(__file__).parent / "report.md"
    return path.read_text(encoding="utf-8")
