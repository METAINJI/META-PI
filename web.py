from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

with open("pi.txt") as f:
    PI = f.read().replace("\n", "")

CONTEXT = 10

app = FastAPI()

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/search")
def search(q: str):

    pos = PI.find(q)

    if pos == -1:
        return {"found": False}

    start = max(0, pos - CONTEXT)
    end = pos + len(q) + CONTEXT

    context = PI[start:end]

    return {
        "found": True,
        "position": pos,
        "context": context
    }


@app.get("/digit")
def digit(position: int):

    digit = PI[position]

    start = max(0, pos - CONTEXT)
end = pos + len(q) + CONTEXT

context = PI[start:end]

return {
    "found": True,
    "position": pos,
    "context": context,
    "start": start
}
