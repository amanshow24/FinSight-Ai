import { createFileRoute, Link } from "@tanstack/react-router";
import { Sparkles, ShieldCheck, Brain, FileText, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";

export const Route = createFileRoute("/")({
  component: Landing,
});

function Landing() {
  const { user } = useAuth();
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Sparkles className="h-5 w-5" />
            </div>
            <span className="text-lg font-bold tracking-tight">FinSight AI</span>
          </div>
          <div className="flex items-center gap-2">
            {user ? (
              <Button asChild><Link to="/home">Open dashboard</Link></Button>
            ) : (
              <>
                <Button asChild variant="ghost"><Link to="/login">Sign in</Link></Button>
                <Button asChild><Link to="/login" search={{ mode: "signup" }}>Get started</Link></Button>
              </>
            )}
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-4 py-20 md:py-28">
        <div className="mx-auto max-w-3xl text-center">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-accent px-3 py-1 text-xs font-medium text-accent-foreground">
            <Sparkles className="h-3 w-3" /> AI-powered for Indian banks
          </span>
          <h1 className="mt-6 text-4xl font-bold tracking-tight md:text-6xl">
            Understand your money in <span className="text-primary">60 seconds</span>
          </h1>
          <p className="mt-5 text-lg text-muted-foreground md:text-xl">
            Upload any Indian bank statement (PDF or CSV) and get instant spending breakdowns,
            anomaly detection, and personalized recommendations — no finance degree required.
          </p>
          <div className="mt-8 flex justify-center gap-3">
            <Button asChild size="lg">
              <Link to={user ? "/upload" : "/login"}>
                {user ? "Analyze a statement" : "Start free analysis"}
                <ArrowRight className="ml-1 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>

        <div className="mt-20 grid gap-6 md:grid-cols-3">
          {[
            { icon: FileText, title: "Smart parsing", body: "Reads PDFs from HDFC, ICICI, SBI, Axis, Kotak and more — automatically." },
            { icon: Brain, title: "AI categorization", body: "Every transaction tagged across 12 categories with a fine-tuned model." },
            { icon: ShieldCheck, title: "Privacy first", body: "Files analyzed and deleted within 24 hours. Nothing is retained." },
          ].map((f) => (
            <div key={f.title} className="rounded-xl border border-border bg-card p-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                <f.icon className="h-5 w-5" />
              </div>
              <h3 className="mt-4 font-semibold">{f.title}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{f.body}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
