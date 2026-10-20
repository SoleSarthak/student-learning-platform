"use client";

import Link from "next/link";
import { useRequireAuth } from "@/lib/auth";
import type { Certificate } from "@/lib/types";
import { useFetch } from "@/lib/useFetch";

export default function CertificatesPage() {
  const { ready, token } = useRequireAuth();
  const { data, error, loading } = useFetch<Certificate[]>(
    token ? "/certificates" : null
  );

  if (!ready || !token || loading) {
    return (
      <main className="container section">
        <p className="muted">Loading certificates...</p>
      </main>
    );
  }

  const certificates = data ?? [];

  return (
    <main className="container section">
      <div className="section-heading">
        <div>
          <span className="eyebrow">ACHIEVEMENTS</span>
          <h2>My certificates</h2>
          <p className="muted">
            Earned by finishing every lesson and passing every quiz in a course.
          </p>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {!error && certificates.length === 0 && (
        <div className="empty-state">
          <h3>No certificates yet</h3>
          <p>Complete a course to earn your first one.</p>
          <Link className="primary-button" href="/courses">
            Browse courses
          </Link>
        </div>
      )}

      <div className="grid">
        {certificates.map((certificate) => (
          <article className="card" key={certificate.id}>
            <div className="course-icon">🏆</div>
            <h3>{certificate.course_title}</h3>
            <p>
              Certificate no. <strong>{certificate.certificate_number}</strong>
              <br />
              Issued {new Date(certificate.issued_at).toLocaleDateString()}
            </p>
            <Link
              className="secondary-button"
              href={`/verify/${certificate.certificate_number}`}
            >
              Public verification page
            </Link>
          </article>
        ))}
      </div>
    </main>
  );
}
