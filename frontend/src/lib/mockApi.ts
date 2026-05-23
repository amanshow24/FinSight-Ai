import type { AnalysisResponse, StatusResponse, Transaction } from "./types";
import { CATEGORIES } from "./categories";

const store = new Map<string, { startedAt: number; bank: string; fileName: string }>();

export function mockUpload(file: File): { task_id: string } {
  const task_id = `mock_${Math.random().toString(36).slice(2, 10)}`;
  const banks = ["HDFC Bank", "ICICI Bank", "State Bank of India", "Axis Bank", "Kotak Mahindra"];
  store.set(task_id, {
    startedAt: Date.now(),
    bank: banks[Math.floor(Math.random() * banks.length)],
    fileName: file.name,
  });
  return { task_id };
}

export function mockStatus(task_id: string): StatusResponse {
  const entry = store.get(task_id);
  if (!entry) {
    // Allow viewing of historical sessions — treat as already done
    store.set(task_id, { startedAt: Date.now() - 10000, bank: "HDFC Bank", fileName: "" });
    return { status: "done", progress: 100 };
  }
  const elapsed = Date.now() - entry.startedAt;
  const total = 6000; // 6s
  if (elapsed >= total) return { status: "done", progress: 100 };
  return { status: "processing", progress: Math.round((elapsed / total) * 100) };
}

function seedRand(seed: number) {
  let s = seed;
  return () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
}

function hashString(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

const narrationByCat: Record<string, string[]> = {
  "Food & Dining": ["Zomato Order", "Swiggy Food Delivery", "Starbucks Coffee", "Domino's Pizza", "Local Restaurant"],
  "Salary / Income": ["Salary Credit", "Freelance Payment", "Interest Credit"],
  "EMI / Loan": ["HDFC Home Loan EMI", "Bajaj Finserv EMI", "Car Loan EMI"],
  "Subscriptions": ["Netflix", "Spotify Premium", "Amazon Prime", "Disney+ Hotstar", "Adobe Creative Cloud"],
  "Shopping": ["Amazon Purchase", "Flipkart Order", "Myntra Fashion", "Reliance Trends"],
  "Travel": ["Uber Trip", "IRCTC Booking", "Ola Cabs", "MakeMyTrip Flight", "Indigo Airlines"],
  "Healthcare": ["Apollo Pharmacy", "Practo Consultation", "1mg Order", "Medical Bill"],
  "Recharge / Bills": ["Airtel Recharge", "Jio Postpaid", "BESCOM Electricity", "Gas Bill Payment"],
  "Education": ["Udemy Course", "Coursera Plus", "Byju's Subscription"],
  "UPI Transfer": ["UPI/Friend/Split bill", "UPI/Family transfer", "UPI/Rent payment", "UPI/PhonePe@ybl"],
  "Cash / ATM": ["ATM Withdrawal SBI", "ATM Withdrawal HDFC"],
  "Others": ["Misc Charge", "Service Fee", "GST Charges"],
};

export function mockAnalysis(task_id: string): AnalysisResponse {
  const seed = hashString(task_id) || 12345;
  const rand = seedRand(seed);
  const banks = ["HDFC Bank", "ICICI Bank", "State Bank of India", "Axis Bank", "Kotak Mahindra"];
  const entry = store.get(task_id);
  const bank = entry?.bank ?? banks[Math.floor(rand() * banks.length)];

  const transactions: Transaction[] = [];
  let balance = 50000 + Math.floor(rand() * 100000);
  const start = new Date();
  start.setDate(start.getDate() - 60);

  const numTxn = 55 + Math.floor(rand() * 25);
  for (let i = 0; i < numTxn; i++) {
    const day = new Date(start);
    day.setDate(start.getDate() + Math.floor((i / numTxn) * 60));
    const cat = CATEGORIES[Math.floor(rand() * CATEGORIES.length)];
    const isIncome = cat === "Salary / Income" || (cat === "UPI Transfer" && rand() > 0.7);
    const amt = isIncome
      ? Math.floor(5000 + rand() * 60000)
      : Math.floor(50 + rand() * (cat === "EMI / Loan" ? 25000 : 5000));
    const narrList = narrationByCat[cat];
    const narration = narrList[Math.floor(rand() * narrList.length)];
    const debit = isIncome ? null : amt;
    const credit = isIncome ? amt : null;
    balance = balance + (credit ?? 0) - (debit ?? 0);

    const is_anomaly = !isIncome && amt > 4500 && rand() > 0.92;
    const is_recurring = ["EMI / Loan", "Subscriptions", "Recharge / Bills"].includes(cat) && rand() > 0.5;

    transactions.push({
      id: `txn_${i}_${task_id}`,
      date: day.toISOString().slice(0, 10),
      narration,
      debit,
      credit,
      balance,
      category: cat,
      is_recurring,
      is_anomaly,
    });
  }

  transactions.sort((a, b) => b.date.localeCompare(a.date));

  const total_income = transactions.reduce((s, t) => s + (t.credit ?? 0), 0);
  const total_expenses = transactions.reduce((s, t) => s + (t.debit ?? 0), 0);
  const net_savings = total_income - total_expenses;

  const savingsRate = total_income > 0 ? net_savings / total_income : 0;
  const health_score = Math.max(20, Math.min(98, Math.round(50 + savingsRate * 60)));
  const health_grade = health_score >= 85 ? "A" : health_score >= 70 ? "B" : health_score >= 55 ? "C" : "D";

  const category_breakdown: Record<string, number> = {};
  for (const t of transactions) {
    if (t.debit) category_breakdown[t.category] = (category_breakdown[t.category] ?? 0) + t.debit;
  }

  const recurringMap = new Map<string, { amount: number; count: number; category: string }>();
  for (const t of transactions) {
    if (t.is_recurring && t.debit) {
      const cur = recurringMap.get(t.narration) ?? { amount: 0, count: 0, category: t.category };
      cur.amount += t.debit;
      cur.count += 1;
      recurringMap.set(t.narration, cur);
    }
  }
  const recurring_payments = Array.from(recurringMap.entries()).slice(0, 6).map(([name, v]) => ({
    name,
    amount: Math.round(v.amount / v.count),
    frequency: v.category === "Subscriptions" ? "Monthly subscription" : v.category === "EMI / Loan" ? "Monthly EMI" : "Monthly",
  }));

  const anomalies = transactions
    .filter((t) => t.is_anomaly)
    .slice(0, 5)
    .map((t) => ({
      date: t.date,
      narration: t.narration,
      amount: t.debit ?? 0,
      reason: "Significantly higher than your typical spending in this category",
    }));

  const ai_summary = `Over the last 60 days at ${bank}, you earned ${Math.round(total_income).toLocaleString("en-IN")} and spent ${Math.round(total_expenses).toLocaleString("en-IN")}, giving you a ${(savingsRate * 100).toFixed(1)}% savings rate. Your top spending category is ${Object.entries(category_breakdown).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "Others"}. Overall, your financial health is rated ${health_grade}.`;

  const recommendations = [
    savingsRate < 0.2 ? "Try to save at least 20% of your monthly income — set up an auto-transfer to a savings account." : "Great savings rate — consider investing the surplus in mutual funds or an FD.",
    recurring_payments.length > 3 ? `You have ${recurring_payments.length} recurring payments. Review subscriptions you no longer use.` : "Your subscription footprint is healthy — keep it lean.",
    anomalies.length > 0 ? `${anomalies.length} unusual transaction(s) detected. Verify these are legitimate.` : "No suspicious activity detected this period.",
    "Track your food & dining spend — small daily expenses compound quickly.",
  ];

  return {
    session_id: task_id,
    bank_name: bank,
    total_income,
    total_expenses,
    net_savings,
    health_score,
    health_grade,
    ai_summary,
    recommendations,
    transactions,
    category_breakdown,
    recurring_payments,
    anomalies,
  };
}

export function mockExportPdf(analysis: AnalysisResponse): Blob {
  const text = `FinSight AI — Analysis Report\n\nBank: ${analysis.bank_name}\nHealth Score: ${analysis.health_score} (${analysis.health_grade})\nTotal Income: ₹${analysis.total_income.toLocaleString("en-IN")}\nTotal Expenses: ₹${analysis.total_expenses.toLocaleString("en-IN")}\nNet Savings: ₹${analysis.net_savings.toLocaleString("en-IN")}\n\nAI Summary:\n${analysis.ai_summary}\n\nRecommendations:\n${analysis.recommendations.map((r, i) => `${i + 1}. ${r}`).join("\n")}\n`;
  return new Blob([text], { type: "application/pdf" });
}
