import { AnswerShowcase } from "@/components/landing/sections/answer-showcase";
import { CtaFooter } from "@/components/landing/sections/cta-footer";
import { HeroSection } from "@/components/landing/sections/hero-section";
import { PointerAura } from "@/components/landing/pointer-aura";
import { ScopeSection } from "@/components/landing/sections/scope-section";
import { SiteHeader } from "@/components/landing/sections/site-header";
import { WorkflowSection } from "@/components/landing/sections/workflow-section";
import { ScrollProgress } from "@/components/landing/scroll-progress";
import { SectionReveal } from "@/components/landing/section-reveal";

export function LandingPage() {
  return (
    <main className="relative min-h-[100dvh] w-full max-w-full overflow-x-hidden bg-[#f7f3ec] text-[#241f1a]">
      <ScrollProgress />
      <PointerAura />
      <div className="ambient-light" aria-hidden="true" />
      <div className="paper-grain" aria-hidden="true" />
      <SiteHeader />
      <HeroSection />
      <SectionReveal>
        <WorkflowSection />
      </SectionReveal>
      <SectionReveal>
        <AnswerShowcase />
      </SectionReveal>
      <SectionReveal>
        <ScopeSection />
      </SectionReveal>
      <SectionReveal>
        <CtaFooter />
      </SectionReveal>
    </main>
  );
}
