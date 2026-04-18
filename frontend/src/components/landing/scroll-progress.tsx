"use client";

import { motion, useScroll, useSpring } from "framer-motion";

export function ScrollProgress() {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, {
    stiffness: 140,
    damping: 28,
    mass: 0.18,
  });

  return (
    <motion.div
      aria-hidden="true"
      className="fixed left-0 top-0 z-40 h-px w-full origin-left bg-[#9d5728]"
      style={{ scaleX }}
    />
  );
}
