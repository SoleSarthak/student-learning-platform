"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import ProgressBar from "@/components/ProgressBar";
import { apiRequest, errorMessage } from "@/lib/api";
import { useRequireAuth } from "@/lib/auth";
import type {
  LessonCompleteResult,
  LessonDetail,
  ModuleOutline,
  Progress,
} from "@/lib/types";
import { useFetch } from "@/lib/useFetch";

export default function LessonPage() {
  const { id } = useParams<{ id: string }>();
  const lessonId = Number(id);
  const { ready, token } = useRequireAuth();

  const lesson = useFetch<LessonDetail>(token ? `/lessons/${id}` : null);
  const courseId = lesson.data?.course_id;

  const outline = useFetch<ModuleOutline[]>(
    courseId ? `/courses/${courseId}/outline` : null
  );
  const progress = useFetch<Progress>(
    courseId ? `/progress/courses/${courseId}` : null
  );

  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [actionError, setActionError] = useState("");
  const [certificate, setCertificate] = useState<string | null>(null);

  async function markComplete() {
    setActionError("");
    setMessage("");
    setSaving(true);

    try {
      const result = await apiRequest<LessonCompleteResult>(
        `/progress/lessons/${id}/complete`,
        { method: "POST" }
      );

      setMessage("Lesson marked as complete.");
      setCertificate(result.certificate_number);
      progress.reload();
    } catch (err) {
      setActionError(errorMessage(err, "Could not save your progress"));
    } finally {
      setSaving(false);
    }
  }

  if (!ready || !token || lesson.loading) {
    return (
      <main className="container section">
        <p className="muted">Loading lesson...</p>
      </main>
    );
  }

  if (lesson.error || !lesson.data) {
    return (
      <main className="container section">
        <div className="error">{lesson.error || "Lesson not found"}</div>
        <Link href="/courses">← Back to courses</Link>
      </main>
    );
  }

  const lessons = outline.data?.flatMap((module) => module.lessons) ?? [];
  const position = lessons.findIndex((item) => item.id === lessonId);
  const previous = position > 0 ? lessons[position - 1] : null;
  const next =
    position >= 0 && position < lessons.length - 1
      ? lessons[position + 1]
      : null;

  const isDone = progress.data?.completed_lesson_ids.includes(lessonId);

  return (
    <main className="container section page-narrow">
      <Link href={`/courses/${lesson.data.course_id}`} className="muted">
        ← Back to course
      </Link>

      {progress.data && (
        <div style={{ margin: "18px 0" }}>
          <ProgressBar value={progress.data.progress_percentage} />
          <small className="muted">
            {progress.data.completed_lessons} of {progress.data.total_lessons}{" "}
            lessons complete
          </small>
        </div>
      )}

      <h1>{lesson.data.title}</h1>

      {lesson.data.video_url && (
        <p>
          <a
            className="secondary-button"
            href={lesson.data.video_url}
            target="_blank"
            rel="noopener noreferrer"
          >
            ▶ Watch the video
          </a>
        </p>
      )}

      {/* Rendered as plain text (never as HTML), so lesson content can not inject scripts. */}
      <article className="card lesson-content">{lesson.data.content}</article>

      {actionError && <div className="error">{actionError}</div>}
      {message && <div className="success">{message}</div>}

      {certificate && (
        <div className="success" style={{ marginTop: 12 }}>
          🏆 Course complete! Your certificate is ready:{" "}
          <Link href="/certificates">view certificates</Link>
        </div>
      )}

      <div className="course-actions">
        <button
          className="primary-button"
          onClick={markComplete}
          disabled={saving || isDone}
        >
          {isDone ? "✓ Completed" : saving ? "Saving..." : "Mark as complete"}
        </button>

        {previous && (
          <Link className="secondary-button" href={`/lessons/${previous.id}`}>
            ← Previous
          </Link>
        )}

        {next && (
          <Link className="secondary-button" href={`/lessons/${next.id}`}>
            Next →
          </Link>
        )}
      </div>
    </main>
  );
}
