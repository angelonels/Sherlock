import { heroProof } from "@/components/landing/landing-content";
import { InsightTicker } from "@/components/landing/insight-ticker";
import { MagneticButton } from "@/components/landing/magnetic-button";
import { InvestigationVisual } from "@/components/landing/visuals/investigation-visual";
import Link from "next/link";

export function HeroSection() {
  return (
    <section id="product" className="hero-vignette relative border-b border-[#ddd2c4]/80">
      <div className="mx-auto grid max-w-[1440px] min-w-0 lg:min-h-[calc(100dvh-4rem)] lg:grid-cols-[minmax(0,0.98fr)_minmax(0,1.02fr)] xl:grid-cols-[minmax(0,0.88fr)_minmax(0,1.12fr)]">
        <div className="relative flex min-w-0 flex-col justify-center overflow-hidden px-4 py-16 sm:px-6 sm:py-20 lg:px-8 lg:py-24">
          <div className="w-full min-w-0 max-w-[720px]">
            <h1 className="display-ink reveal-up max-w-full text-balance text-[clamp(3rem,14vw,6rem)] font-semibold leading-[0.9] tracking-[-0.075em] text-[#241f1a] lg:text-[clamp(3.8rem,5vw,5rem)] xl:text-[clamp(4.8rem,5.2vw,6rem)]">
              Investigate spreadsheets with evidence
            </h1>
            <p
              className="quiet-rule reveal-up mt-8 max-w-full text-lg leading-8 text-[#655c52] sm:max-w-[61ch] sm:text-xl"
              style={{ animationDelay: "90ms" }}
            >
              Upload CSV or Excel data, ask questions, and get findings with charts,
              tables, KPI cards, and data-quality warnings.
            </p>
            <div
              className="reveal-up mt-10 flex w-full min-w-0 flex-col gap-3 sm:w-auto sm:flex-row"
              style={{ animationDelay: "180ms" }}
            >
              <MagneticButton href="/sign-up">Start an investigation</MagneticButton>
              <Link
                href="#workflow"
                className="inline-flex h-12 w-full max-w-full items-center justify-center border border-[#d9cdbf] bg-[#fffaf7] px-5 text-sm font-semibold tracking-[-0.01em] text-[#2b2520] shadow-[0_18px_45px_-34px_rgba(70,47,30,0.7)] transition-all duration-300 hover:-translate-y-0.5 hover:border-[#9d5728] hover:bg-[#fffdf9] hover:text-[#7f421d] hover:shadow-[0_22px_55px_-38px_rgba(70,47,30,0.95)] focus-visible:ring-3 focus-visible:ring-[#b56b32]/25 focus-visible:outline-none active:translate-y-px sm:w-auto"
              >
                See how it works
              </Link>
            </div>
            <InsightTicker />
          </div>

          <div
            className="reveal-up mt-14 grid w-full min-w-0 max-w-2xl grid-cols-1 border-y border-[#ddd2c4] sm:grid-cols-3"
            style={{ animationDelay: "270ms" }}
          >
            {heroProof.map((fact) => (
              <div
                key={fact.label}
                className="group border-b border-[#ddd2c4] py-5 pr-5 transition-colors duration-300 last:border-b-0 hover:bg-[#fffaf7]/58 sm:border-b-0 sm:border-r sm:last:border-r-0"
              >
                <p className="font-mono text-2xl tracking-[-0.04em] text-[#241f1a] transition-transform duration-300 group-hover:translate-x-1">
                  {fact.value}
                </p>
                <p className="mt-2 max-w-32 text-sm leading-5 text-[#756a60]">{fact.label}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="relative border-t border-[#ddd2c4]/80 lg:border-l lg:border-t-0">
          <InvestigationVisual />
        </div>
      </div>
    </section>
  );
}
