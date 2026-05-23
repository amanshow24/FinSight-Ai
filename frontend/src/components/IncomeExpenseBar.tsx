import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from "recharts";
import { formatINR } from "@/lib/format";

interface Props { income: number; expenses: number }

export function IncomeExpenseBar({ income, expenses }: Props) {
  const data = [
    { name: "Income", value: income, fill: "var(--success)" },
    { name: "Expenses", value: expenses, fill: "var(--destructive)" },
    { name: "Savings", value: Math.max(0, income - expenses), fill: "var(--primary)" },
  ];
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="name" stroke="var(--muted-foreground)" fontSize={12} />
          <YAxis stroke="var(--muted-foreground)" fontSize={11} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
          <Tooltip
            cursor={{ fill: "color-mix(in oklch, var(--muted) 40%, transparent)" }}
            contentStyle={{ background: "var(--popover)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12, color: "var(--popover-foreground)" }}
            formatter={(v) => formatINR(Number(v))}
          />
          <Bar dataKey="value" radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
