"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { apiRequest, errorMessage } from "@/lib/api";
import { useRequireAuth } from "@/lib/auth";
import type { Course, ModuleOutline, Question, Quiz } from "@/lib/types";
import { useFetch } from "@/lib/useFetch";

/* ---------- small forms ---------- */

function AddModuleForm({
  courseId,
  nextOrder,
  onDone,
}: {
  courseId: string;
  nextOrder: number;
  onDone: () => void;
}) {
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSaving(true);

    try {
      await apiRequest(`/courses/${courseId}/modules`, {
        method: "POST",
        body: JSON.stringify({ title, order: nextOrder }),
      });

      setTitle("");
      onDone();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="panel" onSubmit={submit}>
      <h3>Add a module</h3>
      {error && <div className="error">{error}</div>}

      <label htmlFor="module-title">Module title</label>
      <input
        id="module-title"
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        maxLength={200}
        required
      />

      <button className="primary-button" disabled={saving}>
        {saving ? "Adding..." : "Add module"}
      </button>
    </form>
  );
}

function AddLessonForm({
  moduleId,
  nextOrder,
  onDone,
}: {
  moduleId: number;
  nextOrder: number;
  onDone: () => void;
}) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [videoUrl, setVideoUrl] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSaving(true);

    try {
      await apiRequest(`/modules/${moduleId}/lessons`, {
        method: "POST",
        body: JSON.stringify({
          title,
          content,
          order: nextOrder,
          video_url: videoUrl.trim() || null,
        }),
      });

      setTitle("");
      setContent("");
      setVideoUrl("");
      onDone();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="panel nested" onSubmit={submit}>
      <h4>Add a lesson</h4>
      {error && <div className="error">{error}</div>}

      <label htmlFor={`lesson-title-${moduleId}`}>Lesson title</label>
      <input
        id={`lesson-title-${moduleId}`}
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        maxLength={200}
        required
      />

      <label htmlFor={`lesson-content-${moduleId}`}>Content</label>
      <textarea
        id={`lesson-content-${moduleId}`}
        rows={5}
        value={content}
        onChange={(event) => setContent(event.target.value)}
        required
      />

      <label htmlFor={`lesson-video-${moduleId}`}>Video link (optional)</label>
      <input
        id={`lesson-video-${moduleId}`}
        type="url"
        placeholder="https://..."
        value={videoUrl}
        onChange={(event) => setVideoUrl(event.target.value)}
      />

      <button className="secondary-button" disabled={saving}>
        {saving ? "Adding..." : "Add lesson"}
      </button>
    </form>
  );
}

function AddQuestionForm({
  quizId,
  onDone,
}: {
  quizId: number;
  onDone: () => void;
}) {
  const [text, setText] = useState("");
  const [options, setOptions] = useState(["", "", "", ""]);
  const [correct, setCorrect] = useState("A");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSaving(true);

    try {
      await apiRequest(`/quizzes/${quizId}/questions`, {
        method: "POST",
        body: JSON.stringify({
          question_text: text,
          option_a: options[0],
          option_b: options[1],
          option_c: options[2],
          option_d: options[3],
          correct_answer: correct,
        }),
      });

      setText("");
      setOptions(["", "", "", ""]);
      setCorrect("A");
      onDone();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="panel nested" onSubmit={submit}>
      <h4>Add a question</h4>
      {error && <div className="error">{error}</div>}

      <label htmlFor={`q-text-${quizId}`}>Question</label>
      <input
        id={`q-text-${quizId}`}
        value={text}
        onChange={(event) => setText(event.target.value)}
        maxLength={1000}
        required
      />

      {["A", "B", "C", "D"].map((letter, index) => (
        <div key={letter}>
          <label htmlFor={`q-${quizId}-${letter}`}>Option {letter}</label>
          <input
            id={`q-${quizId}-${letter}`}
            value={options[index]}
            onChange={(event) =>
              setOptions((current) =>
                current.map((value, i) =>
                  i === index ? event.target.value : value
                )
              )
            }
            maxLength={500}
            required
          />
        </div>
      ))}

      <label htmlFor={`q-correct-${quizId}`}>Correct answer</label>
      <select
        id={`q-correct-${quizId}`}
        value={correct}
        onChange={(event) => setCorrect(event.target.value)}
      >
        <option value="A">A</option>
        <option value="B">B</option>
        <option value="C">C</option>
        <option value="D">D</option>
      </select>

      <button className="secondary-button" disabled={saving}>
        {saving ? "Adding..." : "Add question"}
      </button>
    </form>
  );
}

function QuizManager({ quiz }: { quiz: Quiz }) {
  const questions = useFetch<Question[]>(`/quizzes/${quiz.id}/questions`);

  return (
    <div className="card stack-item">
      <h3>{quiz.title}</h3>
      <p className="muted">
        Pass mark {quiz.passing_score}% -{" "}
        {questions.data ? `${questions.data.length} question(s)` : "loading..."}
      </p>

      {questions.error && <div className="error">{questions.error}</div>}

      <ol>
        {questions.data?.map((question) => (
          <li key={question.id}>{question.question_text}</li>
        ))}
      </ol>

      <AddQuestionForm quizId={quiz.id} onDone={questions.reload} />
    </div>
  );
}

function AddQuizForm({
  courseId,
  onDone,
}: {
  courseId: string;
  onDone: () => void;
}) {
  const [title, setTitle] = useState("");
  const [passing, setPassing] = useState(60);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSaving(true);

    try {
      await apiRequest(`/quizzes/courses/${courseId}`, {
        method: "POST",
        body: JSON.stringify({ title, passing_score: passing }),
      });

      setTitle("");
      onDone();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="panel" onSubmit={submit}>
      <h3>Add a quiz</h3>
      {error && <div className="error">{error}</div>}

      <label htmlFor="quiz-title">Quiz title</label>
      <input
        id="quiz-title"
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        maxLength={200}
        required
      />

      <label htmlFor="quiz-pass">Pass mark (%)</label>
      <input
        id="quiz-pass"
        type="number"
        min={0}
        max={100}
        value={passing}
        onChange={(event) => setPassing(Number(event.target.value))}
        required
      />

      <button className="primary-button" disabled={saving}>
        {saving ? "Adding..." : "Add quiz"}
      </button>
    </form>
  );
}

/* ---------- page ---------- */

export default function ManageCoursePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { ready, token } = useRequireAuth();

  const course = useFetch<Course>(token ? `/courses/${id}` : null);
  const outline = useFetch<ModuleOutline[]>(
    token ? `/courses/${id}/outline` : null
  );
  const quizzes = useFetch<Quiz[]>(token ? `/quizzes/courses/${id}` : null);

  const [error, setError] = useState("");

  const modules = outline.data ?? [];
  const lessonCount = modules.reduce(
    (total, module) => total + module.lessons.length,
    0
  );

  async function deleteCourse() {
    if (
      !window.confirm(
        "Delete this course and everything in it? This cannot be undone."
      )
    ) {
      return;
    }

    try {
      await apiRequest(`/courses/${id}`, { method: "DELETE" });
      router.push("/instructor");
    } catch (err) {
      setError(errorMessage(err, "Could not delete the course"));
    }
  }

  if (!ready || !token || course.loading) {
    return (
      <main className="container section">
        <p className="muted">Loading...</p>
      </main>
    );
  }

  if (course.error || !course.data) {
    return (
      <main className="container section">
        <div className="error">{course.error || "Course not found"}</div>
        <Link href="/instructor">← Back to instructor studio</Link>
      </main>
    );
  }

  return (
    <main className="container section">
      <Link href="/instructor" className="muted">
        ← Instructor studio
      </Link>

      <header className="dashboard-header">
        <span className="badge">{course.data.difficulty}</span>
        <h1>{course.data.title}</h1>
        <p className="muted">{course.data.description}</p>

        {error && <div className="error">{error}</div>}

        <div className="course-actions">
          <Link className="secondary-button" href={`/courses/${id}`}>
            View as student
          </Link>
          <button className="danger-button" onClick={deleteCourse}>
            Delete course
          </button>
        </div>
      </header>

      <h2>Modules and lessons</h2>

      {outline.error && <div className="error">{outline.error}</div>}

      {modules.map((module) => (
        <div className="card stack-item" key={module.id}>
          <h3>{module.title}</h3>

          <ul className="lesson-list">
            {module.lessons.map((lesson) => (
              <li className="lesson-item" key={lesson.id}>
                {lesson.title}
              </li>
            ))}
          </ul>

          <AddLessonForm
            moduleId={module.id}
            nextOrder={lessonCount + 1}
            onDone={outline.reload}
          />
        </div>
      ))}

      <AddModuleForm
        courseId={id}
        nextOrder={modules.length + 1}
        onDone={outline.reload}
      />

      <h2 style={{ marginTop: 40 }}>Quizzes</h2>

      {quizzes.error && <div className="error">{quizzes.error}</div>}

      {quizzes.data?.map((quiz) => (
        <QuizManager key={quiz.id} quiz={quiz} />
      ))}

      <AddQuizForm courseId={id} onDone={quizzes.reload} />
    </main>
  );
}
