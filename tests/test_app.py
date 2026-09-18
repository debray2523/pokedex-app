"""Tests run without network: PokéAPI responses are mocked."""
from unittest.mock import Mock, patch

import pytest

import app as pokedex

SAMPLE = {
    "id": 25, "name": "pikachu", "height": 4, "weight": 60,
    "types": [{"type": {"name": "electric"}}],
    "abilities": [{"ability": {"name": "static"}}, {"ability": {"name": "lightning-rod"}}],
    "stats": [{"stat": {"name": "hp"}, "base_stat": 35}, {"stat": {"name": "speed"}, "base_stat": 90}],
    "sprites": {"front_default": "sprite.png",
                "other": {"official-artwork": {"front_default": "art.png"}}},
}


@pytest.fixture
def client():
    pokedex.app.config["TESTING"] = True
    return pokedex.app.test_client()


def _mock_response(status, payload=None):
    m = Mock()
    m.status_code = status
    m.json.return_value = payload or {}
    return m


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_home_renders_form(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"Pok" in r.data and b"<form" in r.data


@patch("app.requests.get", return_value=_mock_response(200, SAMPLE))
def test_fetch_pokemon_shapes_data(_):
    p = pokedex.fetch_pokemon("Pikachu")
    assert p["id"] == 25 and p["name"] == "Pikachu"
    assert p["height_m"] == 0.4 and p["weight_kg"] == 6.0
    assert p["types"] == ["electric"]
    assert p["abilities"] == ["static", "lightning rod"]
    assert p["stats"] == {"hp": 35, "speed": 90}
    assert p["artwork"] == "art.png"


@patch("app.requests.get", return_value=_mock_response(404))
def test_unknown_pokemon_raises_lookup_error(_):
    with pytest.raises(LookupError):
        pokedex.fetch_pokemon("missingno")


@patch("app.requests.get", return_value=_mock_response(200, SAMPLE))
def test_search_shows_result(_, client):
    r = client.post("/", data={"query": "pikachu"})
    assert r.status_code == 200
    assert b"Pikachu" in r.data and b"electric" in r.data


@patch("app.requests.get", return_value=_mock_response(404))
def test_search_shows_error(_, client):
    r = client.post("/", data={"query": "missingno"})
    assert b"No Pok" in r.data


def test_empty_query_shows_message(client):
    r = client.post("/", data={"query": "   "})
    assert b"Please enter" in r.data
