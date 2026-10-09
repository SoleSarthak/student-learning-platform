"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api";

export default function InstructorPage() {
  const router = useRouter();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [difficulty, setDifficulty] = useState("beginner");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    apiRequest("/auth/me")
      .then((user) => {
        if (!["instructor", "admin"].includes(user.role)) {
          router.replace("/dashboard");
        }
      })
      .catch(() => router.replace("/login"));
  }, [router]);

  async function createCourse(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setError("");

    try {
      const course = await apiRequest("/courses", {
        method: "POST",
        body: JSON.stringify({ title, description, difficulty }),
      });

      setMessage(`Course "${course.title}" created successfully.`);
      setTitle("");
      setDescription("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Course creation failed");
    }
  }

  return (
    <main className="container section">
      <span className="eyebrow">INSTRUCTOR WORKSPACE</span>
      <h1>Create a course</h1>
      <p className="muted">
        Publish structured learning content for your students.
      </p>

      <form className="form-card" onSubmit={createCourse}>
        {error && <div className="error">{error}</div>}
        {message && <div className="success">{message}</div>}

        <label htmlFor="title">Course title</label>
        <input
          id="title"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          required
        />

        <label htmlFor="description">Description</label>
        <textarea
          id="description"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          rows={5}
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

        <button className="primary-button" type="submit">
          Create course
        </button>
      </form>
    </main>
  );
}