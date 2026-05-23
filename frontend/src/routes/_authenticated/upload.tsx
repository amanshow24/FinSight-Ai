import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useCallback, useState } from "react";
import { Upload, FileText, ShieldCheck, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { uploadStatement, useMockApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { createSession } from "@/lib/sessions";
import { toast } from "sonner";

export const Route = createFileRoute("/_authenticated/upload")({
  component: UploadPage,
});

const MAX_SIZE = 10 * 1024 * 1024;
const ACCEPTED = [".pdf", ".csv"];

function isValid(f: File) {
  const name = f.name.toLowerCase();
  return ACCEPTED.some((e) => name.endsWith(e)) && f.size <= MAX_SIZE;
}

function UploadPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [drag, setDrag] = useState(false);

  const onPick = (f: File | null) => {
    if (!f) return setFile(null);
    if (!isValid(f)) {
      toast.error("Only PDF or CSV under 10MB are supported");
      return;
    }
    setFile(f);
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDrag(false);
    const f = e.dataTransfer.files?.[0];
    if (f) onPick(f);
  }, []);

  async function submit() {
    if (!file || !user) return;
    setBusy(true);
    try {
      const { task_id } = await uploadStatement(file);
      await createSession(user.uid, task_id);
      navigate({ to: "/status/$taskId", params: { taskId: task_id } });
    } catch (err: any) {
      toast.error(err?.message ?? "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 md:py-12">
      <div className="text-center">
        <h1 className="text-2xl font-bold md:text-3xl">Analyze a bank statement</h1>
        <p className="mt-2 text-muted-foreground">Upload a single PDF or CSV (max 10MB)</p>
      </div>

      <Card
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={onDrop}
        className={`mt-8 border-2 border-dashed p-10 text-center transition ${drag ? "border-primary bg-accent/40" : "border-border"}`}
      >
        {file ? (
          <div className="flex items-center justify-between rounded-lg border border-border bg-card p-4 text-left">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-md bg-success/15 text-success">
                <FileText className="h-5 w-5" />
              </div>
              <div>
                <div className="font-medium">{file.name}</div>
                <div className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(0)} KB · Ready to analyze</div>
              </div>
            </div>
            <Button variant="ghost" size="icon" onClick={() => setFile(null)} aria-label="Remove file">
              <X className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          <>
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-accent text-accent-foreground">
              <Upload className="h-7 w-7" />
            </div>
            <p className="mt-4 font-medium">Drag &amp; drop your statement here</p>
            <p className="mt-1 text-sm text-muted-foreground">or click to browse — PDF or CSV</p>
            <label className="mt-5 inline-block">
              <input
                type="file"
                className="hidden"
                accept=".pdf,.csv,application/pdf,text/csv"
                onChange={(e) => onPick(e.target.files?.[0] ?? null)}
              />
              <span className="inline-flex h-9 cursor-pointer items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90">
                Choose file
              </span>
            </label>
          </>
        )}
      </Card>

      <div className="mt-6 flex items-center justify-between gap-3">
        <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <ShieldCheck className="h-3.5 w-3.5" />
          Files are analyzed and deleted within 24 hours. No data is retained.
        </p>
        <Button disabled={!file || busy} onClick={submit} size="lg">
          {busy ? "Uploading…" : "Analyze statement"}
        </Button>
      </div>

      {useMockApi && (
        <p className="mt-4 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-center text-xs text-warning-foreground">
          Demo mode — using mock analysis. Set <code>VITE_API_URL</code> to connect a real backend.
        </p>
      )}
    </div>
  );
}
