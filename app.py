"""Pokédex Explorer — a small Flask app over the public PokéAPI.

Search a Pokémon by name or National Dex number and show its types,
abilities, base stats and official artwork. No API key is required.
"""
import os

import requests
from flask import Flask, render_template, request

app = Flask(__name__)

POKEAPI_URL = os.getenv("POKEAPI_URL", "https://pokeapi.co/api/v2/pokemon")
APP_VERSION = os.getenv("APP_VERSION", "dev")


def fetch_pokemon(query: str) -> dict:
    """Return a compact dict for one Pokémon, or raise LookupError / RuntimeError."""
    response = requests.get(f"{POKEAPI_URL}/{query.lower()}", timeout=10)
    if response.status_code == 404:
        raise LookupError(f"No Pokémon called '{query}'.")
    if response.status_code != 200:
        raise RuntimeError(f"PokéAPI error: HTTP {response.status_code}")

    data = response.json()
    artwork = (
        data.get("sprites", {})
        .get("other", {})
        .get("official-artwork", {})
        .get("front_default")
    ) or data.get("sprites", {}).get("front_default")

    return {
        "id": data["id"],
        "name": data["name"].title(),
        "height_m": round(data["height"] / 10, 1),
        "weight_kg": round(data["weight"] / 10, 1),
        "types": [t["type"]["name"] for t in data["types"]],
        "abilities": [a["ability"]["name"].replace("-", " ") for a in data["abilities"]],
        "stats": {s["stat"]["name"]: s["base_stat"] for s in data["stats"]},
        "artwork": artwork,
    }


@app.route("/", methods=["GET", "POST"])
def home():
    pokemon = None
    error = None

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        if not query:
            error = "Please enter a Pokémon name or number."
        else:
            try:
                pokemon = fetch_pokemon(query)
            except LookupError as exc:
                error = str(exc)
            except (RuntimeError, requests.RequestException) as exc:
                error = f"Could not reach PokéAPI: {exc}"

    return render_template("index.html", pokemon=pokemon, error=error, version=APP_VERSION)


@app.route("/health")
def health():
    """Liveness/readiness endpoint for Docker and Kubernetes probes."""
    return {"status": "ok", "version": APP_VERSION}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
