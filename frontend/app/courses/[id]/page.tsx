"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import ProgressBar from "@/components/ProgressBar";
import { apiRequest, errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type {
  Course,
  Enrollment,
  ModuleOutline,
  Progress,
  Quiz,
  User,
} from "@/lib/types";
import { useFetch } from "@/lib/useFetch";

export default function CourseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const courseId = Number(id);
  const { token } = useAuth();

  const course = useFetch<Course>(`/courses/${id}`);
  const outline = useFetch<ModuleOutline[]>(`/courses/${id}/outline`);
  const quizzes = useFetch<Quiz[]>(`/quizzes/courses/${id}`);
  const me = useFetch<User>(token ? "/auth/me" : null);
  const enrollments = useFetch<Enrollment[]>(token ? "/enrollments" : null);

  const enrolled =
    enrollments.data?.some((item) => item.course_id === courseId) ?? false;

  const progress = useFetch<Progress>(
    enrolled ? `/progress/courses/${id}` : null
  );

  const isOwner =
    !!me.data &&
    !!course.data &&
    (me.data.role === "admin" || me.data.id === course.data.instructor_id);

  const canOpenContent = enrolled || isOwner;

  const [enrolling, setEnrolling] = useState(false);
  const [actionError, setActionError] = useState("");

  async function enroll() {
    setActionError("");
    setEnrolling(true);

    try {
      await apiRequest(`/enrollments/courses/${id}`, { method: "POST" });
      enrollments.reload();
    } catch (err) {
      setActionError(errorMessage(err, "Could not enroll"));
    } finally {
      setEnrolling(false);
    }
  }

  if (course.loading) {
    return (
      <main className="container section">
        <p className="muted">Loading course...</p>
      </main>
    );
  }

  if (course.error || !course.data) {
    return (
      <main className="container section">
        <div className="error">{course.error || "Course not found"}</div>
        <Link href="/courses">← Back to courses</Link>
      </main>
    );
  }

  const completed = new Set(progress.data?.completed_lesson_ids ?? []);

  return (
    <main className="container section">
      <Link href="/courses" className="muted">
        ← All courses
      </Link>

      <header className="dashboard-header">
        <span className="badge">{course.data.difficulty}</span>
        <h1>{course.data.title}</h1>
        <p className="muted">{course.data.description}</p>

        {actionError && <div className="error">{actionError}</div>}

        <div className="course-actions">
          {!token && (
            <Link className="primary-button" href="/login">
              Log in to enroll
            </Link>
          )}

          {token && !enrolled && !enrollments.loading && (
            <button
              className="primary-button"
              onClick={enroll}
              disabled={enrolling}
            >
              {enrolling ? "Enrolling..." : "Enroll in this course"}
            </button>
          )}

          {enrolled && <span className="badge">✓ You are enrolled</span>}

          {isOwner && (
            <Link
              className="secondary-button"
              href={`/instructor/courses/${id}`}
            >
              Manage course
            </Link>
          )}
        </div>
      </header>

      {progress.data && (
        <section className="card" style={{ marginBottom: 24 }}>
          <strong>
            {progress.data.completed_lessons} of {progress.data.total_lessons}{" "}
            lessons completed ({Math.round(progress.data.progress_percentage)}%)
          </strong>
          <ProgressBar value={progress.data.progress_percentage} />
        </section>
      )}

      <section>
        <h2>Syllabus</h2>

        {outline.loading && <p className="muted">Loading syllabus...</p>}
        {outline.error && <div className="error">{outline.error}</div>}

        {outline.data && outline.data.length === 0 && (
          <div className="empty-state">No lessons have been added yet.</div>
        )}

        {outline.data?.map((module) => (
          <div className="card stack-item" key={module.id}>
            <h3>{module.title}</h3>

            {module.lessons.length === 0 && (
              <p className="muted">No lessons in this module yet.</p>
            )}

            <ul className="lesson-list">
              {module.lessons.map((lesson) => (
                <li className="lesson-item" key={lesson.id}>
                  {canOpenContent ? (
                    <Link href={`/lessons/${lesson.id}`}>
                      <span aria-hidden="true">
                        {completed.has(lesson.id) ? "✅" : "▶️"}
                      </span>{" "}
                      {lesson.title}
                    </Link>
                  ) : (
                    <span className="muted">
                      <span aria-hidden="true">🔒</span> {lesson.title}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        ))}

        {!canOpenContent && outline.data && outline.data.length > 0 && (
          <p className="muted">Enroll to unlock the lessons and quizzes.</p>
        )}
      </section>

      {quizzes.data && quizzes.data.length > 0 && (
        <section style={{ marginTop: 32 }}>
          <h2>Quizzes</h2>

          {quizzes.data.map((quiz) => (
            <div className="card stack-item row" key={quiz.id}>
              <div>
                <h3 style={{ margin: 0 }}>{quiz.title}</h3>
                <p className="muted" style={{ margin: "6px 0 0" }}>
                  Pass mark: {quiz.passing_score}%
                </p>
              </div>

              {canOpenContent ? (
                <Link className="secondary-button" href={`/quizzes/${quiz.id}`}>
                  Take quiz
                </Link>
              ) : (
                <span className="muted">🔒 Enroll first</span>
              )}
            </div>
          ))}
        </section>
      )}
    </main>
  );
}
