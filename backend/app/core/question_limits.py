"""Bounded, process-local controls for the private question endpoint only."""

from collections import deque
from time import monotonic

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class QuestionLimits:
    def __init__(self, app: ASGIApp):
        self.app = app
        self.requests: dict[str, deque[float]] = {}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope["path"] != "/api/v1/questions"
            or scope["method"] != "POST"
        ):
            await self.app(scope, receive, send)
            return

        now = monotonic()
        self.requests = {
            key: values
            for key, values in self.requests.items()
            if values and values[-1] > now - 60
        }
        # Never trust user-supplied forwarded headers. No question content enters
        # this bounded memory. This is not a distributed/public-deployment limiter.
        client = scope.get("client")
        key = client[0] if client else "unknown"
        if key not in self.requests and len(self.requests) >= 1024:
            await JSONResponse(
                {"detail": "Question service busy"},
                503,
                headers={"Cache-Control": "no-store"},
            )(scope, receive, send)
            return
        window = self.requests.setdefault(key, deque())
        while window and window[0] <= now - 60:
            window.popleft()
        if len(window) >= 12:
            await JSONResponse(
                {"detail": "Please wait before submitting another question"},
                429,
                headers={"Cache-Control": "no-store", "Retry-After": "60"},
            )(scope, receive, send)
            return
        window.append(now)

        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > 16_384:
                await JSONResponse(
                    {"detail": "Request body too large"},
                    413,
                    headers={"Cache-Control": "no-store"},
                )(scope, receive, send)
                return
            if not message.get("more_body", False):
                break

        consumed = False

        async def replay() -> Message:
            nonlocal consumed
            if not consumed:
                consumed = True
                return {"type": "http.request", "body": bytes(body)}
            return await receive()

        await self.app(scope, replay, send)
