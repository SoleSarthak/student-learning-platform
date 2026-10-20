"use client";

import { useRouter } from "next/navigation";
import { useEffect, useSyncExternalStore } from "react";

const TOKEN_KEY = "access_token";
const AUTH_EVENT = "auth-change";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;

  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
  window.dispatchEvent(new Event(AUTH_EVENT));
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
  window.dispatchEvent(new Event(AUTH_EVENT));
}

function subscribe(callback: () => void): () => void {
  window.addEventListener(AUTH_EVENT, callback);
  window.addEventListener("storage", callback); // other tabs

  return () => {
    window.removeEventListener(AUTH_EVENT, callback);
    window.removeEventListener("storage", callback);
  };
}

function subscribeNever(): () => void {
  return () => {};
}

/**
 * `token` is always null on the server and during hydration, so the server
 * and browser render the same HTML. `ready` flips to true once we are
 * running in the browser and `token` can be trusted.
 */
export function useAuth(): { ready: boolean; token: string | null } {
  const token = useSyncExternalStore(subscribe, getToken, () => null);
  const ready = useSyncExternalStore(
    subscribeNever,
    () => true,
    () => false
  );

  return { ready, token };
}

/** Same as useAuth, but sends logged-out visitors to the login page. */
export function useRequireAuth(): { ready: boolean; token: string | null } {
  const router = useRouter();
  const auth = useAuth();

  useEffect(() => {
    if (auth.ready && !auth.token) {
      router.replace("/login");
    }
  }, [auth.ready, auth.token, router]);

  return auth;
}
