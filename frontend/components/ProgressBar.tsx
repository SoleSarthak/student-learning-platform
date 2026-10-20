export default function ProgressBar({ value }: { value: number }) {
  const percent = Math.max(0, Math.min(100, value));

  return (
    <div
      className="progress"
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(percent)}
    >
      <div className="progress-fill" style={{ width: `${percent}%` }} />
    </div>
  );
}
