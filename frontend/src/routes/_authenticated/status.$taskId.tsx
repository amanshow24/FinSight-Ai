import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Sparkles, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { getStatus } from "@/lib/api";

export const Route = createFileRoute("/_authenticated/status/$taskId")({
  component: StatusPage,
});

const STEPS = [
  "Extracting transactions…",
  "Running AI categorization…",
  "Detecting patterns…",
  "Generating insights…",
];

function StatusPage() {
  const { taskId } = Route.useParams();
  const navigate = useNavigate();
  const [stepIdx, setStepIdx] = useState(0);

  const { data, error } = useQuery({
    queryKey: ["status", taskId],
    queryFn: () => getStatus(taskId),
    refetchInterval: (q) => {
      const s = q.state.data?.status;
      return s === "done" || s === "failed" ? false : 2000;
    },
  });

  useEffect(() => {
    const t = setInterval(() => setStepIdx((i) => (i + 1) % STEPS.length), 1500);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (data?.status === "done") navigate({ to: "/analysis/$taskId", params: { taskId } });
  }, [data, navigate, taskId]);

  const progress = data?.progress ?? 5;
  const failed = data?.status === "failed" || !!error;

  return (
    <div className="mx-auto flex max-w-xl flex-col items-center px-4 py-16">
      <Card className="w-full p-8 text-center">
        {failed ? (
          <>
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-destructive/15 text-destructive">
              <AlertCircle className="h-7 w-7" />
            </div>
            <h2 className="mt-4 text-xl font-semibold">Analysis failed</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              We couldn't process this statement. Please try again with a different file.
            </p>
            <Button className="mt-6" onClick={() => navigate({ to: "/upload" })}>Try again</Button>
          </>
        ) : (
          <>
            <div className="mx-auto flex h-14 w-14 animate-pulse items-center justify-center rounded-full bg-primary text-primary-foreground">
              <Sparkles className="h-7 w-7" />
            </div>
            <h2 className="mt-4 text-xl font-semibold">{STEPS[stepIdx]}</h2>
            <p className="mt-1 text-sm text-muted-foreground">This usually takes 5–20 seconds.</p>
            <div className="mt-6">
              <Progress value={progress} />
              <p className="mt-2 text-xs text-muted-foreground">{progress}%</p>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
