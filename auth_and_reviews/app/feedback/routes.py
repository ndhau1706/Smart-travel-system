from flask import Blueprint

feedback_bp = Blueprint("feedback", __name__)


@feedback_bp.route("/ping", methods=["GET"])
def ping():
    return {"message": "Feedback module is working!"}
