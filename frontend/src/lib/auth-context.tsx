import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  GoogleAuthProvider,
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  updateProfile,
  type User,
} from "firebase/auth";
import { firebaseConfigured, getFirebaseAuth } from "./firebase";
import { createUserProfileIfNew } from "./sessions";

type AuthUser = {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoURL: string | null;
};

interface AuthCtx {
  user: AuthUser | null;
  loading: boolean;
  isMock: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, name: string) => Promise<void>;
  signInGoogle: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  logout: () => Promise<void>;
}

const Ctx = createContext<AuthCtx | null>(null);

const MOCK_KEY = "finsight:mock-user";

function toAuthUser(u: User): AuthUser {
  return { uid: u.uid, email: u.email, displayName: u.displayName, photoURL: u.photoURL };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const isMock = !firebaseConfigured;
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isMock) {
      try {
        const raw = typeof window !== "undefined" ? localStorage.getItem(MOCK_KEY) : null;
        if (raw) setUser(JSON.parse(raw));
      } catch {}
      setLoading(false);
      return;
    }
    const auth = getFirebaseAuth()!;
    const unsub = onAuthStateChanged(auth, (u) => {
      if (u) {
        void createUserProfileIfNew(u.uid, u.displayName, u.email, u.photoURL);
      }
      setUser(u ? toAuthUser(u) : null);
      setLoading(false);
    });
    return () => unsub();
  }, [isMock]);

  const value = useMemo<AuthCtx>(() => {
    const mockSet = (u: AuthUser | null) => {
      setUser(u);
      if (typeof window !== "undefined") {
        if (u) localStorage.setItem(MOCK_KEY, JSON.stringify(u));
        else localStorage.removeItem(MOCK_KEY);
      }
    };
    if (isMock) {
      return {
        user,
        loading,
        isMock,
        async signIn(email) {
          mockSet({ uid: `mock_${email}`, email, displayName: email.split("@")[0], photoURL: null });
        },
        async signUp(email, _pw, name) {
          mockSet({ uid: `mock_${email}`, email, displayName: name || email.split("@")[0], photoURL: null });
        },
        async signInGoogle() {
          mockSet({ uid: "mock_google", email: "demo@finsight.ai", displayName: "Demo User", photoURL: null });
        },
        async resetPassword() {},
        async logout() { mockSet(null); },
      };
    }
    const auth = getFirebaseAuth()!;
    return {
      user,
      loading,
      isMock,
      async signIn(email, password) {
        await signInWithEmailAndPassword(auth, email, password);
      },
      async signUp(email, password, name) {
        const cred = await createUserWithEmailAndPassword(auth, email, password);
        if (name) await updateProfile(cred.user, { displayName: name });
        await createUserProfileIfNew(cred.user.uid, name || cred.user.displayName, cred.user.email, cred.user.photoURL);
      },
      async signInGoogle() {
        const cred = await signInWithPopup(auth, new GoogleAuthProvider());
        await createUserProfileIfNew(cred.user.uid, cred.user.displayName, cred.user.email, cred.user.photoURL);
      },
      async resetPassword(email) {
        await sendPasswordResetEmail(auth, email);
      },
      async logout() {
        await signOut(auth);
      },
    };
  }, [user, loading, isMock]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
