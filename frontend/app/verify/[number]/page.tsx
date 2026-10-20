"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import type { CertificateVerification } from "@/lib/types";
import { useFetch } from "@/lib/useFetch";

export default function VerifyCertificatePage() {
  const { number } = useParams<{ number: string }>();

  const { data, error, loading } = useFetch<CertificateVerification>(
    `/certificates/verify/${encodeURIComponent(number)}`
  );

  return (
    <main className="container section page-narrow">
      <span className="eyebrow">CERTIFICATE VERIFICATION</span>
      <h1>Verify a certificate</h1>

      {loading && <p className="muted">Checking...</p>}

      {error && (
        <div className="error">
          ✗ No certificate was found with the number {number}.
        </div>
      )}

      {data && (
        <div className="card">
          <p className="success">✓ This certificate is valid.</p>
          <h2 style={{ marginBottom: 4 }}>{data.student_name}</h2>
          <p>
            completed <strong>{data.course_title}</strong>
          </p>
          <p className="muted">
            Issued {new Date(data.issued_at).toLocaleDateString()} - Certificate
            no. {data.certificate_number}
          </p>
        </div>
      )}

      <p style={{ marginTop: 24 }}>
        <Link href="/courses">Explore courses →</Link>
      </p>
    </main>
  );
}
