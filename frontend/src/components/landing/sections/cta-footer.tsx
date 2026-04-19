import { MagneticButton } from "@/components/landing/magnetic-button";
import Link from "next/link";

export function CtaFooter() {
  const marqueeItems = [
    "CSV/XLSX uploads",
    "Evidence tables",
    "KPI cards",
    "Quality notes",
    "Charts",
    "Suggested follow-up questions",
  ];

  return (
    <footer className="relative overflow-hidden bg-[#241f1a] text-[#fffaf7]">
      <div
        className="absolute inset-0 bg-[radial-gradient(circle_at_16%_18%,rgba(201,129,70,0.18),transparent_28rem),radial-gradient(circle_at_86%_60%,rgba(255,250,247,0.08),transparent_26rem)]"
        aria-hidden="true"
      />
      <div
        className="relative hidden overflow-hidden border-b border-[#4b4037] py-3 sm:block"
        aria-hidden="true"
      >
        <div className="marquee-track">
          {[...marqueeItems, ...marqueeItems].map((item, index) => (
            <span key={`${item}-${index}`} className="marquee-item">
              {item}
            </span>
          ))}
        </div>
      </div>
      <section className="mx-auto max-w-[1440px] px-4 py-24 sm:px-6 sm:py-32 lg:px-8 lg:py-40">
        <div className="relative grid gap-12 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
          <div>
            <h2 className="max-w-5xl text-balance text-5xl font-semibold leading-[0.9] tracking-[-0.075em] sm:text-7xl lg:text-[6.5rem]">
              Open a case file on your spreadsheet
            </h2>
            <p className="mt-8 max-w-[60ch] text-lg leading-8 text-[#d9cdc0]">
              Start with one CSV or Excel file, ask a concrete question, and read the
              evidence before you act on the result.
            </p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row lg:justify-end">
            <MagneticButton href="/app">Start your investigation</MagneticButton>
            <Link
              href="/app"
              className="inline-flex h-12 items-center justify-center border border-[#665548] bg-transparent px-5 text-sm font-semibold tracking-[-0.01em] text-[#fffaf7] transition-transform hover:-translate-y-0.5 hover:border-[#c98146] hover:text-[#dfb48e] focus-visible:ring-3 focus-visible:ring-[#c98146]/25 focus-visible:outline-none active:translate-y-px"
            >
              Open app
            </Link>
          </div>
        </div>
      </section>

      <div className="border-t border-[#4b4037]">
        <div className="relative mx-auto flex max-w-[1440px] flex-col gap-4 px-4 py-6 text-sm text-[#b9aa9a] sm:px-6 md:flex-row md:items-center md:justify-between lg:px-8">
          <Link href="/" className="font-semibold tracking-[-0.02em] text-[#fffaf7]">
            Sherlock
          </Link>
          <div className="flex flex-wrap gap-x-6 gap-y-2">
            <a href="#product" className="transition-colors hover:text-[#fffaf7]">
              Product
            </a>
            <a href="#workflow" className="transition-colors hover:text-[#fffaf7]">
              Workflow
            </a>
            <a href="#evidence" className="transition-colors hover:text-[#fffaf7]">
              Evidence
            </a>
            <a href="#safety" className="transition-colors hover:text-[#fffaf7]">
              Trust
            </a>
            <Link href="/privacy" className="transition-colors hover:text-[#fffaf7]">
              Privacy
            </Link>
            <Link href="/terms" className="transition-colors hover:text-[#fffaf7]">
              Terms
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
