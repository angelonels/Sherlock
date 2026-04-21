"use client";

import { ArrowRight, ShieldCheck } from "@phosphor-icons/react";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import type { MouseEvent, ReactNode } from "react";

type MagneticButtonProps = {
  children: ReactNode;
  href: string;
  variant?: "primary" | "secondary";
};

export function MagneticButton({
  children,
  href,
  variant = "primary",
}: MagneticButtonProps) {
  const pointerX = useMotionValue(0);
  const pointerY = useMotionValue(0);
  const springX = useSpring(pointerX, { stiffness: 180, damping: 18, mass: 0.25 });
  const springY = useSpring(pointerY, { stiffness: 180, damping: 18, mass: 0.25 });
  const x = useTransform(springX, [-0.5, 0.5], [-8, 8]);
  const y = useTransform(springY, [-0.5, 0.5], [-5, 5]);

  function handleMouseMove(event: MouseEvent<HTMLAnchorElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    pointerX.set((event.clientX - rect.left) / rect.width - 0.5);
    pointerY.set((event.clientY - rect.top) / rect.height - 0.5);
  }

  function handleMouseLeave() {
    pointerX.set(0);
    pointerY.set(0);
  }

  const isPrimary = variant === "primary";

  return (
    <motion.a
      href={href}
      style={{ x, y }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      whileTap={{ scale: 0.98, y: 1 }}
      transition={{ type: "spring", stiffness: 100, damping: 20 }}
      className={[
        "group sheen relative inline-flex h-12 w-full max-w-full items-center justify-center gap-3 overflow-hidden px-5 text-sm font-semibold tracking-[-0.01em] transition-all duration-300 focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-[#b56b32]/25 sm:w-auto sm:px-6",
        isPrimary
          ? "border border-[#9d5728] bg-[#9d5728] text-[#fffaf7] shadow-[0_18px_45px_-26px_rgba(111,62,31,0.9),inset_0_1px_0_rgba(255,255,255,0.22)] hover:bg-[#7f421d] hover:shadow-[0_24px_58px_-30px_rgba(111,62,31,0.95),inset_0_1px_0_rgba(255,255,255,0.26)]"
          : "border border-[#d9cdbf] bg-[#fffaf7] text-[#2b2520] shadow-[0_18px_45px_-34px_rgba(70,47,30,0.62)] hover:border-[#9d5728] hover:text-[#7f421d]",
      ].join(" ")}
    >
      <span
        className={[
          "absolute right-1 top-1 h-2 w-2 border-r border-t",
          isPrimary ? "border-white/70" : "border-[#9d5728]/70",
        ].join(" ")}
      />
      {isPrimary ? (
        <ArrowRight size={18} weight="bold" className="transition-transform group-hover:translate-x-0.5" />
      ) : (
        <ShieldCheck size={18} weight="regular" />
      )}
      <span className="min-w-0 truncate">{children}</span>
    </motion.a>
  );
}
