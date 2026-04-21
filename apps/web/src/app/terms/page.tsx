import Link from "next/link";

export default function TermsPage() {
  return (
    <main className="min-h-[100dvh] bg-[#f7f3ec] px-4 py-16 text-[#241f1a] sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl">
        <Link href="/" className="text-sm font-semibold text-[#7f421d]">
          Back to Sherlock
        </Link>
        <h1 className="mt-10 text-5xl font-semibold leading-[0.95] tracking-[-0.06em]">
          Terms
        </h1>
        <div className="mt-8 space-y-6 text-base leading-8 text-[#655c52]">
          <p>
            Sherlock is built for CSV and XLSX spreadsheet investigations. Each conversation
            stays tied to the spreadsheet selected for that investigation so answers have a
            clear evidence source.
          </p>
          <p>
            Users are responsible for uploading files they have the right to analyze. Sherlock
            can surface data-quality warnings, but those warnings do not replace human judgment.
          </p>
          <p>
            The product presents findings, charts, tables, KPI cards, suggestions, and quality
            notes. Users should review the evidence before relying on any answer for business
            decisions.
          </p>
        </div>
      </div>
    </main>
  );
}
