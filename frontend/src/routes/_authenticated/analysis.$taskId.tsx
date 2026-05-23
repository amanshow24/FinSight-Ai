import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { Download, Plus, Sparkles, TrendingDown, TrendingUp, Wallet, AlertTriangle, Repeat } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { getAnalysis, exportPdf } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { updateSessionWithResults } from "@/lib/sessions";
import { formatDate, formatINR } from "@/lib/format";
import { HealthScoreGauge } from "@/components/HealthScoreGauge";
import { CategoryPie } from "@/components/CategoryPie";
import { IncomeExpenseBar } from "@/components/IncomeExpenseBar";
import { TransactionsTable } from "@/components/TransactionsTable";
import { toast } from "sonner";

export const Route = createFileRoute("/_authenticated/analysis/$taskId")({
  component: AnalysisPage,
});

function AnalysisPage() {
  const { taskId } = Route.useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const { data, isLoading, error } = useQuery({
    queryKey: ["analysis", taskId],
    queryFn: () => getAnalysis(taskId),
  });

  useEffect(() => {
    if (data && user) {
      void updateSessionWithResults(user.uid, taskId, {
        bank_name: data.bank_name,
        health_score: data.health_score,
        health_grade: data.health_grade,
        total_income: data.total_income,
        total_expenses: data.total_expenses,
        net_savings: data.net_savings,
      });
    }
  }, [data, user, taskId]);

  async function handleExport() {
    try {
      const blob = await exportPdf(taskId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `finsight-${taskId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      toast.error(e?.message ?? "Export failed");
    }
  }

  if (isLoading) return <DashboardSkeleton />;
  if (error || !data) {
    return (
      <div className="mx-auto max-w-md px-4 py-20 text-center">
        <h2 className="text-xl font-semibold">Could not load analysis</h2>
        <Button className="mt-4" onClick={() => navigate({ to: "/home" })}>Back to home</Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-wider text-muted-foreground">{data.bank_name}</p>
          <h1 className="text-2xl font-bold md:text-3xl">Financial analysis</h1>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={handleExport}><Download className="mr-1 h-4 w-4" /> Export PDF</Button>
          <Button asChild><Link to="/upload"><Plus className="mr-1 h-4 w-4" /> Analyze another</Link></Button>
        </div>
      </div>

      {/* Summary stats */}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard icon={<TrendingUp className="h-5 w-5" />} tone="success" label="Total income" value={formatINR(data.total_income)} />
        <SummaryCard icon={<TrendingDown className="h-5 w-5" />} tone="destructive" label="Total expenses" value={formatINR(data.total_expenses)} />
        <SummaryCard
          icon={<Wallet className="h-5 w-5" />}
          tone={data.net_savings >= 0 ? "primary" : "destructive"}
          label="Net savings"
          value={formatINR(data.net_savings)}
        />
        <Card className="flex items-center gap-4 p-5">
          <HealthScoreGauge score={data.health_score} grade={data.health_grade} />
          <div>
            <p className="text-xs uppercase tracking-wider text-muted-foreground">Health score</p>
            <p className="mt-1 text-lg font-semibold">{data.health_score} / 100</p>
            <p className="text-xs text-muted-foreground">Grade {data.health_grade}</p>
          </div>
        </Card>
      </div>

      {/* Charts */}
      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card className="p-5">
          <h3 className="font-semibold">Spending by category</h3>
          <div className="mt-4">
            <CategoryPie data={data.category_breakdown} />
          </div>
        </Card>
        <Card className="p-5">
          <h3 className="font-semibold">Income vs Expenses</h3>
          <div className="mt-4">
            <IncomeExpenseBar income={data.total_income} expenses={data.total_expenses} />
          </div>
        </Card>
      </div>

      {/* AI Summary */}
      <Card className="mt-6 p-5">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Sparkles className="h-4 w-4" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold">AI summary</h3>
            <p className="mt-2 text-sm leading-relaxed text-foreground/90">{data.ai_summary}</p>
            <div className="mt-4 border-t border-border pt-4">
              <h4 className="text-sm font-semibold">Recommendations</h4>
              <ul className="mt-2 space-y-2 text-sm">
                {data.recommendations.map((r, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                    <span className="text-foreground/90">{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </Card>

      {/* Recurring & Anomalies */}
      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card className="p-5">
          <div className="flex items-center gap-2"><Repeat className="h-4 w-4 text-muted-foreground" /><h3 className="font-semibold">Recurring payments</h3></div>
          <div className="mt-4 overflow-x-auto">
            {data.recurring_payments.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">No recurring payments detected</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow><TableHead>Name</TableHead><TableHead>Frequency</TableHead><TableHead className="text-right">Amount</TableHead></TableRow>
                </TableHeader>
                <TableBody>
                  {data.recurring_payments.map((r) => (
                    <TableRow key={r.name}>
                      <TableCell className="font-medium">{r.name}</TableCell>
                      <TableCell><Badge variant="secondary">{r.frequency}</Badge></TableCell>
                      <TableCell className="text-right">{formatINR(r.amount)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-destructive" /><h3 className="font-semibold">Anomalous transactions</h3></div>
          <div className="mt-4 overflow-x-auto">
            {data.anomalies.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">No anomalies detected</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow><TableHead>Date</TableHead><TableHead>Description</TableHead><TableHead className="text-right">Amount</TableHead><TableHead>Why flagged</TableHead></TableRow>
                </TableHeader>
                <TableBody>
                  {data.anomalies.map((a, i) => (
                    <TableRow key={i} className="bg-destructive/5">
                      <TableCell className="whitespace-nowrap text-xs">{formatDate(a.date)}</TableCell>
                      <TableCell className="max-w-[200px] truncate">{a.narration}</TableCell>
                      <TableCell className="text-right font-medium text-destructive">{formatINR(a.amount)}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">{a.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </Card>
      </div>

      {/* Transactions */}
      <Card className="mt-6 p-5">
        <h3 className="font-semibold">All transactions</h3>
        <div className="mt-4">
          <TransactionsTable transactions={data.transactions} />
        </div>
      </Card>
    </div>
  );
}

function SummaryCard({ icon, label, value, tone }: { icon: React.ReactNode; label: string; value: string; tone: "success" | "destructive" | "primary" }) {
  const toneClass = tone === "success" ? "bg-success/15 text-success" : tone === "destructive" ? "bg-destructive/15 text-destructive" : "bg-primary/15 text-primary";
  return (
    <Card className="p-5">
      <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${toneClass}`}>{icon}</div>
      <p className="mt-3 text-xs uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-bold tracking-tight">{value}</p>
    </Card>
  );
}

function DashboardSkeleton() {
  return (
    <div className="mx-auto max-w-6xl space-y-4 px-4 py-8">
      <div className="h-10 w-1/3 animate-pulse rounded bg-muted/50" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-28 animate-pulse rounded-xl bg-muted/40" />)}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="h-72 animate-pulse rounded-xl bg-muted/40" />
        <div className="h-72 animate-pulse rounded-xl bg-muted/40" />
      </div>
      <div className="h-40 animate-pulse rounded-xl bg-muted/40" />
    </div>
  );
}
