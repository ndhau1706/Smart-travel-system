from __future__ import annotations

from fastapi import FastAPI

from routers.blog import router as blog_router


app = FastAPI(title="Blog + Voucher Service", version="1.0.0")

app.include_router(blog_router)
