"use client";

import Link from "next/link";
import ProgressBar from "@/components/ProgressBar";
import { useRequireAuth } from "@/lib/auth";
import type { Course, Enrollment, Progress, User } from "@/lib/types";
import { useFetch } from "@/lib/useFetch";

function EnrolledCourseCard({ courseId }: { courseId: number }) {
  const course = useFetch<Course>(`/courses/${courseId}`);
  const progress = useFetch<Progress>(`/progress/courses/${courseId}`);

  if (course.loading) {
    return (
      <article className="card">
        <p className="muted">Loading...</p>
      </article>
    );
  }

  if (!course.data) {
    return null;
  }

  const percent = progress.data?.progress_percentage ?? 0;
  const finished = percent >= 100;

  return (
    <article className="card">
      <div className="course-icon">{finished ? "🏆" : "📘"}</div>
      <span className="badge">{course.data.difficulty}</span>
      <h3>{course.data.title}</h3>

      <ProgressBar value={percent} />
      <p className="muted" style={{ marginTop: 8 }}>
        {progress.data
          ? `${progress.data.completed_lessons} of ${progress.data.total_lessons} lessons - ${Math.round(percent)}%`
          : "Loading progress..."}
      </p>

      <Link className="primary-button" href={`/courses/${courseId}`}>
        {finished ? "Review course" : "Continue learning"}
      </Link>
    </article>
  );
}

export default function DashboardPage() {
  const { ready, token } = useRequireAuth();

  const user = useFetch<User>(token ? "/auth/me" : null);
  const enrollments = useFetch<Enrollment[]>(token ? "/enrollments" : null);

  if (!ready || !token || user.loading) {
    return (
      <main className="container section">
        <p className="muted">Loading dashboard...</p>
      </main>
    );
  }

  if (!user.data) {
    return (
      <main className="container section">
        <div className="error">{user.error || "Please log in again."}</div>
      </main>
    );
  }

  const isStaff = user.data.role === "instructor" || user.data.role === "admin";
  const items = enrollments.data ?? [];

  return (
    <main className="container">
      <header className="dashboard-header">
        <span className="eyebrow">YOUR DASHBOARD</span>
        <h1>Welcome, {user.data.name}</h1>
        <p className="muted">Continue learning and keep building momentum.</p>

        <div className="course-actions">
          <Link className="primary-button" href="/courses">
            Browse courses
          </Link>
          <Link className="secondary-button" href="/certificates">
            My certificates
          </Link>
          {isStaff && (
            <Link className="secondary-button" href="/instructor">
              Instructor studio
            </Link>
          )}
        </div>
      </header>

      {enrollments.error && <div className="error">{enrollments.error}</div>}

      <section className="section">
        <h2>My courses</h2>

        {!enrollments.loading && items.length === 0 && (
          <div className="empty-state">
            <h3>You have not enrolled in any course yet</h3>
            <p>Pick a course and start learning today.</p>
            <Link className="primary-button" href="/courses">
              Explore courses
            </Link>
          </div>
        )}

        <div className="grid">
          {items.map((enrollment) => (
            <EnrolledCourseCard
              key={enrollment.id}
              courseId={enrollment.course_id}
            />
          ))}
        </div>
      </section>
    </main>
  );
}
