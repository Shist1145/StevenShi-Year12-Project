from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
import json
import sqlite3
from datetime import datetime


# Basic file and server settings.
BASE_DIR = Path(__file__).resolve().parent
STUDENT_FILE = BASE_DIR / "School Report System Prototype.html"
TEACHER_FILE = BASE_DIR / "teacher.html"
DB_FILE = BASE_DIR / "reports.db"
HOST = "127.0.0.1"
PORT = 8000
TEACHER_KEY = "teacher123"
MAX_JSON_BYTES = 10000
MAX_FIELD_LENGTHS = {
    "studentName": 80,
    "location": 100,
    "issueType": 80,
    "priority": 30,
    "description": 600,
}
VALID_STATUSES = ("Pending", "In Progress", "Completed")


# Open the SQLite database and close it after use.
@contextmanager
def get_connection():
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


# Create table and add test data.
def init_database():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                location TEXT NOT NULL,
                issue_type TEXT NOT NULL,
                priority TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        report_count = connection.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
        if report_count == 0:
            connection.execute(
                """
                INSERT INTO reports (
                    id, student_name, location, issue_type, priority,
                    description, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    100,
                    "Steven He",
                    "ASIA",
                    "EMOTIONAL DAMAGE",
                    "FAILER",
                    "WHY YOU NEED CALCULATOR? USE YOUR BRAIN, IT SHOULD GO RING RING!!!",
                    "Pending",
                    "EMOTION_TEST",
                ),
            )


# Change database row names to JavaScript names.
def row_to_report(row):
    return {
        "id": row["id"],
        "studentName": row["student_name"],
        "location": row["location"],
        "issueType": row["issue_type"],
        "priority": row["priority"],
        "description": row["description"],
        "status": row["status"],
        "createdAt": row["created_at"],
    }


# Get one report by ID.
def get_report(connection, report_id):
    row = connection.execute(
        "SELECT * FROM reports WHERE id = ?",
        (report_id,),
    ).fetchone()
    if row is None:
        return None
    return row_to_report(row)


# Make a database error text.
def database_error_message(error):
    return f"Database error: {error}"


# Check report data before saving it.
def clean_report_data(data):
    if not isinstance(data, dict):
        return None, "Invalid report data."

    cleaned = {}
    for field, max_length in MAX_FIELD_LENGTHS.items():
        value = str(data.get(field, "")).strip()
        if not value:
            return None, "All fields are required."
        if len(value) > max_length:
            return None, f"{field} is too long."
        cleaned[field] = value

    return cleaned, None


class ReportServer(BaseHTTPRequestHandler):
    # Serve pages and teacher report list API.
    def do_GET(self):
        parsed_path = urlparse(self.path)
        request_path = unquote(parsed_path.path)

        if request_path == "/":
            self.send_redirect("/student")
            return

        if request_path in ("/student", "/student.html", f"/{STUDENT_FILE.name}"):
            self.send_html(STUDENT_FILE)
            return

        if request_path in ("/teacher", "/teacher.html"):
            self.send_html(TEACHER_FILE)
            return

        if request_path == "/api/reports":
            if not self.has_teacher_access():
                self.send_json({"error": "Teacher access required."}, status=403)
                return

            try:
                with get_connection() as connection:
                    rows = connection.execute(
                        "SELECT * FROM reports ORDER BY id DESC"
                    ).fetchall()
            except sqlite3.Error as error:
                self.send_json({"error": database_error_message(error)}, status=500)
                return

            self.send_json([row_to_report(row) for row in rows])
            return

        self.send_error(404, "Not found")

    # Student API: create a report.
    def do_POST(self):
        if urlparse(self.path).path != "/api/reports":
            self.send_error(404, "Not found")
            return

        data = self.read_json()
        report_data, error = clean_report_data(data)
        if error:
            self.send_json({"error": error}, status=400)
            return

        created_at = datetime.now().strftime("%d/%m/%Y, %I:%M %p")
        try:
            with get_connection() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO reports (
                        student_name, location, issue_type, priority,
                        description, status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        report_data["studentName"],
                        report_data["location"],
                        report_data["issueType"],
                        report_data["priority"],
                        report_data["description"],
                        "Pending",
                        created_at,
                    ),
                )
                report = get_report(connection, cursor.lastrowid)
        except sqlite3.Error as error:
            self.send_json({"error": database_error_message(error)}, status=500)
            return

        self.send_json(report, status=201)

    # Teacher API: update report status.
    def do_PATCH(self):
        parts = urlparse(self.path).path.strip("/").split("/")
        if len(parts) != 4 or parts[:2] != ["api", "reports"] or parts[3] != "status":
            self.send_error(404, "Not found")
            return

        if not self.has_teacher_access():
            self.send_json({"error": "Teacher access required."}, status=403)
            return

        report_id = self.parse_report_id(parts[2])
        if report_id is None:
            self.send_json({"error": "Invalid report ID."}, status=400)
            return

        data = self.read_json()
        new_status = "" if data is None else str(data.get("status", "")).strip()
        if new_status not in VALID_STATUSES:
            self.send_json({"error": "Invalid status."}, status=400)
            return

        try:
            with get_connection() as connection:
                cursor = connection.execute(
                    "UPDATE reports SET status = ? WHERE id = ?",
                    (new_status, report_id),
                )
                if cursor.rowcount == 0:
                    self.send_json({"error": "Report not found."}, status=404)
                    return
                report = get_report(connection, report_id)
        except sqlite3.Error as error:
            self.send_json({"error": database_error_message(error)}, status=500)
            return

        self.send_json(report)

    # Teacher API: delete one report.
    def do_DELETE(self):
        parts = urlparse(self.path).path.strip("/").split("/")
        if len(parts) != 3 or parts[:2] != ["api", "reports"]:
            self.send_error(404, "Not found")
            return

        if not self.has_teacher_access():
            self.send_json({"error": "Teacher access required."}, status=403)
            return

        report_id = self.parse_report_id(parts[2])
        if report_id is None:
            self.send_json({"error": "Invalid report ID."}, status=400)
            return

        try:
            with get_connection() as connection:
                cursor = connection.execute("DELETE FROM reports WHERE id = ?", (report_id,))
                if cursor.rowcount == 0:
                    self.send_json({"error": "Report not found."}, status=404)
                    return
        except sqlite3.Error as error:
            self.send_json({"error": database_error_message(error)}, status=500)
            return

        self.send_response(204)
        self.end_headers()

    # Check simple teacher key.
    def has_teacher_access(self):
        parsed_path = urlparse(self.path)
        query = parse_qs(parsed_path.query)
        return TEACHER_KEY in query.get("key", [])

    # Read report ID from URL text.
    def parse_report_id(self, value):
        try:
            return int(value)
        except ValueError:
            return None

    # Read JSON body from request.
    def read_json(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            return None

        if content_length == 0:
            return None
        if content_length > MAX_JSON_BYTES:
            self.rfile.read(content_length)
            return None

        try:
            raw_body = self.rfile.read(content_length).decode("utf-8")
            return json.loads(raw_body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None

    # Send browser redirect.
    def send_redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    # Send one HTML file.
    def send_html(self, html_file):
        if not html_file.exists():
            self.send_error(404, "HTML file not found")
            return

        content = html_file.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    # Send JSON response.
    def send_json(self, data, status=200):
        content = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


if __name__ == "__main__":
    # Start database and server.
    try:
        init_database()
    except sqlite3.Error as error:
        raise SystemExit(database_error_message(error))

    try:
        server = ThreadingHTTPServer((HOST, PORT), ReportServer)
    except OSError as error:
        raise SystemExit(f"Could not start server on http://{HOST}:{PORT}: {error}")

    print(f"Server running at http://{HOST}:{PORT}")
    print(f"SQLite database: {DB_FILE}")
    server.serve_forever()
