"use client";

import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";

type AnimatedNumberProps = {
  value: number;
  formatter?: Intl.NumberFormat;
  className?: string;
};

const defaultFormatter = new Intl.NumberFormat("en-US");

export function AnimatedNumber({
  value,
  formatter = defaultFormatter,
  className,
}: AnimatedNumberProps) {
  const source = useMotionValue(value);
  const spring = useSpring(source, { stiffness: 260, damping: 30, mass: 0.22 });
  const display = useTransform(spring, (latest) => formatter.format(Math.round(latest)));

  return (
    <motion.span
      className={className}
      initial={false}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.12 }}
    >
      {display}
    </motion.span>
  );
}
