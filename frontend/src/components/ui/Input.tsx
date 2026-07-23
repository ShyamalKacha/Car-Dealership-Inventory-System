import type { InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export function Input({ label, error, className = "", ...props }: InputProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-sm font-medium text-[var(--color-text-primary)]">
        {label}
      </label>
      <input
        className={`rounded-lg border bg-[var(--color-bg-primary)] px-3 py-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-secondary)] transition-all duration-200 ease-out focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] focus:border-transparent ${
          error
            ? "border-[var(--color-danger)] focus:ring-[var(--color-danger)]"
            : "border-[var(--color-border)]"
        } ${className}`}
        {...props}
      />
      {error && (
        <span className="text-xs text-[var(--color-danger)]">{error}</span>
      )}
    </div>
  );
}
