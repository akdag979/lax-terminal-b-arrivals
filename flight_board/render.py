from __future__ import annotations

import html
import json
import re
from datetime import datetime
from datetime import timedelta
from itertools import islice
from typing import Iterable, Sequence
from zoneinfo import ZoneInfo

from .models import Arrival

ROWS_PER_PAGE = 14


def format_time(value) -> str:
    return value.strftime("%I:%M %p").lstrip("0")


def display_status(arrival: Arrival) -> tuple[str, str]:
    status = arrival.raw_status.lower()
    if status in {"cancelled", "canceled"}:
        return "Cancelled", "cancelled"
    if arrival.actual is not None or status in {"landed", "arrived"}:
        return "Arrived", "arrived"
    if arrival.estimated is not None:
        difference = abs(arrival.estimated - arrival.scheduled)
        if difference >= timedelta(minutes=5):
            return f"New Time {format_time(arrival.estimated)}", "changed"
        if status in {"active", "en-route", "en_route"}:
            return "Estimated", "normal"
    return "On Time", "normal"


def paginate(items: Sequence[Arrival], size: int = ROWS_PER_PAGE) -> list[list[Arrival]]:
    iterator = iter(items)
    pages = list(iter(lambda: list(islice(iterator, size)), []))
    return pages or [[]]


def _safe(value: object) -> str:
    return html.escape(str(value), quote=True)


def _logo_cell(arrival: Arrival) -> str:
    code = re.sub(r"[^A-Z0-9]", "", arrival.airline_code.upper())[:3]
    fallback = _safe(arrival.airline_name or code or "Airline")
    if not code:
        return f'<span class="airline-fallback visible">{fallback}</span>'
    url = f"https://airlabs.co/img/airline/m/{code}.png"
    return (
        '<div class="airline-brand">'
        f'<img src="{url}" alt="{fallback}" '
        'onerror="this.hidden=true;this.nextElementSibling.classList.add(\'visible\')">'
        f'<span class="airline-fallback">{fallback}</span>'
        "</div>"
    )


def _row(arrival: Arrival) -> str:
    status_text, status_class = display_status(arrival)
    return (
        '<div class="flight-row">'
        f'<div class="cell time">{_safe(format_time(arrival.scheduled))}</div>'
        f'<div class="cell time">{_safe(format_time(arrival.best_time))}</div>'
        f'<div class="cell origin" title="{_safe(arrival.origin_name)}">{_safe(arrival.origin_name)}</div>'
        f'<div class="cell airline">{_logo_cell(arrival)}</div>'
        f'<div class="cell flight">{_safe(arrival.flight_number)}</div>'
        f'<div class="cell status {status_class}">{_safe(status_text)}</div>'
        "</div>"
    )


def render_board(
    arrivals: Sequence[Arrival],
    *,
    delayed: bool = False,
    demo: bool = False,
) -> str:
    pages = paginate(arrivals)
    rendered_pages = []
    for page_number, page in enumerate(pages):
        rows = "".join(_row(arrival) for arrival in page)
        missing = ROWS_PER_PAGE - len(page)
        if not page:
            rows = '<div class="empty-state">NO TERMINAL B ARRIVALS IN DISPLAY WINDOW</div>'
            missing = 0
        rows += '<div class="flight-row empty"></div>' * missing
        active = " active" if page_number == 0 else ""
        rendered_pages.append(
            f'<section class="flight-page{active}" data-page="{page_number}">{rows}</section>'
        )

    badges = []
    if delayed:
        badges.append('<span class="board-badge delayed">DATA DELAYED</span>')
    if demo:
        badges.append('<span class="board-badge demo">DEMO DATA</span>')
    badge_html = "".join(badges)
    page_count = len(pages)
    board_id = "lax-arrivals-board"
    initial_clock = datetime.now(ZoneInfo("America/Los_Angeles")).strftime(
        "%A %B %-d, %Y   %-I:%M %p"
    )
    return f"""
<style>
  :root {{ color-scheme: light; }}
  html, body, [data-testid="stAppViewContainer"], .stApp {{
    margin: 0 !important; padding: 0 !important; width: 100% !important;
    height: 100% !important; overflow: hidden !important; background: #004f75 !important;
  }}
  [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
  [data-testid="stStatusWidget"], footer, #MainMenu {{ display: none !important; }}
  [data-testid="stMain"] {{ padding: 0 !important; }}
  [data-testid="stMainBlockContainer"] {{
    padding: 0 !important; margin: 0 !important; max-width: none !important;
    width: 100% !important; height: 100% !important;
  }}
  #{board_id}, #{board_id} * {{ box-sizing: border-box; }}
  #{board_id} {{
    --header-blue: #004d78; --row-a: #005e86; --row-b: #08789f;
    --amber: #f1a43b; --white: #f7f8f8;
    position: fixed; inset: 0; z-index: 999999; width: 100vw; height: 100dvh;
    overflow: hidden; background: var(--header-blue); color: var(--white);
    font-family: "Arial Narrow", "Roboto Condensed", Arial, Helvetica, sans-serif;
    text-rendering: geometricPrecision;
  }}
  #{board_id} .top-header {{
    position: relative; height: 14.4vh; background: #fff; color: var(--header-blue);
  }}
  #{board_id} .lax-logo {{
    position: absolute; inset: 0 auto 0 1.3vw; display: flex; align-items: center;
    height: 100%; font-family: Arial Black, Arial, sans-serif;
    font-size: clamp(54px, 7.5vw, 144px); font-weight: 950; line-height: .8; letter-spacing: -.72vw;
  }}
  #{board_id} .lax-la {{ color: #0caccd; }}
  #{board_id} .lax-x {{ color: #242223; margin-left: .18em; }}
  #{board_id} .arrivals-title {{
    position: absolute; right: 2.1vw; top: 50%; transform: translateY(-50%);
    font-family: Arial, Helvetica, sans-serif; font-size: clamp(52px, 6.2vw, 119px);
    font-weight: 400; letter-spacing: .12vw; line-height: 1; white-space: nowrap;
  }}
  #{board_id} .column-header, #{board_id} .flight-row {{
    display: grid; grid-template-columns: 13% 14% 23% 17% 12% 21%; align-items: center;
  }}
  #{board_id} .column-header {{
    height: 5.6vh; background: #003f70; border-bottom: 1px solid rgba(255,255,255,.48);
    font-size: clamp(16px, 1.78vw, 35px); font-weight: 800; letter-spacing: .01em;
    text-align: center; text-shadow: 0 1px 1px #001d33;
  }}
  #{board_id} .column-header div:nth-child(3) {{ text-align: left; padding-left: 1.1vw; }}
  #{board_id} .pages {{ height: 68vh; position: relative; overflow: hidden; }}
  #{board_id} .flight-page {{
    position: absolute; inset: 0; opacity: 0; visibility: hidden; transition: opacity .5s ease;
  }}
  #{board_id} .flight-page.active {{ opacity: 1; visibility: visible; }}
  #{board_id} .flight-row {{
    height: calc(68vh / {ROWS_PER_PAGE}); background: var(--row-a); border-bottom: 1px solid rgba(0,37,64,.22);
    font-size: clamp(17px, 1.77vw, 34px); line-height: 1; text-shadow: 0 1px 1px rgba(0,0,0,.45);
  }}
  #{board_id} .flight-row:nth-child(even) {{ background: var(--row-b); }}
  #{board_id} .flight-row.empty .cell {{ visibility: hidden; }}
  #{board_id} .cell {{ min-width: 0; padding: 0 .55vw; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  #{board_id} .cell.time, #{board_id} .cell.flight {{ text-align: center; }}
  #{board_id} .cell.origin {{ padding-left: 1.1vw; }}
  #{board_id} .cell.airline {{ height: 100%; display: flex; align-items: center; justify-content: center; text-shadow: none; }}
  #{board_id} .airline-brand {{ width: 92%; height: 82%; display: flex; align-items: center; justify-content: center; }}
  #{board_id} .airline-brand img {{ max-width: 100%; max-height: 78%; object-fit: contain; }}
  #{board_id} .airline-fallback {{ display: none; color: #fff; font-size: .68em; text-align: center; font-weight: 700; text-shadow: 0 1px 1px #00324d; }}
  #{board_id} .airline-fallback.visible {{ display: inline; }}
  #{board_id} .cell.status {{ text-align: center; font-weight: 500; padding-left: .15vw; padding-right: .15vw; }}
  #{board_id} .cell.status.changed {{ color: var(--amber); text-shadow: 0 1px 1px #4f3100; }}
  #{board_id} .cell.status.cancelled {{ color: #fff; }}
  #{board_id} .cell.status.arrived {{ color: #b8f0c6; }}
  #{board_id} .empty-state {{
    height: 68vh; display: flex; align-items: center; justify-content: center; background: var(--row-a);
    font-size: clamp(26px, 2.6vw, 50px); letter-spacing: .04em;
  }}
  #{board_id} .footer-clock {{
    height: 10vh; display: flex; align-items: center; justify-content: center; position: relative;
    background: #004f75; font-size: clamp(25px, 2.55vw, 49px); font-weight: 700;
    text-shadow: 0 2px 2px rgba(0,0,0,.65); letter-spacing: .015em;
  }}
  #{board_id} .badges {{ position: absolute; left: 1.1vw; display: flex; gap: .55vw; align-items: center; }}
  #{board_id} .board-badge {{
    border: 1px solid rgba(255,255,255,.65); border-radius: .28vw; padding: .28em .55em;
    font-size: clamp(10px, .75vw, 15px); letter-spacing: .08em; text-shadow: none;
  }}
  #{board_id} .board-badge.delayed {{ background: #a72b25; }}
  #{board_id} .board-badge.demo {{ background: #a06a00; }}
  #{board_id} .page-dots {{
    position: absolute; right: 1.2vw; display: flex; gap: .45vw; opacity: {"1" if page_count > 1 else "0"};
  }}
  #{board_id} .page-dot {{ width: .5vw; min-width: 7px; aspect-ratio: 1; border-radius: 50%; background: rgba(255,255,255,.38); }}
  #{board_id} .page-dot.active {{ background: white; }}
  @media (max-aspect-ratio: 15/9) {{
    #{board_id} .flight-row {{ font-size: clamp(15px, 1.65vw, 31px); }}
  }}
</style>
<main id="{board_id}" role="application" aria-label="LAX Terminal B arrivals board">
  <header class="top-header">
    <div class="lax-logo" aria-label="LAX"><span class="lax-la">LA</span><span class="lax-x">X</span></div>
    <div class="arrivals-title">ARRIVALS</div>
  </header>
  <div class="column-header" role="row">
    <div>SCHEDULE</div><div>ESTIMATE</div><div>ORIGIN</div>
    <div>AIRLINE</div><div>FLIGHT</div><div>STATUS</div>
  </div>
  <div class="pages">{"".join(rendered_pages)}</div>
  <footer class="footer-clock">
    <div class="badges">{badge_html}</div>
    <time id="lax-board-clock">{_safe(initial_clock)}</time>
    <div class="page-dots">{"".join(f'<i class="page-dot{" active" if i == 0 else ""}"></i>' for i in range(page_count))}</div>
  </footer>
</main>
<script>
(() => {{
  const frame = window.frameElement;
  if (frame) {{
    const viewportHeight = window.parent.innerHeight;
    Object.assign(frame.style, {{
      position: "fixed", inset: "0", width: "100vw", height: `${{viewportHeight}}px`,
      border: "0", zIndex: "999999", display: "block"
    }});
    frame.setAttribute("height", String(viewportHeight));
    frame.setAttribute("scrolling", "no");
  }}
  const board = document.getElementById({json.dumps(board_id)});
  if (!board || board.dataset.ready === "1") return;
  board.dataset.ready = "1";
  const clock = board.querySelector("#lax-board-clock");
  const pages = [...board.querySelectorAll(".flight-page")];
  const dots = [...board.querySelectorAll(".page-dot")];
  let page = 0;
  const updateClock = () => {{
    const parts = new Intl.DateTimeFormat("en-US", {{
      timeZone: "America/Los_Angeles", weekday: "long", month: "long",
      day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit", hour12: true
    }}).formatToParts(new Date());
    const value = (type) => parts.find(p => p.type === type)?.value || "";
    clock.textContent = `${{value("weekday")}} ${{value("month")}} ${{value("day")}}, ${{value("year")}}   ${{value("hour")}}:${{value("minute")}} ${{value("dayPeriod")}}`;
  }};
  updateClock();
  const clockTimer = window.setInterval(updateClock, 15000);
  if (pages.length > 1) {{
    const pageTimer = window.setInterval(() => {{
      pages[page].classList.remove("active"); dots[page]?.classList.remove("active");
      page = (page + 1) % pages.length;
      pages[page].classList.add("active"); dots[page]?.classList.add("active");
    }}, 12000);
    board._pageTimer = pageTimer;
  }}
  board._clockTimer = clockTimer;
}})();
</script>
"""


def render_setup(message: str) -> str:
    return f"""
<style>
  html, body, .stApp {{ margin:0 !important; padding:0 !important; overflow:hidden !important; }}
  [data-testid="stHeader"], [data-testid="stToolbar"], footer, #MainMenu {{ display:none !important; }}
  .setup-screen {{ position:fixed; inset:0; z-index:999999; display:flex; align-items:center; justify-content:center;
    background:#004f75; color:white; font-family:Arial,sans-serif; }}
  .setup-card {{ width:min(720px,78vw); padding:52px; background:white; color:#063f63; border-radius:12px;
    box-shadow:0 22px 70px rgba(0,0,0,.32); text-align:center; }}
  .setup-card h1 {{ margin:0 0 18px; font-size:48px; }}
  .setup-card p {{ font-size:21px; line-height:1.5; }}
  .setup-card code {{ display:block; margin:22px 0; padding:18px; background:#eaf3f7; font-size:18px; }}
</style>
<main class="setup-screen"><section class="setup-card">
  <h1>LAX ARRIVALS</h1><p>{_safe(message)}</p>
  <code>AIRLABS_API_KEY = "your-key"</code>
  <p>Add the key to <strong>.streamlit/secrets.toml</strong>, then reload this page.</p>
</section></main>
<script>
  const frame = window.frameElement;
  if (frame) {{
    const viewportHeight = window.parent.innerHeight;
    Object.assign(frame.style, {{ position:"fixed", inset:"0", width:"100vw", height:`${{viewportHeight}}px`,
      border:"0", zIndex:"999999", display:"block" }});
    frame.setAttribute("height", String(viewportHeight));
    frame.setAttribute("scrolling", "no");
  }}
</script>
"""

