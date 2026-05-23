export const CATEGORIES = [
  "Food & Dining",
  "Salary / Income",
  "EMI / Loan",
  "Subscriptions",
  "Shopping",
  "Travel",
  "Healthcare",
  "Recharge / Bills",
  "Education",
  "UPI Transfer",
  "Cash / ATM",
  "Others",
] as const;

export type Category = (typeof CATEGORIES)[number];

// Maps to CSS variables in styles.css
export const CATEGORY_COLOR_VAR: Record<string, string> = {
  "Food & Dining": "var(--chart-1)",
  "Salary / Income": "var(--chart-2)",
  "EMI / Loan": "var(--chart-3)",
  "Subscriptions": "var(--chart-4)",
  "Shopping": "var(--chart-5)",
  "Travel": "var(--chart-6)",
  "Healthcare": "var(--chart-7)",
  "Recharge / Bills": "var(--chart-8)",
  "Education": "var(--chart-9)",
  "UPI Transfer": "var(--chart-10)",
  "Cash / ATM": "var(--chart-11)",
  "Others": "var(--chart-12)",
};

export function categoryColor(c: string): string {
  return CATEGORY_COLOR_VAR[c] ?? "var(--chart-12)";
}
