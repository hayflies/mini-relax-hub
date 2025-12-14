import base64
import os
from typing import List, Tuple

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.db.models import F
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from .models import Drawing, GuestBook, ReactionTest, TotalClick, WordGameResult

TARGET_WORD = "ㄱㅗㅇㅜㅔㅂ"
MAX_ATTEMPTS = 6


def signup(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "회원가입이 완료되었습니다. 환영합니다!")
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})


@require_GET
def home(request: HttpRequest) -> HttpResponse:
    return render(request, "home.html")


@require_http_methods(["GET", "POST"])
def guestbook_page(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "로그인 후 작성할 수 있습니다.")
            login_url = f"{reverse('login')}?next={request.path}"
            return redirect(login_url)

        content = request.POST.get("content", "").strip()
        if not content:
            messages.error(request, "내용을 입력해주세요.")
        else:
            GuestBook.objects.create(user=request.user, content=content)
            messages.success(request, "방문록이 등록되었습니다.")
        return redirect("guestbook")

    entries = GuestBook.objects.select_related("user").all()
    return render(request, "games/guestbook.html", {"entries": entries})


@login_required
@require_GET
def total_click_page(request: HttpRequest) -> HttpResponse:
    total_click, _ = TotalClick.objects.get_or_create(pk=1, defaults={"total_count": 0})
    return render(request, "games/total_click.html", {"total_count": total_click.total_count})


@login_required
@require_GET
def total_click_count(_: HttpRequest) -> JsonResponse:
    total_click, _ = TotalClick.objects.get_or_create(pk=1, defaults={"total_count": 0})
    return JsonResponse({"total": total_click.total_count})


@login_required
@require_POST
@transaction.atomic
def increment_total_click(_: HttpRequest) -> JsonResponse:
    total_click, _ = TotalClick.objects.select_for_update().get_or_create(
        pk=1, defaults={"total_count": 0}
    )
    TotalClick.objects.filter(pk=total_click.pk).update(total_count=F("total_count") + 1)
    total_click.refresh_from_db()
    return JsonResponse({"total": total_click.total_count})


@login_required
def drawing_page(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        image_data = request.POST.get("image_data")
        if image_data and image_data.startswith("data:image"):
            saved_path = _save_image_from_base64(request.user.id, image_data)
            if saved_path:
                Drawing.objects.create(user=request.user, image_path=saved_path)
                messages.success(request, "그림이 저장되었습니다.")
            else:
                messages.error(request, "이미지 저장에 실패했습니다.")
        else:
            messages.error(request, "유효한 이미지 데이터가 없습니다.")
        return redirect("drawing")

    drawings = Drawing.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "games/drawing.html", {"drawings": drawings})


@login_required
@require_GET
def reaction_test_page(request: HttpRequest) -> HttpResponse:
    records = ReactionTest.objects.filter(user=request.user).order_by("-created_at")[:10]
    return render(request, "games/reaction_test.html", {"records": records})


@login_required
@require_POST
def save_reaction_time(request: HttpRequest) -> JsonResponse:
    reaction_time = request.POST.get("reaction_time")
    try:
        reaction_time_int = int(reaction_time)
    except (TypeError, ValueError):
        return JsonResponse({"error": "잘못된 반응 속도 값"}, status=400)

    record = ReactionTest.objects.create(user=request.user, reaction_time=reaction_time_int)
    return JsonResponse(
        {
            "message": "저장되었습니다",
            "reaction_time": record.reaction_time,
            "created_at": timezone.localtime(record.created_at).strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


@login_required
@require_GET
def word_game_page(request: HttpRequest) -> HttpResponse:
    session_attempts = request.session.get("word_attempts", [])
    success_state = request.session.get("word_success")
    return render(
        request,
        "games/word_game.html",
        {
            "attempts": session_attempts,
            "max_attempts": MAX_ATTEMPTS,
            "success_state": success_state,
        },
    )


@login_required
@require_POST
def submit_word_guess(request: HttpRequest) -> JsonResponse:
    guess = request.POST.getlist("letters[]")
    if len(guess) != len(TARGET_WORD):
        return JsonResponse({"error": "6개의 자모를 입력해주세요."}, status=400)

    if any(len(letter) != 1 or letter.strip() == "" for letter in guess):
        return JsonResponse({"error": "각 칸에는 한 글자만 입력할 수 있습니다."}, status=400)

    result, is_correct = _evaluate_guess(guess, TARGET_WORD)
    cells = [{"letter": letter, "color": color} for letter, color in zip(guess, result)]

    attempts: List[dict] = request.session.get("word_attempts", [])
    if request.session.get("word_success") is not None:
        return JsonResponse({"error": "게임이 이미 종료되었습니다."}, status=400)

    attempts.append({"cells": cells})
    request.session["word_attempts"] = attempts

    if is_correct:
        request.session["word_success"] = True
        WordGameResult.objects.create(user=request.user, is_success=True, try_count=len(attempts))
    elif len(attempts) >= MAX_ATTEMPTS:
        request.session["word_success"] = False
        WordGameResult.objects.create(user=request.user, is_success=False, try_count=len(attempts))

    request.session.modified = True
    return JsonResponse({"result": result, "is_correct": is_correct, "attempts": attempts})


@login_required
@require_POST
def reset_word_game(request: HttpRequest) -> JsonResponse:
    request.session.pop("word_attempts", None)
    request.session.pop("word_success", None)
    return JsonResponse({"message": "게임이 초기화되었습니다."})


def _evaluate_guess(guess: List[str], target: str) -> Tuple[List[str], bool]:
    result = ["gray"] * len(target)
    target_list = list(target)

    for idx, letter in enumerate(guess):
        if letter == target[idx]:
            result[idx] = "green"
            target_list[idx] = None

    for idx, letter in enumerate(guess):
        if result[idx] == "green":
            continue
        if letter in target_list:
            result[idx] = "yellow"
            target_list[target_list.index(letter)] = None

    is_correct = all(color == "green" for color in result)
    return result, is_correct


def _save_image_from_base64(user_id: int, image_data: str) -> str | None:
    try:
        header, imgstr = image_data.split(",", 1)
    except ValueError:
        return None

    extension = header.split("/")[1].split(";")[0]
    file_name = f"drawing_{user_id}_{timezone.now().strftime('%Y%m%d%H%M%S%f')}.{extension}"
    drawings_dir = settings.MEDIA_ROOT / "drawings"
    os.makedirs(drawings_dir, exist_ok=True)

    file_path = drawings_dir / file_name
    try:
        with open(file_path, "wb") as img_file:
            img_file.write(base64.b64decode(imgstr))
    except (OSError, ValueError):
        return None

    return f"drawings/{file_name}"
