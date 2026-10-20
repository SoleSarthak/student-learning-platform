from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt
from app.models.user import User
from app.schemas.question import QuestionCreate, QuestionResponse
from app.schemas.quiz import QuizCreate, QuizResponse
from app.schemas.quiz_attempt import (
    QuizAttemptResponse,
    QuizResult,
    QuizSubmit,
)
from app.services.access_service import (
    ensure_can_manage_course,
    ensure_can_view_course_content,
    ensure_enrolled,
    get_course_or_404,
)
from app.services.certificate_service import issue_certificate_if_eligible
from app.services.progress_service import get_course_progress
from app.services.quiz_service import percentage, score_answers


router = APIRouter(
    prefix="/quizzes",
    tags=["Quizzes"],
)


def _get_quiz_or_404(db: Session, quiz_id: int) -> Quiz:
    quiz = db.get(Quiz, quiz_id)

    if quiz is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )

    return quiz


@router.post(
    "/courses/{course_id}",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quiz(
    course_id: int,
    quiz_data: QuizCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = get_course_or_404(db, course_id)
    ensure_can_manage_course(course, current_user)

    quiz = Quiz(
        title=quiz_data.title,
        passing_score=quiz_data.passing_score,
        course_id=course_id,
    )

    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    return quiz


@router.get(
    "/courses/{course_id}",
    response_model=list[QuizResponse],
)
def get_course_quizzes(
    course_id: int,
    db: Session = Depends(get_db),
):
    get_course_or_404(db, course_id)

    return list(
        db.scalars(
            select(Quiz)
            .where(Quiz.course_id == course_id)
            .order_by(Quiz.id)
        ).all()
    )


@router.post(
    "/{quiz_id}/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_question(
    quiz_id: int,
    question_data: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quiz = _get_quiz_or_404(db, quiz_id)
    course = get_course_or_404(db, quiz.course_id)
    ensure_can_manage_course(course, current_user)

    question = Question(
        question_text=question_data.question_text,
        option_a=question_data.option_a,
        option_b=question_data.option_b,
        option_c=question_data.option_c,
        option_d=question_data.option_d,
        correct_answer=question_data.correct_answer,
        quiz_id=quiz_id,
    )

    db.add(question)
    db.commit()
    db.refresh(question)

    return question


@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
):
    return _get_quiz_or_404(db, quiz_id)


@router.get(
    "/{quiz_id}/questions",
    response_model=list[QuestionResponse],
)
def get_questions(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quiz = _get_quiz_or_404(db, quiz_id)
    course = get_course_or_404(db, quiz.course_id)
    ensure_can_view_course_content(db, course, current_user)

    return list(
        db.scalars(
            select(Question)
            .where(Question.quiz_id == quiz_id)
            .order_by(Question.id)
        ).all()
    )


@router.get(
    "/{quiz_id}/attempts",
    response_model=list[QuizAttemptResponse],
)
def get_my_attempts(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_quiz_or_404(db, quiz_id)

    return list(
        db.scalars(
            select(QuizAttempt)
            .where(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.student_id == current_user.id,
            )
            .order_by(QuizAttempt.attempted_at.desc(), QuizAttempt.id.desc())
        ).all()
    )


@router.post("/{quiz_id}/submit", response_model=QuizResult)
def submit_quiz(
    quiz_id: int,
    submission: QuizSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quiz = _get_quiz_or_404(db, quiz_id)

    ensure_enrolled(db, current_user.id, quiz.course_id)

    questions = list(
        db.scalars(
            select(Question).where(Question.quiz_id == quiz_id)
        ).all()
    )

    if not questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This quiz has no questions",
        )

    correct_answers = {
        question.id: question.correct_answer for question in questions
    }

    score = score_answers(
        correct_answers,
        [(item.question_id, item.answer) for item in submission.answers],
    )

    total_questions = len(questions)
    score_percentage = percentage(score, total_questions)
    passed = score_percentage >= quiz.passing_score

    attempt = QuizAttempt(
        student_id=current_user.id,
        quiz_id=quiz_id,
        score=score,
        total_questions=total_questions,
        passed=passed,
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    certificate = None
    certificate_issued = False

    if passed:
        certificate, certificate_issued = issue_certificate_if_eligible(
            db,
            current_user,
            quiz.course_id,
        )

    progress = get_course_progress(db, current_user.id, quiz.course_id)

    return {
        "attempt_id": attempt.id,
        "score": score,
        "total_questions": total_questions,
        "percentage": score_percentage,
        "passed": passed,
        "attempted_at": attempt.attempted_at,
        "certificate_issued": certificate_issued,
        "certificate_number": (
            certificate.certificate_number if certificate else None
        ),
        "lessons_remaining": (
            progress["total_lessons"] - progress["completed_lessons"]
        ),
    }
