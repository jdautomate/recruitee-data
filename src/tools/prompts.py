from src.utils.server_config import mcp



PRINT_CANDIDATE_DETAILS = """
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

### NOTES COUNT:
Show `candidate.notes_count` as “Internal notes: X”.

---

**Formatting rules**

* Use simple bullets (`*`) for lists, one item per line.  
* Do **not** include any JSON, brackets, or quotes in the final output.  
* Do **not** output sections that end up empty.  
"""


@mcp.tool()
def candidate_details_prompt() -> str:
    """Return the prompt used to format candidate details."""
    return PRINT_CANDIDATE_DETAILS