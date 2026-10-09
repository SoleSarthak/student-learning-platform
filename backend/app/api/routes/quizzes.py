import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.db.database import get_db
from app.models.certificate import Certificate
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt
from app.models.user import User
from app.schemas.question import (
    QuestionCreate,
    QuestionResponse
)
from app.schemas.quiz import (
    QuizCreate,
    QuizResponse
)
from app.schemas.quiz_attempt import (
    QuizResult,
    QuizSubmit
)


router = APIRouter(
    prefix="/quizzes",
    tags=["Quizzes"]
)


@router.post(
    "/courses/{course_id}",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED
)
def create_quiz(
    course_id: int,
    quiz_data: QuizCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    course = db.get(Course, course_id)

    if course is None:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    if (
        current_user.role != "admin"
        and course.instructor_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You do not own this course"
        )

    quiz = Quiz(
        title=quiz_data.title,
        passing_score=quiz_data.passing_score,
        course_id=course_id
    )

    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    return quiz


@router.post(
    "/{quiz_id}/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_question(
    quiz_id: int,
    question_data: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    quiz = db.get(Quiz, quiz_id)

    if quiz is None:
        raise HTTPException(
            status_code=404,
            detail="Quiz not found"
        )

    course = db.get(Course, quiz.course_id)

    if (
        current_user.role != "admin"
        and course.instructor_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You do not own this course"
        )

    correct_answer = question_data.correct_answer.upper()

    if correct_answer not in ["A", "B", "C", "D"]:
        raise HTTPException(
            status_code=400,
            detail="correct_answer must be A, B, C or D"
        )

    question = Question(
        question_text=question_data.question_text,
        option_a=question_data.option_a,
        option_b=question_data.option_b,
        option_c=question_data.option_c,
        option_d=question_data.option_d,
        correct_answer=correct_answer,
        quiz_id=quiz_id
    )

    db.add(question)
    db.commit()
    db.refresh(question)

    return question


@router.get(
    "/{quiz_id}",
    response_model=QuizResponse
)
def get_quiz(
    quiz_id: int,
    db: Session = Depends(get_db)
):

    quiz = db.get(Quiz, quiz_id)

    if quiz is None:
        raise HTTPException(
            status_code=404,
            detail="Quiz not found"
        )

    return quiz


@router.get(
    "/{quiz_id}/questions",
    response_model=list[QuestionResponse]
)
def get_questions(
    quiz_id: int,
    db: Session = Depends(get_db)
):

    quiz = db.get(Quiz, quiz_id)

    if quiz is None:
        raise HTTPException(
            status_code=404,
            detail="Quiz not found"
        )

    statement = (
        select(Question)
        .where(Question.quiz_id == quiz_id)
        .order_by(Question.id)
    )

    return list(db.scalars(statement).all())


@router.post(
    "/{quiz_id}/submit",
    response_model=QuizResult
)
def submit_quiz(
    quiz_id: int,
    submission: QuizSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    quiz = db.get(Quiz, quiz_id)

    if quiz is None:
        raise HTTPException(
            status_code=404,
            detail="Quiz not found"
        )

    enrollment = db.scalar(
        select(Enrollment)
        .where(
            Enrollment.student_id == current_user.id,
            Enrollment.course_id == quiz.course_id
        )
    )

    if enrollment is None:
        raise HTTPException(
            status_code=403,
            detail="You are not enrolled in this course"
        )

    questions = list(
        db.scalars(
            select(Question)
            .where(Question.quiz_id == quiz_id)
        ).all()
    )

    if not questions:
        raise HTTPException(
            status_code=400,
            detail="This quiz has no questions"
        )

    correct_answers = {
        question.id: question.correct_answer
        for question in questions
    }

    score = 0

    for submitted_answer in submission.answers:

        correct_answer = correct_answers.get(
            submitted_answer.question_id
        )

        if (
            correct_answer is not None
            and submitted_answer.answer.upper()
            == correct_answer
        ):
            score += 1

    total_questions = len(questions)

    percentage = round(
        (score / total_questions) * 100,
        2
    )

    passed = percentage >= quiz.passing_score

    attempt = QuizAttempt(
        student_id=current_user.id,
        quiz_id=quiz_id,
        score=score,
        total_questions=total_questions,
        passed=passed
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    # Generate certificate if the student passes.
    if passed:

        existing_certificate = db.scalar(
            select(Certificate).where(
                Certificate.student_id == current_user.id,
                Certificate.course_id == quiz.course_id
            )
        )

        if existing_certificate is None:

            certificate = Certificate(
                certificate_number=f"CERT-{uuid.uuid4().hex[:12].upper()}",
                student_id=current_user.id,
                course_id=quiz.course_id
            )

            db.add(certificate)
            db.commit()

    return {
        "attempt_id": attempt.id,
        "score": score,
        "total_questions": total_questions,
        "percentage": percentage,
        "passed": passed,
        "attempted_at": attempt.attempted_at
    }