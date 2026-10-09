import Link from "next/link";

const features = [
  {
    icon: "📚",
    title: "Structured learning",
    description:
      "Learn through organized courses, modules, and lessons.",
  },
  {
    icon: "🎯",
    title: "Track your progress",
    description:
      "Keep track of completed lessons and your learning journey.",
  },
  {
    icon: "🏆",
    title: "Earn certificates",
    description:
      "Pass quizzes and earn certificates for your achievements.",
  },
];

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <div className="container hero-grid">
          <div>
            <span className="eyebrow">
              YOUR NEXT CHAPTER STARTS HERE
            </span>

            <h1>
              Learn skills.
              <br />
              Build your future.
            </h1>

            <p>
              One platform for courses, practical learning,
              quizzes, progress tracking, and achievements.
            </p>

            <div className="hero-actions">
              <Link href="/register" className="primary-button">
                Start learning →
              </Link>

              <Link href="/courses" className="secondary-button">
                Explore courses
              </Link>
            </div>
          </div>

          <div className="hero-panel">
            <span className="badge">Your learning space</span>
            <h3>Small steps. Real progress.</h3>
            <p>
              Build consistency, learn at your own pace, and
              measure what you accomplish.
            </p>

            <div className="stat-row">
              <span>Organized courses</span>
              <strong>Learn</strong>
            </div>

            <div className="stat-row">
              <span>Lesson tracking</span>
              <strong>Progress</strong>
            </div>

            <div className="stat-row">
              <span>Quiz achievements</span>
              <strong>Grow</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="section-heading">
            <div>
              <span className="eyebrow">WHY LEARNSPHERE</span>
              <h2>Everything in one place</h2>
              <p className="muted">
                A focused space to learn, practice, and improve.
              </p>
            </div>
          </div>

          <div className="grid">
            {features.map((feature) => (
              <article className="card" key={feature.title}>
                <div className="course-icon">{feature.icon}</div>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <footer className="footer">
        LearnSphere · Learn something meaningful every day.
      </footer>
    </>
  );
}