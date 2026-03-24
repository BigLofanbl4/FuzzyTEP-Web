import json
import mimetypes
from wsgiref.simple_server import make_server

from .config import STATIC_DIR
from .storage import (
    delete_enterprise,
    get_enterprise,
    get_history,
    init_db,
    list_enterprises,
    save_analysis,
    save_enterprise,
)


def json_response(start_response, payload, status="200 OK"):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = [("Content-Type", "application/json; charset=utf-8"), ("Content-Length", str(len(body)))]
    start_response(status, headers)
    return [body]


def text_response(start_response, body, status="200 OK", content_type="text/plain; charset=utf-8"):
    payload = body.encode("utf-8")
    headers = [("Content-Type", content_type), ("Content-Length", str(len(payload)))]
    start_response(status, headers)
    return [payload]


def parse_json_body(environ):
    try:
        size = int(environ.get("CONTENT_LENGTH") or "0")
    except ValueError:
        size = 0
    raw_body = environ["wsgi.input"].read(size) if size > 0 else b"{}"
    if not raw_body:
        return {}
    return json.loads(raw_body.decode("utf-8"))


def serve_static(start_response, path):
    if path == "/":
        target = STATIC_DIR / "index.html"
    else:
        relative = path[len("/static/") :]
        target = (STATIC_DIR / relative).resolve()
        if not str(target).startswith(str(STATIC_DIR.resolve())):
            return text_response(start_response, "Forbidden", status="403 Forbidden")

    if not target.exists():
        return text_response(start_response, "Not found", status="404 Not Found")

    content_type = mimetypes.guess_type(target)[0] or "application/octet-stream"
    data = target.read_bytes()
    start_response("200 OK", [("Content-Type", content_type), ("Content-Length", str(len(data)))])
    return [data]


def application(environ, start_response):
    method = environ["REQUEST_METHOD"].upper()
    path = environ.get("PATH_INFO", "/")

    if method == "OPTIONS":
        start_response(
            "204 No Content",
            [
                ("Access-Control-Allow-Origin", "*"),
                ("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"),
                ("Access-Control-Allow-Headers", "Content-Type"),
            ],
        )
        return [b""]

    if path == "/" or path.startswith("/static/"):
        return serve_static(start_response, path)

    try:
        if path == "/api/enterprises" and method == "GET":
            return json_response(start_response, {"items": list_enterprises()})
        if path == "/api/enterprises" and method == "POST":
            return json_response(start_response, {"item": save_enterprise(parse_json_body(environ))}, status="201 Created")

        if path.startswith("/api/enterprises/"):
            parts = [part for part in path.split("/") if part]
            if len(parts) < 3:
                return text_response(start_response, "Not found", status="404 Not Found")

            enterprise_id = int(parts[2])
            enterprise = get_enterprise(enterprise_id)
            if enterprise is None:
                return json_response(start_response, {"error": "Предприятие не найдено."}, status="404 Not Found")

            if len(parts) == 3 and method == "GET":
                return json_response(start_response, {"item": enterprise})
            if len(parts) == 3 and method == "PUT":
                payload = parse_json_body(environ)
                return json_response(start_response, {"item": save_enterprise(payload, enterprise_id=enterprise_id)})
            if len(parts) == 3 and method == "DELETE":
                delete_enterprise(enterprise_id)
                return json_response(start_response, {"success": True})
            if len(parts) == 4 and parts[3] == "history" and method == "GET":
                return json_response(start_response, {"items": get_history(enterprise_id)})
            if len(parts) == 4 and parts[3] == "analyze" and method == "POST":
                return json_response(start_response, {"item": save_analysis(enterprise_id, parse_json_body(environ))}, status="201 Created")

        return text_response(start_response, "Not found", status="404 Not Found")
    except ValueError as error:
        return json_response(start_response, {"error": str(error)}, status="400 Bad Request")
    except json.JSONDecodeError:
        return json_response(start_response, {"error": "Некорректный JSON в запросе."}, status="400 Bad Request")
    except Exception as error:
        return json_response(start_response, {"error": f"Внутренняя ошибка сервера: {error}"}, status="500 Internal Server Error")


def run():
    init_db()
    host = "127.0.0.1"
    port = 8000
    print(f"FuzzyTEP Web запущен на http://{host}:{port}")
    try:
        with make_server(host, port, application) as server:
            server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
