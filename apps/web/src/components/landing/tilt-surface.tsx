"use client";

import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import type { MouseEvent, ReactNode } from "react";

type TiltSurfaceProps = {
  children: ReactNode;
  className?: string;
};

export function TiltSurface({ children, className }: TiltSurfaceProps) {
  const pointerX = useMotionValue(0);
  const pointerY = useMotionValue(0);
  const smoothX = useSpring(pointerX, { stiffness: 120, damping: 18, mass: 0.28 });
  const smoothY = useSpring(pointerY, { stiffness: 120, damping: 18, mass: 0.28 });
  const rotateY = useTransform(smoothX, [-0.5, 0.5], [-2.4, 2.4]);
  const rotateX = useTransform(smoothY, [-0.5, 0.5], [2, -2]);
  const translateY = useTransform(smoothY, [-0.5, 0.5], [-2, 2]);

  function handleMouseMove(event: MouseEvent<HTMLDivElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    pointerX.set((event.clientX - rect.left) / rect.width - 0.5);
    pointerY.set((event.clientY - rect.top) / rect.height - 0.5);
  }

  function handleMouseLeave() {
    pointerX.set(0);
    pointerY.set(0);
  }

  return (
    <motion.div
      className={className}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        rotateX,
        rotateY,
        y: translateY,
        transformPerspective: 1200,
        transformStyle: "preserve-3d",
      }}
      transition={{ type: "spring", stiffness: 100, damping: 20 }}
    >
      {children}
    </motion.div>
  );
}
