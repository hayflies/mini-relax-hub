"""Flask 보조 API 서버: 반응 속도 저장 및 누적 클릭 조회."""
import os
from flask import Flask, jsonify, request

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mini_relax_hub.settings")
import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from games.models import ReactionTest, TotalClick  # noqa: E402

User = get_user_model()

app = Flask(__name__)


@app.route("/api/clicks", methods=["GET"])
def api_clicks():
    total, _ = TotalClick.objects.get_or_create(pk=1, defaults={"total_count": 0})
    return jsonify({"total": total.total_count})


@app.route("/api/reaction", methods=["POST"])
def api_reaction():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    reaction_time = data.get("reaction_time")
    if username is None or reaction_time is None:
        return jsonify({"error": "username과 reaction_time이 필요합니다."}), 400
    try:
        user = User.objects.get(username=username)
        reaction_value = int(reaction_time)
    except (User.DoesNotExist, ValueError):
        return jsonify({"error": "잘못된 사용자 또는 반응 속도"}), 400

    record = ReactionTest.objects.create(user=user, reaction_time=reaction_value)
    return jsonify({"message": "저장됨", "reaction_time": record.reaction_time})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
