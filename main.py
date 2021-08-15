import re
from typing import Optional
from matplotlib.pyplot import text
from requests.api import request
import seaborn as sns
import pandas as pd

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from load_data_script import load_data_assemble_output

templates = Jinja2Templates('templates')


app = FastAPI()

df = sns.load_dataset('tips')


@app.get("/", response_class=HTMLResponse())
async def root(request: Request):
    # return {"message": "Hello World"}
    table_html = """<p> No data to display.</p>"""
    return templates.TemplateResponse('index.html', {'request': request, 'table_to_show': table_html})


@app.post("/load_data/", response_class=HTMLResponse)
def load_data(request: Request, textarea_tickers: Optional[str] = Form(None)):
    print("CALL")
    if textarea_tickers:
        tickers = [x.strip().upper() for x in textarea_tickers.split(",")]
    else:
        print("===EMPTY???")
        return RedirectResponse("/", status_code=302)


    table, tickers = load_data_assemble_output(tickers)
    table_html = table.to_html(classes=('table', 'is-narrow', "is-hoverable"))
    return templates.TemplateResponse('index.html', {'request': request, 'table_to_show': table_html, 'tickers': ", ".join(tickers)})
    # return "got post"
