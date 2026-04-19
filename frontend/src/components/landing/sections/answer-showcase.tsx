import { AnimatedNumber } from "@/components/landing/animated-number";
import { answerBlocks, chartBars } from "@/components/landing/landing-content";
import {
  ChartLineUp,
  CheckCircle,
  FileText,
  Rows,
  Table,
  Warning,
} from "@phosphor-icons/react/dist/ssr";
import type { ReactNode } from "react";

export function AnswerShowcase() {
  return (
    <section
      id="evidence"
      className="section-depth relative overflow-hidden border-b border-[#ddd2c4]/80 bg-[#fffaf7] py-28 sm:py-36 lg:py-44"
    >
      <div className="mx-auto max-w-[1440px] px-4 sm:px-6 lg:px-8">
        <div className="grid gap-12 lg:grid-cols-[0.78fr_1.22fr] lg:gap-20">
          <div className="lg:pt-10">
            <h2 className="display-ink max-w-3xl text-balance text-4xl font-semibold leading-[0.95] tracking-[-0.06em] text-[#241f1a] sm:text-6xl">
              Answers you can inspect before you trust
            </h2>
            <p className="mt-6 max-w-[60ch] text-lg leading-8 text-[#655c52]">
              Sherlock gives the conclusion and the supporting context together, so a user
              can read the answer, check the rows, and see quality caveats in the same place.
            </p>
            <div className="mt-12 grid grid-flow-dense gap-4 sm:grid-cols-2">
              {answerBlocks.map((block) => (
                <article
                  key={block.title}
                  className="group border-t border-[#d6c9bb] pt-5 transition-colors duration-300 hover:border-[#c98146]/45"
                >
                  <p className="font-mono text-xs text-[#8f6a4e]">{block.value}</p>
                  <h3 className="mt-3 text-2xl font-semibold tracking-[-0.045em] text-[#241f1a] transition-transform duration-300 group-hover:translate-x-1">
                    {block.title}
                  </h3>
                  <p className="mt-3 text-sm leading-6 text-[#655c52]">{block.body}</p>
                </article>
              ))}
            </div>
          </div>

          <div className="grid grid-flow-dense gap-4 lg:grid-cols-12">
            <div className="premium-surface border-beam lift-card border border-[#d8cbbb] bg-[#f7f3ec] p-5 lg:col-span-7">
              <div className="flex items-center gap-3">
                <span className="grid size-10 place-items-center bg-[#241f1a] text-[#fffaf7]">
                  <FileText size={20} weight="duotone" />
                </span>
                <div>
                  <p className="font-mono text-xs text-[#8f6a4e]">finding</p>
                  <h3 className="text-2xl font-semibold tracking-[-0.05em]">
                    March had the strongest quarter signal.
                  </h3>
                </div>
              </div>
              <p className="mt-5 text-base leading-7 text-[#655c52]">
                Revenue rose from January through March, with a softer April. The answer
                includes a quality note because missing values exist in the uploaded file.
              </p>
              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                <MetricCard icon={<Rows size={20} />} value="11,750" label="usable rows" />
                <MetricCard icon={<Warning size={20} />} value="341" label="missing values" />
              </div>
            </div>

            <div className="premium-dark-surface border-beam lift-card border border-[#d8cbbb] bg-[#241f1a] p-5 text-[#fffaf7] lg:col-span-5">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <p className="font-mono text-xs text-[#dfb48e]">quality note</p>
                  <h3 className="mt-1 text-2xl font-semibold tracking-[-0.05em]">
                    Caveats stay visible
                  </h3>
                </div>
                <Warning size={24} className="text-[#c98146]" />
              </div>
              <p className="text-sm leading-6 text-[#d9cdc0]">
                Messy spreadsheets can still be useful. Sherlock keeps the caveat visible
                so the answer does not overstate confidence.
              </p>
            </div>

            <div className="premium-surface border-beam lift-card border border-[#d8cbbb] bg-[#f7f3ec] p-5 lg:col-span-7">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <p className="font-mono text-xs text-[#8f6a4e]">chart</p>
                  <h3 className="mt-1 text-2xl font-semibold tracking-[-0.05em]">
                    Revenue trend
                  </h3>
                </div>
                <ChartLineUp size={24} className="text-[#9d5728]" />
              </div>
              <div className="flex h-52 items-end gap-3 border-b border-l border-[#cabdac] px-3">
                {chartBars.map((bar, index) => (
                  <div key={bar.label} className="flex h-full flex-1 flex-col justify-end gap-2">
                    <div
                      className="bar-rise min-h-5 bg-[#9d5728] shadow-[inset_0_1px_0_rgba(255,255,255,0.35)] transition-transform duration-500 hover:scale-y-105"
                      style={{ height: bar.height, animationDelay: `${index * 80}ms` }}
                    />
                    <span className="pb-2 text-center font-mono text-[10px] text-[#756a60]">
                      {bar.label}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="premium-surface lift-card border border-[#d8cbbb] bg-[#f7f3ec] p-5 lg:col-span-5">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <p className="font-mono text-xs text-[#8f6a4e]">table</p>
                  <h3 className="mt-1 text-2xl font-semibold tracking-[-0.05em]">
                    Evidence rows
                  </h3>
                </div>
                <Table size={24} className="text-[#9d5728]" />
              </div>
              <div className="divide-y divide-[#ddd2c4] border-y border-[#ddd2c4] font-mono text-xs">
                {["North  $42,810", "West   $47,235", "South  $51,904"].map((row) => (
                  <div
                    key={row}
                    className="flex items-center justify-between py-3 transition-colors duration-300 hover:bg-[#fffaf7]"
                  >
                    <span>{row}</span>
                    <CheckCircle size={15} className="text-[#7f421d]" />
                  </div>
                ))}
              </div>
              <p className="mt-5 text-sm leading-6 text-[#655c52]">
                Supporting rows stay close to the claim, making the answer easier to check.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

type MetricCardProps = {
  icon: ReactNode;
  label: string;
  value: string;
};

function MetricCard({ icon, label, value }: MetricCardProps) {
  const numericValue = Number(value.replace(/,/g, ""));

  return (
    <div className="lift-card border border-[#d8cbbb] bg-[#fffaf7] p-4">
      <div className="text-[#9d5728]">{icon}</div>
      <p className="mt-5 font-mono text-3xl tracking-[-0.055em] text-[#241f1a]">
        {Number.isFinite(numericValue) ? <AnimatedNumber value={numericValue} /> : value}
      </p>
      <p className="mt-1 text-sm text-[#756a60]">{label}</p>
    </div>
  );
}
