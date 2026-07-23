import type { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}

export function Card({ children, className = "", hover = true }: CardProps) {
  return (
    <div
      className={`rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-6 shadow-sm transition-all duration-200 ease-out ${
        hover ? "hover:shadow-md hover:border-[var(--color-accent)]/20" : ""
      } ${className}`}
    >
      {children}
    </div>
  );
}
