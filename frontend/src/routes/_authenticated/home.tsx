import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { FileText, Plus, TrendingUp, TrendingDown } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { listSessions } from "@/lib/sessions";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatINR, formatDate } from "@/lib/format";

export const Route = createFileRoute("/_authenticated/home")({
  component: HomePage,
});

function HomePage() {
  const { user } = useAuth();
  const { data: sessions, isLoading } = useQuery({
    queryKey: ["sessions", user?.uid],
    queryFn: () => listSessions(user!.uid),
    enabled: !!user,
  });

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 md:py-12">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold md:text-3xl">Welcome back, {user?.displayName?.split(" ")[0] ?? "there"}</h1>
          <p className="mt-1 text-muted-foreground">Your recent statement analyses</p>
        </div>
        <Button asChild size="lg">
          <Link to="/upload"><Plus className="mr-1 h-4 w-4" /> Analyze new statement</Link>
        </Button>
      </div>

      <div className="mt-8">
        {isLoading ? (
          <SkeletonGrid />
        ) : !sessions || sessions.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {sessions.map((s) => (
              <Card key={s.task_id} className="p-5 transition hover:shadow-md">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">{s.bank_name}</span>
                    </div>
                    <p className="mt-0.5 text-xs text-muted-foreground">{formatDate(s.created_at)}</p>
                  </div>
                  <ScoreBadge score={s.health_score} grade={s.health_grade} />
                </div>
                <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
                  <Stat icon={<TrendingUp className="h-3.5 w-3.5 text-success" />} label="Income" value={formatINR(s.total_income)} />
                  <Stat icon={<TrendingDown className="h-3.5 w-3.5 text-destructive" />} label="Expenses" value={formatINR(s.total_expenses)} />
                </div>
                <div className="mt-3 border-t border-border pt-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Net savings</span>
                    <span className={s.net_savings >= 0 ? "font-semibold text-success" : "font-semibold text-destructive"}>
                      {formatINR(s.net_savings)}
                    </span>
                  </div>
                </div>
                <Button asChild variant="outline" className="mt-4 w-full">
                  <Link to="/analysis/$taskId" params={{ taskId: s.task_id }}>View analysis</Link>
                </Button>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ScoreBadge({ score, grade }: { score: number; grade: string }) {
  const tone = score >= 70 ? "bg-success/15 text-success" : score >= 55 ? "bg-warning/20 text-warning-foreground" : "bg-destructive/15 text-destructive";
  return <Badge className={`${tone} border-transparent`}>{score} · {grade}</Badge>;
}

function Stat({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div>
      <div className="flex items-center gap-1 text-xs text-muted-foreground">{icon}{label}</div>
      <div className="mt-0.5 font-semibold">{value}</div>
    </div>
  );
}

function SkeletonGrid() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 3 }).map((_, i) => (
        <Card key={i} className="h-48 animate-pulse bg-muted/40" />
      ))}
    </div>
  );
}

function EmptyState() {
  return (
    <Card className="flex flex-col items-center px-6 py-16 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-accent text-accent-foreground">
        <FileText className="h-7 w-7" />
      </div>
      <h2 className="mt-4 text-lg font-semibold">No analyses yet</h2>
      <p className="mt-1 max-w-sm text-sm text-muted-foreground">
        Upload your first bank statement (PDF or CSV) to see your financial picture in seconds.
      </p>
      <Button asChild className="mt-6">
        <Link to="/upload"><Plus className="mr-1 h-4 w-4" /> Analyze new statement</Link>
      </Button>
    </Card>
  );
}
