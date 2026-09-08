import os

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="grounded-support-agent")


class Health(BaseModel):
    status: str
    version: str


@app.get("/health")
def health() -> Health:
    return Health(status="ok", version=os.environ.get("GIT_SHA", "dev"))
