from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

with open("pi.txt") as f:
    PI = f.read().replace("\n", "")

CONTEXT = 10

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

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

@app.get("/digit")
def digit(position: int):

    if position < 0 or position >= len(PI):
        return {"error": "범위 초과"}

    digit = PI[position]

    start = max(position - CONTEXT, 0)
    end = position + CONTEXT + 1

    context = PI[start:end]

    return {
        "position": position,
        "digit": digit,
        "context": context,
        "start": start
    }

MAX_RESULTS = 10000

@app.get("/search")
def search(q: str):

    positions = []
    start = 0
    count = 0

    while True:
        pos = PI.find(q, start)
        if pos == -1:
            break

        count += 1

        if len(positions) < MAX_RESULTS:
            positions.append(pos)

        if count > MAX_RESULTS:
            break

        start = pos + 1

    if count == 0:
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
        "count": "10000+" if count > MAX_RESULTS else count,
        "context": context,
        "position": pos,
        "start": start_ctx
    })
