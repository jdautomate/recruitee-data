## Instructions for report generation
- Below is a template for a recruitment report. Instructions for tools usage are provided in the template in `<instructions here>` format.
- Report should be generated in Markdown format. No additional text should be included outside the report.
- Before generating the report ask the user for a specific recruitment and optionally a date range.
- Read the template carefully and retrieve all necessary metrics. Correct filters should be applied to the metrics.
- Generate charts and gather URLs for charts if using MCP server for charts.
- Generate the report using the template.

---

# <job title> Recruitment Report
Date Range: <start date> to <end date>

## Stages Overview

### 1. Proceed Rates per Stage
<use proceed_rate metric and group by stage-name. Present data in a table with columns: Stage, Candidates Entered, Candidates Proceeded, Proceed Rate>

### 3. Average Time Spent per Stage
<use time_spent_in_stage metric and group by stage-name. Present data in bar chart with stages on x-axis and days on y-axis>

### 4. Drop-off Rates by Stage
<use dropoff_rate metric and group by stage-name. Create column chart showing percentage of candidates who don't proceed from each stage>

### 5. Cumulative Time to Reach Stages
<use time_to_reach_stage metric and group by stage-name. Create line chart showing how long it takes from start to reach each stage>

### 6. Candidate Source Distribution
<use candidates breakdown metric, group by stage as primary and candidate-source-tag as secondary. Create sankey chart where source nodes are candidate source tags and target nodes are stages, showing the flow of how many candidates from each source tag reached each specific stage. Use nodeAlign="justify" for better layout>

## Stage Performance Summary Table
| Metric | Best Performing Stage | Worst Performing Stage | Average |
|--------|----------------------|------------------------|---------|
| Proceed Rate | <stage with highest proceed rate> | <stage with lowest proceed rate> | <average proceed rate> |
| Time Spent | <stage with shortest time> | <stage with longest time> | <average time> |
| Drop-off Rate | <stage with lowest drop-off> | <stage with highest drop-off> | <average drop-off> |

## Key Insights & Recommendations
- **Bottleneck Analysis:** <identify stages with highest drop-off rates>
- **Time Efficiency:** <identify stages taking longest time>
- **Process Optimization:** <suggest improvements based on data>
- **Resource Allocation:** <recommend where to focus recruitment efforts>