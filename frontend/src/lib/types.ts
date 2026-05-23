export interface UploadResponse { task_id: string }

export interface StatusResponse {
  status: "pending" | "processing" | "done" | "failed";
  progress: number;
}

export interface Transaction {
  id: string;
  date: string;
  narration: string;
  debit: number | null;
  credit: number | null;
  balance: number;
  category: string;
  is_recurring: boolean;
  is_anomaly: boolean;
}

export interface RecurringPayment {
  name: string;
  amount: number;
  frequency: string;
}

export interface Anomaly {
  date: string;
  narration: string;
  amount: number;
  reason: string;
}

export interface AnalysisResponse {
  session_id: string;
  bank_name: string;
  total_income: number;
  total_expenses: number;
  net_savings: number;
  health_score: number;
  health_grade: string;
  ai_summary: string;
  recommendations: string[];
  transactions: Transaction[];
  category_breakdown: Record<string, number>;
  recurring_payments: RecurringPayment[];
  anomalies: Anomaly[];
}

export interface SessionMeta {
  task_id: string;
  bank_name: string;
  created_at: number;
  health_score: number;
  health_grade: string;
  total_income: number;
  total_expenses: number;
  net_savings: number;
  status: StatusResponse["status"];
}
