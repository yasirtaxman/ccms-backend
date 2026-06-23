import time
from collections import defaultdict, deque
from asyncio import Lock
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.config import settings
from app.utils.responses import error_response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app); self.requests=defaultdict(deque); self.lock=Lock()

    async def dispatch(self, request, call_next):
        if not settings.RATE_LIMIT_ENABLED or request.url.path in {"/health", "/docs", "/openapi.json"}:
            return await call_next(request)
        ip=request.client.host if request.client else "unknown"; now=time.monotonic()
        async with self.lock:
            bucket=self.requests[ip]
            while bucket and bucket[0] <= now-60: bucket.popleft()
            if len(bucket) >= settings.RATE_LIMIT_PER_MINUTE:
                return JSONResponse(status_code=429, content=error_response("Rate limit exceeded", [{"message":"Too many requests","code":"rate_limited"}]), headers={"Retry-After":"60"})
            bucket.append(now)
        return await call_next(request)
