"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";

interface Certificate {
  id: number;
  certificate_number: string;
  student_id: number;
  course_id: number;
  issued_at: string;
}

export default function CertificatesPage() {
  const [certificates, setCertificates] = useState<Certificate[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiRequest("/certificates")
      .then(setCertificates)
      .catch((err) => setError(err.message || "Unable to load certificates"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="container section">
      <span className="eyebrow">ACHIEVEMENTS</span>
      <h1>Your certificates</h1>
      <p className="muted">Your learning achievements in one place.</p>

      {loading && <p>Loading certificates...</p>}
      {error && <div className="error">{error}</div>}

      {!loading && !error && certificates.length === 0 && (
        <div className="empty-state">
          <h3>No certificates yet</h3>
          <p>Complete eligible quizzes to earn certificates.</p>
        </div>
      )}

      <div className="grid" style={{ marginTop: 25 }}>
        {certificates.map((certificate) => (
          <article className="card" key={certificate.id}>
            <div className="course-icon">🏆</div>
            <h3>Course #{certificate.course_id}</h3>
            <p>Certificate: {certificate.certificate_number}</p>
            <p>
              Issued: {new Date(certificate.issued_at).toLocaleDateString()}
            </p>
          </article>
        ))}
      </div>
    </main>
  );
}