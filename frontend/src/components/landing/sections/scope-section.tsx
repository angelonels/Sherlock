import {
  audienceItems,
  outcomeItems,
  trustPrinciples,
} from "@/components/landing/landing-content";
import {
  ArrowRight,
  CheckCircle,
  Compass,
  ShieldCheck,
  Sparkle,
  UsersThree,
} from "@phosphor-icons/react/dist/ssr";

export function ScopeSection() {
  return (
    <section
      id="safety"
      className="section-depth relative overflow-hidden border-b border-[#ddd2c4]/80 py-28 sm:py-36 lg:py-44"
    >
      <div className="mx-auto max-w-[1440px] px-4 sm:px-6 lg:px-8">
        <div className="grid gap-12 lg:grid-cols-[1.1fr_0.9fr] lg:gap-20">
          <div>
            <div className="max-w-4xl">
              <h2 className="display-ink text-balance text-4xl font-semibold leading-[0.95] tracking-[-0.06em] text-[#241f1a] sm:text-6xl">
                Built for confident spreadsheet decisions
              </h2>
              <p className="mt-6 max-w-[64ch] text-lg leading-8 text-[#655c52]">
                Sherlock keeps the landing page promise simple: upload the spreadsheet,
                ask the business question, and review the evidence before acting on the
                answer.
              </p>
            </div>

            <div className="mt-14 grid gap-5 md:grid-cols-2">
              {trustPrinciples.map((principle) => (
                <article
                  key={principle.title}
                  className="group border-t border-[#d6c9bb] pt-5 transition-all duration-300 hover:-translate-y-1 hover:border-[#c98146]/45"
                >
                  <div className="mb-5 grid size-10 place-items-center bg-[#241f1a] text-[#fffaf7] shadow-[0_18px_36px_-28px_rgba(36,31,26,0.9)] transition-transform duration-300 group-hover:-rotate-3 group-hover:scale-105">
                    <ShieldCheck size={20} weight="duotone" />
                  </div>
                  <h3 className="text-2xl font-semibold tracking-[-0.045em] text-[#241f1a]">
                    {principle.title}
                  </h3>
                  <p className="mt-3 text-sm leading-6 text-[#655c52]">{principle.body}</p>
                </article>
              ))}
            </div>
          </div>

          <div className="grid gap-4 lg:pt-8">
            <div className="premium-surface lift-card border border-[#d8cbbb] bg-[#fffaf7] p-5">
              <div className="mb-6 flex items-center gap-3">
                <span className="grid size-10 place-items-center bg-[#9d5728] text-[#fffaf7]">
                  <Sparkle size={20} weight="duotone" />
                </span>
                <h3 className="text-2xl font-semibold tracking-[-0.045em] text-[#241f1a]">
                  What teams use it for
                </h3>
              </div>
              <ul className="space-y-3">
                {outcomeItems.map((item) => (
                  <li key={item} className="flex gap-3 text-sm leading-6 text-[#655c52]">
                    <CheckCircle size={17} className="mt-1 shrink-0 text-[#7f421d]" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1">
              {audienceItems.map((item, index) => (
                <article
                  key={item.title}
                  className="group lift-card border border-[#d8cbbb] bg-[#eee6db] p-5"
                >
                  <div className="mb-5 flex items-center justify-between">
                    <span className="grid size-9 place-items-center bg-[#241f1a] text-[#fffaf7]">
                      {index === 0 ? (
                        <Compass size={18} weight="duotone" />
                      ) : index === 1 ? (
                        <UsersThree size={18} weight="duotone" />
                      ) : (
                        <ShieldCheck size={18} weight="duotone" />
                      )}
                    </span>
                    <ArrowRight
                      size={18}
                      className="text-[#9d5728] transition-transform duration-300 group-hover:translate-x-1"
                    />
                  </div>
                  <h3 className="text-xl font-semibold tracking-[-0.04em] text-[#241f1a]">
                    {item.title}
                  </h3>
                  <p className="mt-3 text-sm leading-6 text-[#655c52]">{item.body}</p>
                </article>
              ))}
            </div>

            <div className="premium-dark-surface lift-card border border-[#d8cbbb] bg-[#241f1a] p-5 text-[#fffaf7]">
              <div className="mb-6 flex items-center gap-3">
                <span className="grid size-10 place-items-center bg-[#c98146] text-[#241f1a]">
                  <ShieldCheck size={20} weight="duotone" />
                </span>
                <h3 className="text-2xl font-semibold tracking-[-0.045em]">Clear by design</h3>
              </div>
              <p className="text-sm leading-6 text-[#d9cdc0]">
                Sherlock avoids pretending every spreadsheet is perfect. When the source
                data has gaps, the product keeps that context near the answer.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
