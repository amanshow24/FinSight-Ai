import { useMemo, useState } from "react";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { CategoryBadge } from "./CategoryBadge";
import { formatDate, formatINR } from "@/lib/format";
import { CATEGORIES } from "@/lib/categories";
import type { Transaction } from "@/lib/types";

const PAGE = 20;

export function TransactionsTable({ transactions }: { transactions: Transaction[] }) {
  const [cat, setCat] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"date" | "amount">("date");
  const [dir, setDir] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(0);

  const filtered = useMemo(() => {
    const list = cat === "all" ? transactions : transactions.filter((t) => t.category === cat);
    const sorted = [...list].sort((a, b) => {
      if (sortBy === "amount") {
        const av = (a.credit ?? 0) - (a.debit ?? 0);
        const bv = (b.credit ?? 0) - (b.debit ?? 0);
        return dir === "asc" ? av - bv : bv - av;
      }
      return dir === "asc" ? a.date.localeCompare(b.date) : b.date.localeCompare(a.date);
    });
    return sorted;
  }, [transactions, cat, sortBy, dir]);

  const pages = Math.max(1, Math.ceil(filtered.length / PAGE));
  const slice = filtered.slice(page * PAGE, page * PAGE + PAGE);

  function toggleSort(col: "date" | "amount") {
    if (sortBy === col) setDir(dir === "asc" ? "desc" : "asc");
    else { setSortBy(col); setDir("desc"); }
    setPage(0);
  }

  const SortIcon = ({ col }: { col: "date" | "amount" }) =>
    sortBy !== col ? <ArrowUpDown className="ml-1 inline h-3 w-3 opacity-50" /> :
    dir === "asc" ? <ArrowUp className="ml-1 inline h-3 w-3" /> : <ArrowDown className="ml-1 inline h-3 w-3" />;

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3">
        <Select value={cat} onValueChange={(v) => { setCat(v); setPage(0); }}>
          <SelectTrigger className="w-[200px]"><SelectValue placeholder="Filter category" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All categories</SelectItem>
            {CATEGORIES.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
          </SelectContent>
        </Select>
        <span className="text-xs text-muted-foreground">{filtered.length} transactions</span>
      </div>

      <div className="overflow-x-auto rounded-md border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="cursor-pointer select-none" onClick={() => toggleSort("date")}>Date<SortIcon col="date" /></TableHead>
              <TableHead>Narration</TableHead>
              <TableHead>Category</TableHead>
              <TableHead className="cursor-pointer select-none text-right" onClick={() => toggleSort("amount")}>Amount<SortIcon col="amount" /></TableHead>
              <TableHead>Type</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {slice.map((t) => {
              const isIncome = (t.credit ?? 0) > 0;
              return (
                <TableRow key={t.id}>
                  <TableCell className="whitespace-nowrap text-xs">{formatDate(t.date)}</TableCell>
                  <TableCell className="max-w-[260px] truncate">{t.narration}</TableCell>
                  <TableCell><CategoryBadge category={t.category} /></TableCell>
                  <TableCell className={`text-right font-medium ${isIncome ? "text-success" : ""}`}>
                    {formatINR(isIncome ? (t.credit ?? 0) : (t.debit ?? 0))}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className={isIncome ? "border-success/40 text-success" : "border-destructive/30 text-destructive"}>
                      {isIncome ? "Income" : "Expense"}
                    </Badge>
                  </TableCell>
                </TableRow>
              );
            })}
            {slice.length === 0 && (
              <TableRow><TableCell colSpan={5} className="py-8 text-center text-sm text-muted-foreground">No transactions match this filter</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {pages > 1 && (
        <div className="mt-3 flex items-center justify-between text-sm">
          <span className="text-xs text-muted-foreground">Page {page + 1} of {pages}</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>Previous</Button>
            <Button variant="outline" size="sm" disabled={page >= pages - 1} onClick={() => setPage((p) => p + 1)}>Next</Button>
          </div>
        </div>
      )}
    </div>
  );
}
