
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseNotAllowed
from django.contrib.auth.decorators import login_required

from .models import Course, Lesson, Question, Choice, Enrollment, Submission


def course_details(request, course_id):
    course = get_object_or_404(
        Course.objects.prefetch_related("lessons"),
        pk=course_id,
    )
    return render(
        request,
        "onlinecourse/course_details_bootstrap.html",
        {"course": course},
    )


def check_if_enrolled(user, course):
    if not user.is_authenticated:
        return False

    return Enrollment.objects.filter(
        user=user,
        course=course,
    ).exists()


def extract_answers(request):
    """Collect selected choice IDs from the submitted exam form."""
    submitted_answers = []

    for key in request.POST:
        if key.startswith("choice"):
            submitted_answers.extend(
                int(value)
                for value in request.POST.getlist(key)
                if value.isdigit()
            )

    return submitted_answers


@login_required
def submit(request, course_id):
    """Create a submission for the logged-in learner's enrollment."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    course = get_object_or_404(Course, pk=course_id)

    enrollment = get_object_or_404(
        Enrollment,
        user=request.user,
        course=course,
    )

    submission = Submission.objects.create(
        enrollment=enrollment
    )

    selected_ids = extract_answers(request)

    # Only save choices belonging to questions in this course.
    choices = Choice.objects.filter(
        id__in=selected_ids,
        question__course=course,
    )

    submission.choices.set(choices)

    score = 0

    for question in Question.objects.filter(course=course):
        selected_for_question = choices.filter(
            question=question
        ).values_list("id", flat=True)

        score += question.is_get_score(selected_for_question)

    submission.score = score
    submission.completed = True
    submission.save()

    return redirect(
        "onlinecourse:show_exam_result",
        course_id=course.id,
        submission_id=submission.id,
    )


@login_required
def show_exam_result(request, course_id, submission_id):
    """Calculate and display the learner's exam result."""
    course = get_object_or_404(Course, pk=course_id)

    submission = get_object_or_404(
        Submission,
        pk=submission_id,
        enrollment__user=request.user,
        enrollment__course=course,
    )

    selected_ids = set(
        submission.choices.values_list("id", flat=True)
    )

    results = []
    total_score = 0

    questions = Question.objects.filter(
        course=course
    ).prefetch_related("choices")

    for question in questions:
        possible_choices = question.choices.all()

        question_choice_ids = set(
            possible_choices.values_list("id", flat=True)
        )

        selected_for_question = selected_ids.intersection(
            question_choice_ids
        )

        correct_ids = set(
            possible_choices.filter(
                is_correct=True
            ).values_list("id", flat=True)
        )

        question_score = question.is_get_score(
            selected_for_question
        )

        total_score += question.grade

        results.append({
            "question": question,
            "choices": possible_choices,
            "possible": possible_choices,
            "selected_ids": selected_for_question,
            "correct_ids": correct_ids,
            "is_correct": question_score > 0,
            "grade": question.grade,
            "score": question_score,
        })

    percentage = (
        round((submission.score / total_score) * 100, 2)
        if total_score
        else 0
    )

    return render(
        request,
        "onlinecourse/exam_result_bootstrap.html",
        {
            "course": course,
            "submission": submission,
            "results": results,
            "selected_ids": selected_ids,
            "score": submission.score,
            "total_score": total_score,
            "grade": percentage,
        },
    )
