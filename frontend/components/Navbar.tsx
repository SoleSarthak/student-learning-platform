"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { clearToken, useAuth } from "@/lib/auth";
import type { User } from "@/lib/types";
import { useFetch } from "@/lib/useFetch";

export default function Navbar() {
  const router = useRouter();
  const { token } = useAuth();
  const { data: user } = useFetch<User>(token ? "/auth/me" : null);

  const isStaff = user?.role === "instructor" || user?.role === "admin";

  function logout() {
    clearToken();
    router.push("/login");
  }

  return (
    <nav className="navbar">
      <Link href="/" className="brand">
        Learn<span>Sphere</span>
      </Link>

      <div className="nav-links">
        <Link href="/courses">Explore courses</Link>

        {token ? (
          <>
            <Link href="/dashboard">Dashboard</Link>
            {isStaff && <Link href="/instructor">Instructor</Link>}
            <button className="nav-button" onClick={logout}>
              Log out
            </button>
          </>
        ) : (
          <>
            <Link href="/login">Log in</Link>
            <Link href="/register" className="nav-cta">
              Get started
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}
