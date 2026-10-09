"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";

interface Course {
  id: number;
  title: string;
  description: string;
  difficulty: string;
  instructor_id: number;
}

interface Module {
  id: number;
  title: string;
  order: number;
  course_id: number;
}

export default function CourseDetailsPage() {
  const params = useParams<{ id: string }>();
  const courseId = params.id;

  const [course, setCourse] = useState<Course | null>(null);
  const [modules, setModules] = useState<Module[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const courseData = await apiRequest(`/courses/${courseId}`);
        setCourse(courseData);

        try {
          const moduleData = await apiRequest(
            `/courses/${courseId}/modules`
          );
          setModules(moduleData);
        } catch {
          setModules([]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load course");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [courseId]);

  async function enroll() {
    setMessage("");
    setError("");

    try {
      await apiRequest(`/courses/${courseId}/enroll`, {
        method: "POST",
      });
      setMessage("You are now enrolled in this course.");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Log in before enrolling in a course."
      );
    }
  }

  if (loading) return <main className="container section">Loading course...</main>;
  if (error && !course) return <main className="container section"><div className="error">{error}</div></main>;
  if (!course) return null;

  return (
    <main className="container section">
      <Link href="/courses" className="muted">← All courses</Link>

      <section className="hero-panel" style={{ marginTop: 22 }}>
        <span className="badge">{course.difficulty}</span>
        <h1>{course.title}</h1>
        <p>{course.description}</p>
        <p className="muted">Instructor ID: {course.instructor_id}</p>

        <div className="course-actions">
          <button className="primary-button" onClick={enroll}>
            Enroll in course
          </button>
        </div>

        {message && <p className="success">{message}</p>}
        {error && <p className="error">{error}</p>}
      </section>

      <section className="section">
        <h2>Course modules</h2>

        {modules.length === 0 ? (
          <div className="empty-state">
            No modules are available for this course yet.
          </div>
        ) : (
          <div className="grid">
            {modules.map((module) => (
              <article className="card" key={module.id}>
                <span className="badge">Module {module.order}</span>
                <h3>{module.title}</h3>
                <Link
                  href={`/lessons/${module.id}`}
                  className="secondary-button"
                >
                  View lessons
                </Link>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}