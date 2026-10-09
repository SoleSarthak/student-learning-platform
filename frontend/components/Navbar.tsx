"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

export default function Navbar() {
  const router = useRouter();

  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("access_token")
      : null;

  function logout() {
    localStorage.removeItem("access_token");
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