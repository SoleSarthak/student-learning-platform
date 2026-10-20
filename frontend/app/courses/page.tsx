"use client";

import Link from "next/link";
import { useState } from "react";
import type { Course } from "@/lib/types";
import { useFetch } from "@/lib/useFetch";

export default function CoursesPage() {
  const [search, setSearch] = useState("");
  const { data, error, loading } = useFetch<Course[]>("/courses?limit=100");

  const courses = data ?? [];

  const filtered = courses.filter((course) =>
    `${course.title} ${course.description}`
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  return (
    <main className="container section">
      <div className="section-heading">
        <div>
          <span className="eyebrow">COURSE CATALOG</span>
          <h2>Explore courses</h2>
          <p className="muted">Find your next learning opportunity.</p>
        </div>
      </div>

      <input
        className="search-input"
        placeholder="Search courses..."
        aria-label="Search courses"
        value={search}
        onChange={(event) => setSearch(event.target.value)}
      />

      {error && <div className="error">{error}</div>}
      {loading && <p className="muted">Loading courses...</p>}

      {!loading && !error && filtered.length === 0 && (
        <div className="empty-state" style={{ marginTop: 24 }}>
          <h3>No courses found</h3>
          <p>Try another search, or check back when courses are available.</p>
        </div>
      )}

      <div className="grid" style={{ marginTop: 24 }}>
        {filtered.map((course) => (
          <article className="card" key={course.id}>
            <div className="course-icon">📘</div>
            <span className="badge">{course.difficulty}</span>
            <h3>{course.title}</h3>
            <p>{course.description}</p>
            <Link className="primary-button" href={`/courses/${course.id}`}>
              View course →
            </Link>
          </article>
        ))}
      </div>
    </main>
  );
}
