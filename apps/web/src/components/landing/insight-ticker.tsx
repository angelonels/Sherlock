"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";

const prompts = [
  "Which region softened in April?",
  "Where are missing values affecting confidence?",
  "What changed from January to March?",
] as const;

export function InsightTicker() {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    const interval = window.setInterval(() => {
      setActiveIndex((index) => (index + 1) % prompts.length);
    }, 3200);

    return () => window.clearInterval(interval);
  }, []);

  return (
    <div className="reveal-up mt-5 w-full max-w-full overflow-hidden border border-[#ddd2c4] bg-[#fffaf7]/70 px-4 py-3 shadow-[0_18px_46px_-38px_rgba(70,47,30,0.68)] backdrop-blur-sm sm:max-w-2xl">
      <div className="grid min-h-6 min-w-0 grid-cols-[auto_auto_minmax(0,1fr)] items-center gap-3 overflow-hidden">
        <span className="font-mono text-[11px] leading-4 text-[#8f6a4e]">Ask Sherlock</span>
        <div className="h-4 w-px bg-[#d8cbbb]" />
        <motion.p
          key={prompts[activeIndex]}
          initial={{ opacity: 0.35, y: 6, filter: "blur(3px)" }}
          animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
          transition={{ type: "spring", stiffness: 180, damping: 24, mass: 0.22 }}
          className="min-w-0 truncate text-sm font-medium tracking-[-0.01em] text-[#3d342d]"
        >
          {prompts[activeIndex]}
        </motion.p>
      </div>
    </div>
  );
}
