import {
  collection,
  deleteDoc,
  doc,
  getDoc,
  getDocs,
  orderBy,
  query,
  serverTimestamp,
  setDoc,
  Timestamp,
  updateDoc,
} from "firebase/firestore";
import { db, firebaseConfigured } from "./firebase";
import type { SessionMeta } from "./types";

type FirestoreSessionMeta = {
  task_id: string;
  uid: string;
  bank_name: string;
  statement_period?: string;
  total_income: number;
  total_expenses: number;
  net_savings: number;
  health_score: number;
  health_grade: string;
  status: "pending" | "processing" | "done" | "failed";
  created_at: Timestamp;
  expires_at: Timestamp;
};

type FirestoreUserProfile = {
  uid: string;
  displayName: string | null;
  email: string | null;
  photoURL: string | null;
  created_at: ReturnType<typeof serverTimestamp>;
};

const LS_KEY = (uid: string) => `finsight:sessions:${uid}`;

function readLocal(uid: string): SessionMeta[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(LS_KEY(uid)) ?? "[]");
  } catch {
    return [];
  }
}

function writeLocal(uid: string, list: SessionMeta[]) {
  if (typeof window === "undefined") return;
  localStorage.setItem(LS_KEY(uid), JSON.stringify(list));
}

function toMillis(value: number | Timestamp): number {
  return value instanceof Timestamp ? value.toMillis() : value;
}

function fromDbSession(data: FirestoreSessionMeta): SessionMeta {
  return {
    task_id: data.task_id,
    bank_name: data.bank_name,
    created_at: data.created_at.toMillis(),
    health_score: data.health_score,
    health_grade: data.health_grade,
    total_income: data.total_income,
    total_expenses: data.total_expenses,
    net_savings: data.net_savings,
    status: data.status,
  };
}

function toDbSession(uid: string, meta: SessionMeta & Partial<Pick<FirestoreSessionMeta, "statement_period">>): FirestoreSessionMeta {
  const createdAt = Timestamp.fromMillis(toMillis(meta.created_at));
  const expiresAt = Timestamp.fromMillis(createdAt.toMillis() + 24 * 60 * 60 * 1000);

  return {
    task_id: meta.task_id,
    uid,
    bank_name: meta.bank_name,
    statement_period: meta.statement_period,
    total_income: meta.total_income,
    total_expenses: meta.total_expenses,
    net_savings: meta.net_savings,
    health_score: meta.health_score,
    health_grade: meta.health_grade,
    status: meta.status,
    created_at: createdAt,
    expires_at: expiresAt,
  };
}

function getDbOrThrow() {
  if (!db) throw new Error("Firebase is not configured");
  return db;
}

export async function createUserProfileIfNew(
  uid: string,
  displayName: string | null,
  email: string | null,
  photoURL: string | null,
): Promise<void> {
  if (!firebaseConfigured || !db) return;
  const ref = doc(getDbOrThrow(), "users", uid);
  const snap = await getDoc(ref);
  if (!snap.exists()) {
    const profile: FirestoreUserProfile = {
      uid,
      displayName,
      email,
      photoURL,
      created_at: serverTimestamp(),
    };
    await setDoc(ref, profile);
  }
}

export async function createSession(uid: string, task_id: string): Promise<void> {
  if (!firebaseConfigured || !db) return;
  const ref = doc(getDbOrThrow(), "users", uid, "sessions", task_id);
  const now = new Date();
  const expires = new Date(now.getTime() + 24 * 60 * 60 * 1000);

  await setDoc(ref, {
    task_id,
    uid,
    bank_name: "Processing...",
    total_income: 0,
    total_expenses: 0,
    net_savings: 0,
    health_score: 0,
    health_grade: "",
    status: "pending",
    created_at: Timestamp.fromDate(now),
    expires_at: Timestamp.fromDate(expires),
  } satisfies FirestoreSessionMeta);
}

export async function updateSessionWithResults(
  uid: string,
  task_id: string,
  data: Partial<Omit<FirestoreSessionMeta, "task_id" | "uid" | "created_at" | "expires_at">>,
): Promise<void> {
  if (!firebaseConfigured || !db) return;
  const ref = doc(getDbOrThrow(), "users", uid, "sessions", task_id);
  await updateDoc(ref, {
    ...data,
    status: "done",
  });
}

export async function markSessionFailed(uid: string, task_id: string): Promise<void> {
  if (!firebaseConfigured || !db) return;
  const ref = doc(getDbOrThrow(), "users", uid, "sessions", task_id);
  await updateDoc(ref, { status: "failed" });
}

export async function getUserSessions(uid: string): Promise<SessionMeta[]> {
  if (firebaseConfigured && db) {
    try {
      const q = query(collection(getDbOrThrow(), "users", uid, "sessions"), orderBy("created_at", "desc"));
      const snap = await getDocs(q);
      return snap.docs.map((d) => fromDbSession(d.data() as FirestoreSessionMeta));
    } catch (e) {
      console.warn("Firestore unavailable, using local cache", e);
    }
  }
  return readLocal(uid);
}

export async function getSession(uid: string, task_id: string): Promise<SessionMeta | null> {
  if (firebaseConfigured && db) {
    try {
      const snap = await getDoc(doc(getDbOrThrow(), "users", uid, "sessions", task_id));
      return snap.exists() ? fromDbSession(snap.data() as FirestoreSessionMeta) : null;
    } catch (e) {
      console.warn("Firestore unavailable, using local cache", e);
    }
  }
  return readLocal(uid).find((session) => session.task_id === task_id) ?? null;
}

export async function deleteSession(uid: string, task_id: string): Promise<void> {
  if (!firebaseConfigured || !db) return;
  await deleteDoc(doc(getDbOrThrow(), "users", uid, "sessions", task_id));
}

export async function saveSession(uid: string, meta: SessionMeta): Promise<void> {
  const list = readLocal(uid).filter((session) => session.task_id !== meta.task_id);
  list.unshift(meta);
  writeLocal(uid, list.slice(0, 100));

  if (firebaseConfigured && db) {
    const ref = doc(getDbOrThrow(), "users", uid, "sessions", meta.task_id);
    const existing = await getDoc(ref);
    const payload = existing.exists()
      ? {
          task_id: meta.task_id,
          uid,
          bank_name: meta.bank_name,
          total_income: meta.total_income,
          total_expenses: meta.total_expenses,
          net_savings: meta.net_savings,
          health_score: meta.health_score,
          health_grade: meta.health_grade,
          status: meta.status,
        }
      : toDbSession(uid, meta);
    await setDoc(ref, payload, { merge: true });
  }
}

export async function listSessions(uid: string): Promise<SessionMeta[]> {
  return getUserSessions(uid);
}
