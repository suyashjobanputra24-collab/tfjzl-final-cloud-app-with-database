
from django.db import models
from django.conf import settings
from django.utils.timezone import now


class Course(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Lesson(models.Model):
    course = models.ForeignKey(
        Course,
        related_name="lessons",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=200)
    order = models.IntegerField(default=0)
    content = models.TextField(blank=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    AUDIT = "audit"
    HONOR = "honor"
    BETA = "BETA"

    COURSE_MODES = [
        (AUDIT, "Audit"),
        (HONOR, "Honor"),
        (BETA, "BETA"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
    )
    date_enrolled = models.DateField(default=now)
    mode = models.CharField(
        max_length=5,
        choices=COURSE_MODES,
        default=AUDIT,
    )
    rating = models.FloatField(default=5.0)

    def __str__(self):
        return f"{self.user.username} - {self.course.name}"


class Question(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
    )
    question_text = models.CharField(max_length=500)
    grade = models.IntegerField(default=1)

    def is_get_score(self, selected_ids):
        correct_ids = set(
            self.choices.filter(
                is_correct=True
            ).values_list("id", flat=True)
        )

        if correct_ids and set(selected_ids) == correct_ids:
            return self.grade

        return 0

    def __str__(self):
        return self.question_text


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        related_name="choices",
        on_delete=models.CASCADE,
    )
    choice_text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.choice_text


class Submission(models.Model):
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
    )
    choices = models.ManyToManyField(Choice)
    completed = models.BooleanField(default=False)
    score = models.FloatField(default=0)

    def __str__(self):
        return f"Submission {self.id}"


class Instructor(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.name


class Learner(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.name
