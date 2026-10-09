"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api";

interface User {
  id: number;
  name: string;
  email: string;
  role: string;
}

interface Enrollment {
  id: number;
  course_id: number;
  student_id: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const [currentUser, myEnrollments] = await Promise.all([
          apiRequest("/auth/me"),
          apiRequest("/enrollments"),
        ]);

        setUser(currentUser);
        setEnrollments(myEnrollments);
      } catch {
        localStorage.removeItem("access_token");
        router.replace("/login");
      }
    }

    load();
  }, [router]);

  if (!user) {
    return <main className="container section">Loading dashboard...</main>;
  }

  return (
    <main className="container">
      <header className="dashboard-header">
        <span className="eyebrow">YOUR DASHBOARD</span>
        <h1>Welcome, {user.name}</h1>
        <p className="muted">
          Continue learning and keep building momentum.
        </p>
      </header>

      {error && <div className="error">{error}</div>}

      <section className="grid">
        <article className="card">
          <div className="course-icon">📚</div>
          <h3>My courses</h3>
          <p>You are enrolled in {enrollments.length} course(s).</p>
          <Link className="primary-button" href="/courses">
            Explore courses
          </Link>
        </article>

        <article className="card">
          <div className="course-icon">🏆</div>
          <h3>Certificates</h3>
          <p>View certificates earned from your learning.</p>
          <Link className="secondary-button" href="/certificates">
            My certificates
          </Link>
        </article>

        {user.role === "instructor" || user.role === "admin" ? (
          <article className="card">
            <div className="course-icon">🎓</div>
            <h3>Instructor tools</h3>
            <p>Manage learning content and courses.</p>
            <Link className="secondary-button" href="/instructor">
              Open instructor area
            </Link>
          </article>
        ) : (
          <article className="card">
            <div className="course-icon">👤</div>
            <h3>Your profile</h3>
            <p>{user.email}</p>
            <span className="badge">{user.role}</span>
          </article>
        )}
      </section>
    </main>
  );
}