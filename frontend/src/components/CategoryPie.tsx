import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { categoryColor } from "@/lib/categories";
import { formatINR } from "@/lib/format";

interface Props { data: Record<string, number> }

export function CategoryPie({ data }: Props) {
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  const total = entries.reduce((s, [, v]) => s + v, 0);
  const items = entries.map(([name, value]) => ({ name, value, color: categoryColor(name) }));

  return (
    <div className="flex flex-col gap-4 md:flex-row md:items-center">
      <div className="h-64 w-full md:w-64">
        <ResponsiveContainer>
          <PieChart>
            <Pie data={items} dataKey="value" nameKey="name" innerRadius={50} outerRadius={95} paddingAngle={2}>
              {items.map((e) => <Cell key={e.name} fill={e.color} stroke="var(--background)" strokeWidth={2} />)}
            </Pie>
            <Tooltip
              contentStyle={{ background: "var(--popover)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12, color: "var(--popover-foreground)" }}
              formatter={(v, n) => [formatINR(Number(v)), String(n)]}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="flex-1 space-y-1.5 text-sm">
        {items.map((e) => (
          <li key={e.name} className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 truncate">
              <span className="h-2.5 w-2.5 shrink-0 rounded-sm" style={{ background: e.color }} />
              <span className="truncate">{e.name}</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <span>{total > 0 ? Math.round((e.value / total) * 100) : 0}%</span>
              <span className="font-medium text-foreground">{formatINR(e.value)}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
