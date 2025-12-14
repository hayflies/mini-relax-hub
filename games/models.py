"""Game-related data models."""
from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class TotalClick(models.Model):
    """Stores the global button click count using a single row."""

    total_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Total Click"
        verbose_name_plural = "Total Clicks"

    def save(self, *args, **kwargs):
        # Ensure only a single row exists by fixing the primary key.
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Total Clicks: {self.total_count}"


class Drawing(models.Model):
    """Represents a drawing saved by a user."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="drawings")
    image_path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Drawing by {self.user}: {self.image_path}"


class ReactionTest(models.Model):
    """Stores reaction time test records."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reaction_tests")
    reaction_time = models.IntegerField(help_text="Reaction time in milliseconds")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user} - {self.reaction_time}ms"


class WordGameResult(models.Model):
    """Stores results for word-based games."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="word_game_results")
    is_success = models.BooleanField()
    try_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        status = "Success" if self.is_success else "Fail"
        return f"{self.user} - {status} in {self.try_count} tries"
