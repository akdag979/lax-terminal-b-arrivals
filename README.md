# LAX Terminal B Arrivals Board

A full-screen, 16:9 Streamlit flight-information display modeled on the supplied blue LAX arrivals board. It shows live arrivals assigned to Tom Bradley International Terminal (Terminal B), including the West Gates.

## 1. Install

Python 3.9 or newer is supported; Python 3.11 or newer is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 2. Add the AirLabs key

Create a free personal API key at [AirLabs](https://airlabs.co/), then copy the example secret file:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` and replace `your-airlabs-key`. The real secret file is ignored by Git.

## 3. Run the display

```bash
streamlit run app.py
```

Open the local URL Streamlit prints, move the browser window to the LG display, and enter browser full-screen mode (`Control-Command-F` on macOS). Use the LG panel's 16:9 / Just Scan setting if the edges are cropped.

The board requests fresh data every five minutes, keeps the last successful response during short outages, rotates groups of 14 flights every 12 seconds, and updates its Los Angeles clock in the browser.

## Preview without an API key

Demo mode uses realistic sample flights and never contacts AirLabs:

```bash
FLIGHT_BOARD_DEMO=1 streamlit run app.py
```

The footer clearly labels demo data so it cannot be mistaken for live airport information.

## Tests

```bash
pytest -q
```

## Troubleshooting

- **Setup screen remains visible:** confirm `.streamlit/secrets.toml` exists and contains `AIRLABS_API_KEY`.
- **DATA DELAYED appears:** the app is showing its last successful response while AirLabs is unavailable or rate-limited.
- **No flights appear:** there may be no Terminal B arrivals in the rolling window from 30 minutes ago through four hours ahead.
- **A logo becomes text:** the airline's logo image was unavailable; flight data remains unaffected.
- **Browser controls are visible:** enter the browser's full-screen presentation mode, not merely a maximized window.
