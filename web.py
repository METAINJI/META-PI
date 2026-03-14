from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

with open("pi.txt") as f:
    PI = f.read().replace("\n", "")

CONTEXT = 10

app = FastAPI()

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/context")
def context(pos: int, length: int = 5):

    start = max(pos - 10, 0)
    end = pos + length + 10

    ctx = PI[start:end]

    return {
        "context": ctx,
        "start": start
    }

@app.get("/search")
def search(q: str):

    positions = []
    start = 0

    while True:
        pos = PI.find(q, start)
        if pos == -1:
            break

        positions.append(pos)
        start = pos + 1

    if not positions:
        return JSONResponse({
            "found": False
        })

    pos = positions[0]

    start_ctx = max(pos - 10, 0)
    end_ctx = pos + len(q) + 10

    context = PI[start_ctx:end_ctx]

    return JSONResponse({
        "found": True,
        "positions": positions,
        "count": len(positions),
        "context": context,
        "position": pos,
        "start": start_ctx
    })
