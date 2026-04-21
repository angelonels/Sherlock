"use client";

import { navItems } from "@/components/landing/landing-content";
import { motion } from "framer-motion";
import Link from "next/link";
import { useEffect, useState } from "react";

export function SiteHeader() {
  const [activeHref, setActiveHref] = useState<(typeof navItems)[number]["href"]>("#product");

  useEffect(() => {
    const sections = navItems
      .map((item) => document.querySelector(item.href))
      .filter((section): section is Element => Boolean(section));

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

        if (visible?.target.id) {
          setActiveHref(`#${visible.target.id}` as (typeof navItems)[number]["href"]);
        }
      },
      { rootMargin: "-22% 0px -58% 0px", threshold: [0.1, 0.2, 0.4, 0.6] },
    );

    sections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, []);

  return (
    <header className="sticky top-0 z-20 border-b border-[#ddd2c4]/80 bg-[#f7f3ec]/88 backdrop-blur-xl">
      <nav
        aria-label="Main navigation"
        className="mx-auto grid min-h-16 max-w-[1440px] grid-cols-[1fr_auto] items-center gap-4 px-4 sm:px-6 lg:grid-cols-[260px_1fr_180px] lg:px-8"
      >
        <Link
          href="/"
          className="group inline-flex w-fit items-center gap-3 rounded-sm text-[#241f1a] outline-none transition-colors hover:text-[#7f421d] focus-visible:ring-3 focus-visible:ring-[#b56b32]/25"
        >
          <span className="signal-pulse relative grid size-9 place-items-center overflow-hidden border border-[#241f1a] bg-[#241f1a] text-[#fffaf7] shadow-[3px_3px_0_#d2c3b3]">
            <span className="h-4 w-4 rounded-full border border-[#c98146]" />
            <span className="absolute bottom-2 right-2 h-px w-4 rotate-45 bg-[#c98146]" />
          </span>
          <span className="text-lg font-semibold tracking-[-0.03em]">Sherlock</span>
        </Link>

        <div className="hidden justify-self-center lg:flex">
          <div className="relative grid grid-cols-4 overflow-hidden border-x border-[#ddd2c4]/80">
            {navItems.map((item) => {
              const isActive = activeHref === item.href;

              return (
                <a
                  key={item.href}
                  href={item.href}
                  className={[
                    "relative px-5 py-5 text-sm font-medium transition-colors focus-visible:outline-none",
                    isActive ? "text-[#241f1a]" : "text-[#6d6258] hover:text-[#241f1a]",
                  ].join(" ")}
                >
                  {isActive ? (
                    <motion.span
                      layoutId="active-nav-background"
                      className="absolute inset-0 bg-[#ebe2d7]"
                      transition={{ type: "spring", stiffness: 360, damping: 34 }}
                    />
                  ) : null}
                  <span className="relative">{item.label}</span>
                </a>
              );
            })}
          </div>
        </div>

        <Link
          href="/sign-in"
          className="sheen inline-flex h-10 items-center justify-center justify-self-end overflow-hidden border border-[#241f1a] bg-[#241f1a] px-4 text-sm font-semibold text-[#fffaf7] shadow-[0_18px_44px_-34px_rgba(36,31,26,0.85)] transition-all duration-300 hover:-translate-y-0.5 hover:bg-[#3b332d] hover:shadow-[0_24px_60px_-38px_rgba(36,31,26,0.95)] focus-visible:ring-3 focus-visible:ring-[#b56b32]/25 focus-visible:outline-none active:translate-y-px"
        >
          Open app
        </Link>
      </nav>
    </header>
  );
}
