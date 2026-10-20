from app.services.quiz_service import percentage, score_answers


CORRECT = {1: "A", 2: "B", 3: "C"}


def test_counts_correct_answers_case_insensitively():
    assert score_answers(CORRECT, [(1, "a"), (2, "B"), (3, "D")]) == 2


def test_duplicate_answers_count_once():
    # Regression: submitting the same right answer 10 times used to score 10.
    assert score_answers(CORRECT, [(1, "A")] * 10) == 1


def test_last_answer_for_a_question_wins():
    assert score_answers(CORRECT, [(1, "B"), (1, "A")]) == 1
    assert score_answers(CORRECT, [(1, "A"), (1, "B")]) == 0


def test_unknown_question_ids_are_ignored():
    assert score_answers(CORRECT, [(99, "A")]) == 0


def test_percentage():
    assert percentage(2, 3) == 66.67
    assert percentage(0, 0) == 0.0
    assert percentage(3, 3) == 100.0
