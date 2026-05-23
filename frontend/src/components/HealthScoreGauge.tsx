interface Props { score: number; grade: string }

export function HealthScoreGauge({ score, grade }: Props) {
  const radius = 38;
  const c = 2 * Math.PI * radius;
  const pct = Math.max(0, Math.min(100, score)) / 100;
  const offset = c * (1 - pct);
  const color = score >= 70 ? "var(--success)" : score >= 55 ? "var(--warning)" : "var(--destructive)";

  return (
    <div className="relative flex h-24 w-24 items-center justify-center">
      <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
        <circle cx="50" cy="50" r={radius} fill="none" stroke="var(--muted)" strokeWidth="9" />
        <circle
          cx="50" cy="50" r={radius} fill="none"
          stroke={color} strokeWidth="9" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-bold leading-none">{score}</span>
        <span className="text-[10px] uppercase tracking-wider text-muted-foreground">{grade}</span>
      </div>
    </div>
  );
}
