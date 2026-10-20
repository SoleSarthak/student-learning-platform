"""Pure quiz logic (no database), so it is trivial to unit test."""
from collections.abc import Iterable


def score_answers(
    correct_answers: dict[int, str],
    submitted: Iterable[tuple[int, str]],
) -> int:
    """Count correct answers.

    * Each question is counted at most ONCE, even if the client submits the
      same question many times (the last submission for a question wins).
      Without this, submitting one right answer 10 times would score 10.
    * Question ids that do not belong to the quiz are ignored.
    * Comparison is case-insensitive.
    """
    latest: dict[int, str] = {}

    for question_id, answer in submitted:
        latest[question_id] = answer

    score = 0

    for question_id, answer in latest.items():
        correct = correct_answers.get(question_id)

        if correct is not None and answer.upper() == correct.upper():
            score += 1

    return score


def percentage(score: int, total_questions: int) -> float:
    if total_questions <= 0:
        return 0.0

    return round((score / total_questions) * 100, 2)
