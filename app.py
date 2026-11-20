from __future__ import annotations

import os

import streamlit as st
import streamlit.components.v1 as components

from flight_board.airlabs import AirLabsError, fetch_arrivals
from flight_board.demo import demo_arrivals
from flight_board.render import render_board, render_setup

st.set_page_config(page_title="LAX Terminal B Arrivals", page_icon="✈", layout="wide")


def _secret(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
    except (FileNotFoundError, KeyError):
        value = ""
    return str(value or os.getenv(name, "")).strip()


API_KEY = _secret("AIRLABS_API_KEY")
DEMO_MODE = os.getenv("FLIGHT_BOARD_DEMO", "").lower() in {"1", "true", "yes"}


@st.cache_data(ttl=280, show_spinner=False)
def _cached_arrivals(api_key: str):
    return fetch_arrivals(api_key)


if "last_good_arrivals" not in st.session_state:
    st.session_state.last_good_arrivals = []


@st.fragment(run_every="5m")
def live_board() -> None:
    delayed = False
    if DEMO_MODE:
        arrivals = demo_arrivals()
    else:
        try:
            arrivals = _cached_arrivals(API_KEY)
            st.session_state.last_good_arrivals = arrivals
        except AirLabsError:
            arrivals = st.session_state.last_good_arrivals
            delayed = bool(arrivals)
            if not arrivals:
                components.html(
                    render_setup("The live flight service could not be reached."),
                    height=900,
                    scrolling=False,
                )
                return

    components.html(
        render_board(arrivals, delayed=delayed, demo=DEMO_MODE),
        height=1080,
        scrolling=False,
    )


if not API_KEY and not DEMO_MODE:
    components.html(
        render_setup("An AirLabs API key is required for live Terminal B flight data."),
        height=900,
        scrolling=False,
    )
else:
    live_board()

