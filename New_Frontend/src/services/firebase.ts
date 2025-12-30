import { initializeApp, getApps, type FirebaseApp } from "firebase/app";
import {
  getAuth,
  GoogleAuthProvider,
  createUserWithEmailAndPassword,
  getRedirectResult,
  sendEmailVerification,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signInWithPopup,
  signInWithRedirect,
  signOut,
  updateProfile,
  type Auth,
  type User,
} from "firebase/auth";

type FirebaseConfig = {
  apiKey?: string;
  authDomain?: string;
  projectId?: string;
  appId?: string;
  messagingSenderId?: string;
  storageBucket?: string;
};

function readFirebaseConfig(): FirebaseConfig {
  return {
    apiKey: (import.meta.env.VITE_FIREBASE_API_KEY as string | undefined) || undefined,
    authDomain: (import.meta.env.VITE_FIREBASE_AUTH_DOMAIN as string | undefined) || undefined,
    projectId: (import.meta.env.VITE_FIREBASE_PROJECT_ID as string | undefined) || undefined,
    appId: (import.meta.env.VITE_FIREBASE_APP_ID as string | undefined) || undefined,
    messagingSenderId: (import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID as string | undefined) || undefined,
    storageBucket: (import.meta.env.VITE_FIREBASE_STORAGE_BUCKET as string | undefined) || undefined,
  };
}

const firebaseConfig = readFirebaseConfig();

export const firebaseEnabled = Boolean(
  firebaseConfig.apiKey && firebaseConfig.authDomain && firebaseConfig.projectId && firebaseConfig.appId,
);

let firebaseApp: FirebaseApp | null = null;
let firebaseAuth: Auth | null = null;

function ensureFirebase(): Auth {
  if (!firebaseEnabled) {
    throw new Error("Firebase chưa được cấu hình (thiếu VITE_FIREBASE_*).");
  }

  if (!firebaseApp) {
    const apps = getApps();
    firebaseApp = apps.length > 0 ? apps[0]! : initializeApp(firebaseConfig);
  }
  if (!firebaseAuth) {
    firebaseAuth = getAuth(firebaseApp);
  }

  return firebaseAuth;
}

export function getFirebaseAuthOrNull(): Auth | null {
  if (!firebaseEnabled) return null;
  try {
    return ensureFirebase();
  } catch {
    return null;
  }
}

export async function firebaseSignInEmailPassword(email: string, password: string): Promise<User> {
  const auth = ensureFirebase();
  const cred = await signInWithEmailAndPassword(auth, email, password);
  return cred.user;
}

export async function firebaseSignUpEmailPassword(params: {
  email: string;
  password: string;
  displayName?: string;
  sendVerificationEmail?: boolean;
}): Promise<User> {
  const auth = ensureFirebase();
  const cred = await createUserWithEmailAndPassword(auth, params.email, params.password);

  if (params.displayName) {
    await updateProfile(cred.user, { displayName: params.displayName });
  }

  if (params.sendVerificationEmail) {
    try {
      await sendEmailVerification(cred.user);
    } catch {
      // ignore
    }
  }

  return cred.user;
}

export async function firebaseSendPasswordReset(email: string): Promise<void> {
  const auth = ensureFirebase();
  await sendPasswordResetEmail(auth, email);
}

export async function firebaseSignInGoogle(): Promise<User | null> {
  const auth = ensureFirebase();
  const provider = new GoogleAuthProvider();
  provider.setCustomParameters({ prompt: "select_account" });

  try {
    const cred = await signInWithPopup(auth, provider);
    return cred.user;
  } catch (err: any) {
    const code = String(err?.code || "");
    // On some mobile browsers popups are blocked; fall back to redirect.
    if (code === "auth/popup-blocked" || code === "auth/cancelled-popup-request") {
      await signInWithRedirect(auth, provider);
      return null;
    }
    throw err;
  }
}

export async function firebaseHandleRedirectResult(): Promise<User | null> {
  const auth = ensureFirebase();
  const res = await getRedirectResult(auth);
  return res?.user ?? null;
}

export async function firebaseGetIdToken(user?: User): Promise<string> {
  const auth = ensureFirebase();
  const current = user ?? auth.currentUser;
  if (!current) throw new Error("Chưa đăng nhập Firebase.");
  return current.getIdToken();
}

export async function firebaseSignOut(): Promise<void> {
  const auth = getFirebaseAuthOrNull();
  if (!auth) return;
  await signOut(auth);
}

