import json
import logging
import mimetypes
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

from models import SessionStore
from utils import build_compliance_packet, generate_order_id

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
EXPORT_FOLDER = BASE_DIR / "exports"
LOG_FOLDER = BASE_DIR / "logs"
TMP_FOLDER = BASE_DIR / "tmp"
SESSION_FILE = TMP_FOLDER / "session_store.json"

for folder in (UPLOAD_FOLDER, EXPORT_FOLDER, LOG_FOLDER, TMP_FOLDER):
    folder.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["EXPORT_FOLDER"] = str(EXPORT_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB
app.config["SECRET_KEY"] = "governance-gateway-demo"

session_store = SessionStore(SESSION_FILE)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FOLDER / "app.log"), logging.StreamHandler()],
)


@app.route("/")
def index():
    return render_template("index.html")


def _allowed_file(filename: str) -> bool:
    return filename.lower().endswith(".pdf")


@app.route("/upload", methods=["POST"])
def upload():
    if "document" not in request.files:
        abort(400, "No file provided")

    file = request.files["document"]
    if file.filename == "":
        abort(400, "Empty filename")

    if not _allowed_file(file.filename):
        abort(400, "Only PDF uploads are supported")

    filename = secure_filename(file.filename)
    order_id = generate_order_id()

    stored_filename = f"{order_id}_{filename}"
    upload_path = UPLOAD_FOLDER / stored_filename
    file.save(upload_path)

    size_bytes = upload_path.stat().st_size

    record = {
        "order_id": order_id,
        "uploaded_filename": filename,
        "stored_filename": stored_filename,
        "mime": mimetypes.guess_type(filename)[0] or "application/pdf",
        "size_bytes": size_bytes,
        "uploaded_at": datetime.utcnow().isoformat() + "Z",
        "finalized": False,
        "packet": None,
    }

    session_store.set(order_id, record)

    return redirect(url_for("progress", order_id=order_id))


@app.route("/progress/<order_id>")
def progress(order_id):
    record = session_store.get(order_id)
    if not record:
        abort(404)
    return render_template("progress.html", order=record)


@app.route("/finalize/<order_id>", methods=["POST"])
def finalize(order_id):
    record = session_store.get(order_id)
    if not record:
        abort(404)

    if record.get("finalized") and record.get("packet"):
        packet_info = record["packet"]
        return jsonify({
            "ok": True,
            "order_id": order_id,
            "json_url": packet_info.get("json_url"),
            "csv_url": packet_info.get("csv_url"),
        })

    packet_info = build_compliance_packet(order_id, record, EXPORT_FOLDER)
    record["finalized"] = True
    record["packet"] = packet_info
    session_store.set(order_id, record)

    return jsonify({
        "ok": True,
        "order_id": order_id,
        "json_url": packet_info["json_url"],
        "csv_url": packet_info["csv_url"],
    })


@app.route("/exports/<path:filename>")
def download_packet(filename):
    return send_from_directory(app.config["EXPORT_FOLDER"], filename, as_attachment=True)


@app.route("/templates/download/onboarding")
def download_template():
    sample_path = BASE_DIR / "templates" / "sample_uploads"
    return send_from_directory(sample_path, "Onboarding_Template.csv", as_attachment=True)


@app.route("/rail/send/<order_id>", methods=["POST"])
def send_to_rail(order_id):
    record = session_store.get(order_id)
    if not record or not record.get("packet"):
        abort(404)

    json_path = EXPORT_FOLDER / Path(record["packet"]["json_url"]).name
    if not json_path.exists():
        abort(404)

    with json_path.open("r", encoding="utf-8") as fh:
        packet = json.load(fh)

    line = f"{datetime.utcnow().isoformat()}Z | {order_id} | {packet.get('packet_hash')}\n"
    rail_log = LOG_FOLDER / "rail_stub.log"
    with rail_log.open("a", encoding="utf-8") as log_file:
        log_file.write(line)

    return redirect(url_for("sent", order_id=order_id))


@app.route("/sent/<order_id>")
def sent(order_id):
    record = session_store.get(order_id)
    if not record or not record.get("packet"):
        abort(404)

    json_url = record["packet"]["json_url"]
    packet_hash = record["packet"].get("packet_hash")

    return render_template(
        "sent.html",
        order_id=order_id,
        packet_hash=packet_hash,
        json_url=json_url,
    )


if __name__ == "__main__":
    app.run(debug=True)
