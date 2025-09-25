import unittest
from typing import Iterable

from fastapi.testclient import TestClient
from mcp.server.streamable_http import StreamableHTTPServerTransport
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from src.utils.server_config import mcp


def _create_app():
    app = mcp.http_app(path="/mcp")

    async def control_route(request: Request):
        return JSONResponse({"accept": request.headers.get("accept")})

    app.router.routes.append(Route("/control", control_route, methods=["GET"]))
    return app


class MCPAcceptHeaderTests(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.captured: list[str | None] = []
        original = StreamableHTTPServerTransport._check_accept_headers

        def recorder(transport, request):  # type: ignore[no-untyped-def]
            self.captured.append(request.headers.get("accept"))
            return original(transport, request)

        StreamableHTTPServerTransport._check_accept_headers = recorder
        self.addCleanup(
            lambda: setattr(
                StreamableHTTPServerTransport,
                "_check_accept_headers",
                original,
            )
        )

    def _exercise_case(
        self,
        accept_header: str | None,
        expected_control: str,
        expected_entries: Iterable[str],
    ) -> None:
        headers = {}
        if accept_header is not None:
            headers["Accept"] = accept_header

        self.captured.clear()
        with TestClient(_create_app()) as client:
            client.post(
                "/mcp",
                headers=headers,
                json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            )

            self.assertTrue(self.captured, "Accept header was not inspected by MCP handler")
            mutated_header = self.captured[-1] or ""
            mutated_entries = {part.strip() for part in mutated_header.split(",") if part.strip()}
            for entry in expected_entries:
                self.assertIn(entry, mutated_entries)

            control_response = client.get("/control", headers=headers)
            self.assertEqual(control_response.json()["accept"], expected_control)

    def test_accept_header_mutations(self) -> None:
        scenarios = [
            (None, "*/*", ("application/json", "text/event-stream")),
            ("application/json", "application/json", ("application/json", "text/event-stream")),
            (
                "application/json;q=0.5",
                "application/json;q=0.5",
                ("application/json;q=0.5", "text/event-stream"),
            ),
            ("text/event-stream", "text/event-stream", ("application/json", "text/event-stream")),
        ]

        for accept_header, expected_control, expected_entries in scenarios:
            with self.subTest(accept_header=accept_header):
                self._exercise_case(accept_header, expected_control, expected_entries)


if __name__ == "__main__":
    unittest.main()
