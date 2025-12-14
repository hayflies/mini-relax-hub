from django.contrib import admin

from .models import Drawing, ReactionTest, TotalClick, WordGameResult


@admin.register(TotalClick)
class TotalClickAdmin(admin.ModelAdmin):
    list_display = ("total_count", "updated_at")


@admin.register(Drawing)
class DrawingAdmin(admin.ModelAdmin):
    list_display = ("user", "image_path", "created_at")
    search_fields = ("user__username", "image_path")


@admin.register(ReactionTest)
class ReactionTestAdmin(admin.ModelAdmin):
    list_display = ("user", "reaction_time", "created_at")
    search_fields = ("user__username",)


@admin.register(WordGameResult)
class WordGameResultAdmin(admin.ModelAdmin):
    list_display = ("user", "is_success", "try_count", "created_at")
    search_fields = ("user__username",)
    list_filter = ("is_success",)
