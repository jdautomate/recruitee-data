## General Guidelines
- Follow the template provided below to generate a recruitment report.
- Instructions for tools usage are provided in the template in `<instructions here>` format.
- Report should be generated in Markdown format. No additional text should be included outside the report.
- Ensure all metrics are formatted correctly. Don't show time in seconds, instead use days or hours, depending on value.
- The currency unit is PLN
- Use abbreviated names (e.g., "Joe D." instead of full names) for charts labels.

## Instructions for report generation
- Before generating the report ask the user for a specific recruitment and optionally a date range.
- Find the offer ID using `list_offers` tool.
- List all available metrics. Metric kind must match the tool.
- Read the template carefully and retrieve all necessary metrics.
  - Correct filters should be applied to the metrics.
  - If retrieving a metric fails, try again after checking the metric details and available options.
- Generate charts and gather URLs for charts if using MCP server for charts.
- Generate the report using the template.
- Ask the user if they want to generate a URL for the report. If yes, use the markdown_to_url tool and print the URL.

---

# <job title> Recruitment Report
Date Range: <start date> to <end date>

## Single Metrics
- Time to fill: <use `job_open_time` single metric with `include_archived_jobs: true`>
- Time to hire: <use `custom_time_based` time based metric with `end_point: "candidate_hired"`, `start_point: "candidate_applied"`, `include_archived_jobs: true`>
- Total candidates: <use `candidates` breakdown metric>
- Total hires: <use `hires` breakdown metric>
- Total interview session time: <use `time_spent_interviewing` single metric>

## Candidate Breakdown
<use `candidates` breakdown metric to get total candidates. Then get `disqualifications` breakdown metric to get a disqualified count. Then use `hires` breakdown metric to get hired count. Calculate candidates in the pipeline as: Total Candidates - Disqualified - Hired. Create a Markdown table with columns: Status, Count, Percentage, Description. Include rows for Total Candidates, Disqualified, Hired, and Still in Pipeline with appropriate calculations and status indicators>
Short analysis of the breakdown

## Disqualifications Breakdown
<use `candidates` breakdown metric to get a total candidates count. Then use `disqualifications` breakdown metric with `primary_group: "disqualify-reason"` to get detailed breakdown by reason. Calculate the total disqualified by summing all counts. Create a Markdown table with columns: Rank, Disqualification Reason, Count, % of Total, % of Disqualified. Sort data by count in descending order. Calculate % of Total as (Reason Count ÷ Total Candidates) × 100. Calculate % of Disqualified as (Reason Count ÷ Total Disqualified) × 100. Add rank numbers starting from 1 for the highest count>
Short analysis of the breakdown

## Stages Overview

### 1. Proceed Rates per Stage
<use `proceed_rate` funnel metric and group by stage-name. Present data in a table with columns: Stage, Candidates Entered, Candidates Proceeded, Proceed Rate>

### 2. Average Time Spent per Stage
<use `time_spent_in_stage` metric with `primary_group: "stage-name"`. Present data in a column chart with stages on x-axis and days on y-axis>

### 3. Drop-off Rates by Stage
<use `dropoff_rate` funnel metric with `primary_group: "stage-name"`. Create a column chart showing the percentage of candidates who don't proceed from each stage>

### 4. Cumulative Time to Reach Stages
<use `time_to_reach_stage` funnel metric with `primary_group: "stage-name"`. Create a line chart showing how long it takes from start to reach each stage>

### 5. Candidate Source Distribution
<use `candidates` breakdown metric with `primary_group: "stage"`, `secondary_group: "candidate-source-tag"`. Create a pie chart showing the number of candidates per source tag for each stage>
<use `candidates` breakdown metric with `primary_group: "stage"`, `secondary_group: "candidate-source-tag"`. Create a sankey chart where source nodes are candidate source tags and target nodes are stages, showing the flow of how many candidates from each source tag reached each stage. Use `nodeAlign="justify"` for better layout>

### Stage Performance Summary Table
| Metric        | Best Performing Stage             | Worst Performing Stage           | Average                |
|---------------|-----------------------------------|----------------------------------|------------------------|
| Proceed Rate  | <stage with highest proceed rate> | <stage with lowest proceed rate> | <average proceed rate> |
| Time Spent    | <stage with shortest time>        | <stage with longest time>        | <average time>         |
| Drop-off Rate | <stage with lowest drop-off>      | <stage with highest drop-off>    | <average drop-off>     |

### Stages Summary
Analysis of the above metrics to identify trends, bottlenecks, and areas for improvement in the recruitment process.

## Recruitment Team Breakdown
### Time to hire by hiring manager
<use `custom_time_based` time based metric with `end_point: "candidate_hired"`, `start_point: "candidate_applied"`, `primary_group: "hiring-manager"`, `include_archived_jobs: true`. Create a table with columns: Hiring Manager, Hires, Time to Hire, Total (candidates per hiring manager).>

### Time spent on interviewing by interviewer
<use `time_spent_interviewing` single metric with `primary_group: "participant"`. Sort results by time spent in descending order. Create a table with columns: Rank, Interviewer, Time Spent, % of Total. Calculate total interview time by summing all participant times. Calculate a percentage of total for each interviewer as (Individual Time ÷ Total Time) × 100. Add rank numbers starting from 1 for the highest time. Include total interview time summary.>
- Total interviewer time investment: <sum the column "Time Spent" from the table, it's different from the total interview session time metric>

### Stage per interviewer
<use `candidates` breakdown metric with `primary_group: "participant"`, `secondary_group: "stage"`. Filter out rows where a participant is `"__empty__"` or `"No Interviewer Assigned"`. Create a stacked column chart where: `stack: true` and `group: false`.>

### Hires by recruiter
<use `hires` breakdown metric with `primary_group: "recruiter"`. Create a simple Markdown table with columns: Recruiter, Hires. Sort by hire count in descending order.>

### Recruitment Team Summary
Short analysis of the recruitment team breakdown, highlighting key contributors. Do not analyze the performance.