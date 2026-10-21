"""Player profile management."""
import logging
import shutil

from flask import Blueprint, jsonify, request

from dragon_city.storage import user_dir

logger = logging.getLogger(__name__)

bp = Blueprint("account", __name__)


@bp.route("/delete_profile", methods=["POST"])
def delete_profile():
    try:
        data = request.get_json(force=True)
        user_id = data.get("user_id")

        if not user_id:
            return jsonify({"status": "error", "msg": "user_id is required"}), 400

        directory = user_dir(user_id)

        if directory.exists():
            shutil.rmtree(directory)
            logger.info("Save folder deleted for player %s", user_id)
            return jsonify({"status": "ok", "deleted": True})

        logger.info("No save folder to delete for player %s (login profile only)", user_id)
        return jsonify({"status": "ok", "deleted": False})

    except Exception as e:
        logger.exception("Error in /delete_profile")
        return jsonify({"status": "error", "msg": str(e)}), 500
