"""Lightweight web server for workflow and tool switching."""
from __future__ import annotations

import json
import threading
from queue import Queue, Empty
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, Callable, Any
from urllib.parse import parse_qs, urlparse

from config.llm import get_llm
from config.model import DEFAULT_MODEL_ID
from config.model_utils import get_default_model, list_models, get_model_by_id
from tools.registry import get_tools
from workflow.flow import MultiAgentWorkflow


WORKFLOW_REGISTRY: Dict[str, Callable[[], Any]] = {
    MultiAgentWorkflow.name: MultiAgentWorkflow,
}

STATIC_DIR = Path(__file__).resolve().parent / "static"


class AgentHTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler that serves static page and workflow APIs."""

    def _json_response(self, payload: Dict[str, Any], status: int = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _serve_index(self) -> None:
        file_path = STATIC_DIR / "index.html"
        if not file_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "index.html not found")
            return
        data = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            return {}
        raw_data = self.rfile.read(content_length).decode("utf-8")
        return json.loads(raw_data) if raw_data.strip() else {}

    def _handle_workflows(self) -> None:
        workflows = [{"name": name, "label": name} for name in WORKFLOW_REGISTRY.keys()]
        self._json_response({"workflows": workflows})

    def _handle_tools(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        model_id = (query.get("model_id") or [None])[0]
        try:
            validated_model_id = self._validate_model_id(model_id)
        except ValueError as exc:
            self._json_response({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        model_cfg = get_model_by_id(validated_model_id) if validated_model_id else get_default_model()
        llm = get_llm(model=model_cfg)
        tools = get_tools(llm)
        payload = {
            "tools": [
                {"name": tool.name, "description": tool.description}
                for tool in tools
            ]
        }
        self._json_response(payload)

    def _handle_models(self) -> None:
        self._json_response(
            {
                "default_model_id": DEFAULT_MODEL_ID,
                "models": list_models("huoshan"),
            }
        )

    @staticmethod
    def _validate_model_id(model_id: str | None) -> str | None:
        if not model_id:
            return None
        get_model_by_id(model_id)
        return model_id

    def _handle_run(self) -> None:
        try:
            body = self._read_json()
        except json.JSONDecodeError:
            self._json_response({"error": "invalid json"}, status=HTTPStatus.BAD_REQUEST)
            return

        user_input = str(body.get("input", "")).strip()
        workflow_name = str(body.get("workflow", MultiAgentWorkflow.name)).strip()
        enabled_tools = body.get("tools", [])
        history = body.get("history", [])
        model_id = str(body.get("model_id", "")).strip() or None
        try:
            model_id = self._validate_model_id(model_id)
        except ValueError as exc:
            self._json_response({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        if not user_input:
            self._json_response({"error": "input is required"}, status=HTTPStatus.BAD_REQUEST)
            return

        workflow_factory = WORKFLOW_REGISTRY.get(workflow_name)
        if workflow_factory is None:
            self._json_response(
                {"error": f"unknown workflow: {workflow_name}"},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        if not isinstance(enabled_tools, list) or not all(isinstance(t, str) for t in enabled_tools):
            self._json_response({"error": "tools must be a string list"}, status=HTTPStatus.BAD_REQUEST)
            return
        if not isinstance(history, list):
            self._json_response({"error": "history must be a list"}, status=HTTPStatus.BAD_REQUEST)
            return

        workflow = workflow_factory()
        composed_input = self._compose_input(history, user_input)
        try:
            result = workflow.run(
                user_input=composed_input,
                stream=False,
                enabled_tool_names=enabled_tools,
                model_id=model_id,
            )
        except Exception as exc:  # noqa: BLE001
            self._json_response(
                {"error": "workflow execution failed", "detail": str(exc)},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            return

        self._json_response(
            {
                "message": {
                    "user": user_input,
                    "assistant": result.get("final", ""),
                },
                "result": result,
            }
        )

    def _handle_chat_stream(self) -> None:
        try:
            body = self._read_json()
        except json.JSONDecodeError:
            self._json_response({"error": "invalid json"}, status=HTTPStatus.BAD_REQUEST)
            return

        user_input = str(body.get("input", "")).strip()
        workflow_name = str(body.get("workflow", MultiAgentWorkflow.name)).strip()
        enabled_tools = body.get("tools", [])
        history = body.get("history", [])
        model_id = str(body.get("model_id", "")).strip() or None
        try:
            model_id = self._validate_model_id(model_id)
        except ValueError as exc:
            self._json_response({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        if not user_input:
            self._json_response({"error": "input is required"}, status=HTTPStatus.BAD_REQUEST)
            return
        workflow_factory = WORKFLOW_REGISTRY.get(workflow_name)
        if workflow_factory is None:
            self._json_response({"error": f"unknown workflow: {workflow_name}"}, status=HTTPStatus.BAD_REQUEST)
            return
        if not isinstance(enabled_tools, list) or not all(isinstance(t, str) for t in enabled_tools):
            self._json_response({"error": "tools must be a string list"}, status=HTTPStatus.BAD_REQUEST)
            return
        if not isinstance(history, list):
            self._json_response({"error": "history must be a list"}, status=HTTPStatus.BAD_REQUEST)
            return

        composed_input = self._compose_input(history, user_input)
        workflow = workflow_factory()
        queue: Queue[dict[str, Any]] = Queue()

        def sink(event: dict[str, Any]) -> None:
            queue.put(event)

        def worker() -> None:
            try:
                workflow.run_streaming(
                    user_input=composed_input,
                    enabled_tool_names=enabled_tools,
                    event_sink=sink,
                    model_id=model_id,
                )
            except Exception as exc:  # noqa: BLE001
                queue.put({"type": "error", "error": "workflow execution failed", "detail": str(exc)})
            finally:
                queue.put({"type": "__end__"})

        threading.Thread(target=worker, daemon=True).start()

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        while True:
            try:
                event = queue.get(timeout=0.2)
            except Empty:
                continue
            line = json.dumps(event, ensure_ascii=False).encode("utf-8") + b"\n"
            self.wfile.write(line)
            self.wfile.flush()
            if event.get("type") == "__end__":
                break

    @staticmethod
    def _compose_input(history: list[Any], user_input: str) -> str:
        valid_history = [
            item for item in history
            if isinstance(item, dict)
            and isinstance(item.get("user"), str)
            and isinstance(item.get("assistant"), str)
        ]
        if not valid_history:
            return user_input

        lines: list[str] = []
        for item in valid_history[-8:]:
            lines.append(f"用户：{item['user']}")
            lines.append(f"助手：{item['assistant']}")
        lines.append(f"用户：{user_input}")
        return "\n".join(lines)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._serve_index()
            return
        if parsed.path == "/api/workflows":
            self._handle_workflows()
            return
        if parsed.path == "/api/tools":
            self._handle_tools()
            return
        if parsed.path == "/api/models":
            self._handle_models()
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/chat_stream":
            self._handle_chat_stream()
            return
        if parsed.path in {"/api/run", "/api/chat"}:
            self._handle_run()
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Start HTTP server."""
    server = ThreadingHTTPServer((host, port), AgentHTTPRequestHandler)
    print(f"Server started at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()
