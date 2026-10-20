"use client";

import { useCallback, useEffect, useState } from "react";
import { apiRequest, errorMessage } from "@/lib/api";

interface Settled<T> {
  key: string;
  endpoint: string;
  data: T | null;
  error: string;
}

/**
 * Load JSON from the API.
 *
 * - Pass `null` as the endpoint to skip the request (e.g. not logged in yet).
 * - `reload()` fetches again and keeps showing the old data meanwhile.
 */
export function useFetch<T>(endpoint: string | null) {
  const [version, setVersion] = useState(0);
  const [settled, setSettled] = useState<Settled<T> | null>(null);

  const key = endpoint === null ? null : `${endpoint}#${version}`;

  useEffect(() => {
    if (endpoint === null || key === null) return;

    let active = true;

    apiRequest<T>(endpoint)
      .then((data) => {
        if (active) setSettled({ key, endpoint, data, error: "" });
      })
      .catch((err: unknown) => {
        if (active) {
          setSettled({ key, endpoint, data: null, error: errorMessage(err) });
        }
      });

    return () => {
      active = false;
    };
  }, [endpoint, key]);

  const reload = useCallback(() => setVersion((value) => value + 1), []);

  const current =
    settled !== null && settled.endpoint === endpoint ? settled : null;

  return {
    data: current?.data ?? null,
    error: current?.error ?? "",
    loading: key !== null && settled?.key !== key,
    reload,
  };
}
