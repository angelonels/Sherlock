import Link from "next/link";

export default function PrivacyPage() {
  return (
    <main className="min-h-[100dvh] bg-[#f7f3ec] px-4 py-16 text-[#241f1a] sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl">
        <Link href="/" className="text-sm font-semibold text-[#7f421d]">
          Back to Sherlock
        </Link>
        <h1 className="mt-10 text-5xl font-semibold leading-[0.95] tracking-[-0.06em]">
          Privacy
        </h1>
        <div className="mt-8 space-y-6 text-base leading-8 text-[#655c52]">
          <p>
            Sherlock stores the information needed to run spreadsheet investigations: account
            details, uploaded data, chats, messages, and answer history.
          </p>
          <p>
            Uploaded files are used to inspect the spreadsheet, prepare it for analysis, and
            return evidence-backed answers inside the product.
          </p>
          <p>
            Product screens show readable answers, charts, tables, progress, and quality
            context so users can understand what Sherlock found.
          </p>
        </div>
      </div>
    </main>
  );
}
