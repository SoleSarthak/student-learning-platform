"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { apiRequest, errorMessage } from "@/lib/api";
import { useRequireAuth } from "@/lib/auth";
import type { Course, User } from "@/lib/types";
import { useFetch } from "@/lib/useFetch";

export default function InstructorPage() {
  const router = useRouter();
  const { ready, token } = useRequireAuth();

  const user = useFetch<User>(token ? "/auth/me" : null);
  const isStaff =
    user.data?.role === "instructor" || user.data?.role === "admin";

  const courses = useFetch<Course[]>(isStaff ? "/courses/mine" : null);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [difficulty, setDifficulty] = useState("beginner");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  // Students have no business here.
  useEffect(() => {
    if (user.data && !isStaff) {
      router.replace("/dashboard");
    }
  }, [user.data, isStaff, router]);

  async function createCourse(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSaving(true);

    try {
      const created = await apiRequest<Course>("/courses", {
        method: "POST",
        body: JSON.stringify({ title, description, difficulty }),
      });

      setTitle("");
      setDescription("");
      setDifficulty("beginner");
      router.push(`/instructor/courses/${created.id}`);
    } catch (err) {
      setError(errorMessage(err, "Could not create the course"));
    } finally {
      setSaving(false);
    }
  }

  if (!ready || !token || user.loading || !isStaff) {
    return (
      <main className="container section">
        <p className="muted">Loading...</p>
      </main>
    );
  }

  return (
    <main className="container section">
      <div className="section-heading">
        <div>
          <span className="eyebrow">INSTRUCTOR STUDIO</span>
          <h2>Your courses</h2>
          <p className="muted">
            Create a course, then add modules, lessons and quizzes to it.
          </p>
        </div>
      </div>

      <div className="two-column">
        <section>
          {courses.error && <div className="error">{courses.error}</div>}

          {courses.data && courses.data.length === 0 && (
            <div className="empty-state">
              You have not created a course yet. Use the form to start one.
            </div>
          )}

          {courses.data?.map((course) => (
            <div className="card stack-item row" key={course.id}>
              <div>
                <span className="badge">{course.difficulty}</span>
                <h3 style={{ margin: "10px 0 0" }}>{course.title}</h3>
              </div>

              <Link
                className="secondary-button"
                href={`/instructor/courses/${course.id}`}
              >
                Manage
              </Link>
            </div>
          ))}
        </section>

        <form className="panel" onSubmit={createCourse}>
          <h3>Create a new course</h3>

          {error && <div className="error">{error}</div>}

          <label htmlFor="title">Title</label>
          <input
            id="title"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            maxLength={200}
            required
          />

          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            rows={5}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            maxLength={5000}
            required
          />

          <label htmlFor="difficulty">Difficulty</label>
          <select
            id="difficulty"
            value={difficulty}
            onChange={(event) => setDifficulty(event.target.value)}
          >
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>

          <button className="primary-button" disabled={saving}>
            {saving ? "Creating..." : "Create course"}
          </button>
        </form>
      </div>
    </main>
  );
}
