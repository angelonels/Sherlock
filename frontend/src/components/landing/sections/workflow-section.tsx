import { workflowSteps } from "@/components/landing/landing-content";

export function WorkflowSection() {
  return (
    <section
      id="workflow"
      className="section-depth relative overflow-hidden border-b border-[#ddd2c4]/80 py-28 sm:py-36 lg:py-44"
    >
      <div className="mx-auto max-w-[1440px] px-4 sm:px-6 lg:px-8">
        <div className="grid gap-10 lg:grid-cols-[0.72fr_1.28fr] lg:gap-16">
          <div className="max-w-xl">
            <h2 className="display-ink text-balance text-4xl font-semibold leading-[0.95] tracking-[-0.06em] text-[#241f1a] sm:text-6xl">
              From upload to answer in one focused flow
            </h2>
            <p className="mt-6 text-lg leading-8 text-[#655c52]">
              Sherlock is designed for the common moment before a decision: someone has a
              spreadsheet, a business question, and no time to build a custom report.
            </p>
          </div>

          <div className="relative">
            <div className="absolute left-[13px] top-0 hidden h-full w-px bg-gradient-to-b from-transparent via-[#c98146]/45 to-transparent md:block" />
            <div className="grid gap-5">
              {workflowSteps.map((step, index) => (
                <article
                  key={step.title}
                  className="group grid gap-4 border-t border-[#ddd2c4] pt-5 transition-colors duration-300 hover:border-[#c98146]/45 md:grid-cols-[44px_1fr]"
                  style={{ animationDelay: `${index * 70}ms` }}
                >
                  <div className="relative hidden md:block">
                    <span className="absolute left-0 top-0 grid size-7 place-items-center border border-[#b56b32] bg-[#f7f3ec] font-mono text-xs text-[#7f421d] shadow-[0_12px_28px_-20px_rgba(111,62,31,0.95)] transition-all duration-300 group-hover:-translate-y-0.5 group-hover:bg-[#9d5728] group-hover:text-[#fffaf7]">
                      {index + 1}
                    </span>
                  </div>
                  <div className="grid gap-4 md:grid-cols-[0.42fr_0.58fr]">
                    <h3 className="text-2xl font-semibold tracking-[-0.045em] text-[#241f1a] transition-transform duration-300 group-hover:translate-x-1">
                      {step.title}
                    </h3>
                    <p className="text-base leading-7 text-[#655c52]">{step.body}</p>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
