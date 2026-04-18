export const navItems = [
  { label: "Product", href: "#product" },
  { label: "Workflow", href: "#workflow" },
  { label: "Evidence", href: "#evidence" },
  { label: "Trust", href: "#safety" },
] as const;

export const heroProof = [
  { value: "CSV/XLSX", label: "spreadsheet uploads" },
  { value: "Evidence", label: "behind every answer" },
  { value: "Quality", label: "warnings when data is messy" },
] as const;

export const workflowSteps = [
  {
    title: "Bring the spreadsheet",
    body: "Upload a CSV or Excel file and choose the sheet you want to investigate. Sherlock previews the data before you move forward.",
  },
  {
    title: "Ask the real question",
    body: "Use plain language for the questions people actually ask in reviews: what changed, what drove it, and which rows support the answer.",
  },
  {
    title: "Get the answer with proof",
    body: "Sherlock returns findings alongside charts, KPI cards, tables, notes, and suggested follow-up questions.",
  },
  {
    title: "Spot weak data early",
    body: "Missing values, duplicates, and other quality concerns stay visible so the answer does not sound more certain than the data allows.",
  },
  {
    title: "Keep the context focused",
    body: "Each investigation stays tied to the selected spreadsheet, which makes the conversation easier to trust and easier to revisit.",
  },
  {
    title: "Move from answer to next question",
    body: "Use the generated suggestions to keep exploring without rebuilding the analysis from scratch.",
  },
] as const;

export const answerBlocks = [
  {
    title: "Plain answer",
    body: "A direct explanation of what Sherlock found, written for the person making the decision.",
    value: "answer",
  },
  {
    title: "KPI cards",
    body: "Compact metrics for totals, row counts, ratios, and other values that need to stand out.",
    value: "metric",
  },
  {
    title: "Charts",
    body: "Quick visuals for trends, comparisons, and distributions when a chart makes the answer easier to read.",
    value: "chart",
  },
  {
    title: "Evidence tables",
    body: "Bounded supporting rows so you can inspect the facts behind the conclusion.",
    value: "evidence",
  },
] as const;

export const trustPrinciples = [
  {
    title: "Answers cite the dataset",
    body: "Every response is tied back to the uploaded spreadsheet instead of floating as generic advice.",
  },
  {
    title: "Quality caveats stay visible",
    body: "Sherlock surfaces missing values and duplicate rows so users know when an answer needs caution.",
  },
  {
    title: "Readable by default",
    body: "The product experience focuses on answers, charts, tables, and notes that a business user can actually scan.",
  },
  {
    title: "One investigation stays focused",
    body: "A chat follows the selected spreadsheet, keeping follow-up questions grounded in the same evidence.",
  },
] as const;

export const outcomeItems = [
  "Explain changes across months, regions, segments, and categories",
  "Turn messy spreadsheet rows into readable findings",
  "Compare performance with charts and KPI cards",
  "Review supporting rows before sharing an insight",
  "Catch data-quality issues before they become bad decisions",
  "Continue analysis with suggested follow-up questions",
] as const;

export const audienceItems = [
  {
    title: "Operators",
    body: "Review weekly exports, find variance, and understand the rows behind the movement.",
  },
  {
    title: "Founders",
    body: "Ask fast questions about revenue, pipeline, customers, and spend without waiting on a custom report.",
  },
  {
    title: "Analysts",
    body: "Use Sherlock as a focused first pass before deeper modeling or recurring reporting.",
  },
] as const;

export const sampleRows = [
  ["Jan", "North", "$42,810", "good"],
  ["Feb", "West", "$47,235", "warning"],
  ["Mar", "South", "$51,904", "good"],
  ["Apr", "East", "$49,118", "missing"],
] as const;

export const chartBars = [
  { label: "Jan", height: "42%" },
  { label: "Feb", height: "56%" },
  { label: "Mar", height: "78%" },
  { label: "Apr", height: "66%" },
  { label: "May", height: "86%" },
] as const;
