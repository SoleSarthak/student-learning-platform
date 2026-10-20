"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { apiRequest, errorMessage } from "@/lib/api";
import { useRequireAuth } from "@/lib/auth";
import type { Question, Quiz, QuizAttempt, QuizResult } from "@/lib/types";
import { useFetch } from "@/lib/useFetch";

const LETTERS = ["A", "B", "C", "D"] as const;

function optionText(question: Question, letter: (typeof LETTERS)[number]) {
  switch (letter) {
    case "A":
      return question.option_a;
    case "B":
      return question.option_b;
    case "C":
      return question.option_c;
    default:
      return question.option_d;
  }
}

export default function QuizPage() {
  const { id } = useParams<{ id: string }>();
  const { ready, token } = useRequireAuth();

  const quiz = useFetch<Quiz>(`/quizzes/${id}`);
  const questions = useFetch<Question[]>(token ? `/quizzes/${id}/questions` : null);
  const attempts = useFetch<QuizAttempt[]>(token ? `/quizzes/${id}/attempts` : null);

  const [selected, setSelected] = useState<Record<number, string>>({});
  const [result, setResult] = useState<QuizResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [actionError, setActionError] = useState("");

  const items = questions.data ?? [];
  const allAnswered =
    items.length > 0 && items.every((question) => selected[question.id]);

  async function submit() {
    setActionError("");
    setSubmitting(true);

    try {
      const data = await apiRequest<QuizResult>(`/quizzes/${id}/submit`, {
        method: "POST",
        body: JSON.stringify({
          answers: items.map((question) => ({
            question_id: question.id,
            answer: selected[question.id],
          })),
        }),
      });

      setResult(data);
      attempts.reload();
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      setActionError(errorMessage(err, "Could not submit the quiz"));
    } finally {
      setSubmitting(false);
    }
  }

  function retake() {
    setSelected({});
    setResult(null);
  }

  if (!ready || !token || quiz.loading || questions.loading) {
    return (
      <main className="container section">
        <p className="muted">Loading quiz...</p>
      </main>
    );
  }

  if (quiz.error || !quiz.data) {
    return (
      <main className="container section">
        <div className="error">{quiz.error || "Quiz not found"}</div>
        <Link href="/courses">← Back to courses</Link>
      </main>
    );
  }

  const backLink = (
    <Link href={`/courses/${quiz.data.course_id}`} className="muted">
      ← Back to course
    </Link>
  );

  // e.g. 403 "You are not enrolled in this course"
  if (questions.error) {
    return (
      <main className="container section page-narrow">
        {backLink}
        <h1>{quiz.data.title}</h1>
        <div className="error">{questions.error}</div>
      </main>
    );
  }

  return (
    <main className="container section page-narrow">
      {backLink}

      <h1>{quiz.data.title}</h1>
      <p className="muted">Pass mark: {quiz.data.passing_score}%</p>

      {result && (
        <section
          className={result.passed ? "success" : "error"}
          style={{ padding: 20, margin: "20px 0" }}
        >
          <h2 style={{ marginTop: 0 }}>
            {result.passed ? "🎉 You passed!" : "Not quite - try again"}
          </h2>

          <p>
            You scored {result.score} out of {result.total_questions} (
            {Math.round(result.percentage)}%).
          </p>

          {result.certificate_issued && (
            <p>
              🏆 <strong>Certificate earned!</strong>{" "}
              <Link href="/certificates">View your certificates</Link>
            </p>
          )}

          {!result.certificate_issued &&
            result.passed &&
            result.certificate_number && (
              <p>
                You already have a certificate for this course:{" "}
                <Link href="/certificates">view it</Link>
              </p>
            )}

          {result.passed &&
            !result.certificate_number &&
            result.lessons_remaining > 0 && (
              <p>
                Finish the remaining {result.lessons_remaining} lesson
                {result.lessons_remaining === 1 ? "" : "s"} to receive your
                certificate.
              </p>
            )}

          <button className="secondary-button" onClick={retake}>
            Retake quiz
          </button>
        </section>
      )}

      {!result && (
        <>
          {items.length === 0 && (
            <div className="empty-state">This quiz has no questions yet.</div>
          )}

          {items.map((question, index) => (
            <fieldset className="card stack-item quiz-question" key={question.id}>
              <legend>
                {index + 1}. {question.question_text}
              </legend>

              {LETTERS.map((letter) => (
                <label className="option" key={letter}>
                  <input
                    type="radio"
                    name={`question-${question.id}`}
                    value={letter}
                    checked={selected[question.id] === letter}
                    onChange={() =>
                      setSelected((current) => ({
                        ...current,
                        [question.id]: letter,
                      }))
                    }
                  />
                  <span>
                    <strong>{letter}.</strong> {optionText(question, letter)}
                  </span>
                </label>
              ))}
            </fieldset>
          ))}

          {actionError && <div className="error">{actionError}</div>}

          {items.length > 0 && (
            <button
              className="primary-button"
              onClick={submit}
              disabled={!allAnswered || submitting}
            >
              {submitting
                ? "Submitting..."
                : allAnswered
                  ? "Submit answers"
                  : "Answer every question to submit"}
            </button>
          )}
        </>
      )}

      {attempts.data && attempts.data.length > 0 && (
        <section style={{ marginTop: 36 }}>
          <h3>Your previous attempts</h3>
          <ul className="lesson-list">
            {attempts.data.map((attempt) => (
              <li className="lesson-item row" key={attempt.id}>
                <span>
                  {attempt.score}/{attempt.total_questions} -{" "}
                  {attempt.passed ? "Passed" : "Not passed"}
                </span>
                <span className="muted">
                  {new Date(attempt.attempted_at).toLocaleString()}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
