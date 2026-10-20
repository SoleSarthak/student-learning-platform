export interface User {
  id: number;
  name: string;
  email: string;
  role: "student" | "instructor" | "admin";
}

export interface Course {
  id: number;
  title: string;
  description: string;
  difficulty: string;
  instructor_id: number;
  created_at: string;
}

export interface LessonSummary {
  id: number;
  title: string;
  order: number;
}

export interface ModuleOutline {
  id: number;
  title: string;
  order: number;
  course_id: number;
  lessons: LessonSummary[];
}

export interface LessonDetail {
  id: number;
  title: string;
  content: string;
  video_url: string | null;
  order: number;
  module_id: number;
  course_id: number;
}

export interface Enrollment {
  id: number;
  student_id: number;
  course_id: number;
  enrolled_at: string;
}

export interface Progress {
  course_id: number;
  total_lessons: number;
  completed_lessons: number;
  progress_percentage: number;
  completed_lesson_ids: number[];
}

export interface LessonCompleteResult {
  lesson_id: number;
  completed: boolean;
  completed_at: string | null;
  certificate_number: string | null;
}

export interface Quiz {
  id: number;
  title: string;
  passing_score: number;
  course_id: number;
}

export interface Question {
  id: number;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  quiz_id: number;
}

export interface QuizAttempt {
  id: number;
  quiz_id: number;
  score: number;
  total_questions: number;
  passed: boolean;
  attempted_at: string;
}

export interface QuizResult {
  attempt_id: number;
  score: number;
  total_questions: number;
  percentage: number;
  passed: boolean;
  attempted_at: string;
  certificate_issued: boolean;
  certificate_number: string | null;
  lessons_remaining: number;
}

export interface Certificate {
  id: number;
  certificate_number: string;
  student_id: number;
  course_id: number;
  course_title: string;
  issued_at: string;
}

export interface CertificateVerification {
  valid: boolean;
  certificate_number: string;
  student_name: string;
  course_title: string;
  issued_at: string;
}
