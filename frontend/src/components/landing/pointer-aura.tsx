"use client";

import { motion, useMotionValue, useSpring } from "framer-motion";
import { useEffect } from "react";

export function PointerAura() {
  const pointerX = useMotionValue(-320);
  const pointerY = useMotionValue(-320);
  const x = useSpring(pointerX, { stiffness: 70, damping: 26, mass: 0.35 });
  const y = useSpring(pointerY, { stiffness: 70, damping: 26, mass: 0.35 });

  useEffect(() => {
    const media = window.matchMedia("(pointer: fine)");

    function handlePointerMove(event: PointerEvent) {
      if (!media.matches) {
        return;
      }

      pointerX.set(event.clientX - 220);
      pointerY.set(event.clientY - 220);
    }

    window.addEventListener("pointermove", handlePointerMove, { passive: true });
    return () => window.removeEventListener("pointermove", handlePointerMove);
  }, [pointerX, pointerY]);

  return (
    <motion.div
      aria-hidden="true"
      className="pointer-events-none fixed left-0 top-0 z-[1] hidden size-[440px] rounded-full bg-[radial-gradient(circle,rgba(201,129,70,0.16)_0%,rgba(201,129,70,0.07)_34%,transparent_70%)] mix-blend-multiply blur-xl lg:block"
      style={{ x, y }}
    />
  );
}
