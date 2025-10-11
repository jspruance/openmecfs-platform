"""
Open ME/CFS API Regression Tests — Phase 4
-------------------------------------------
Quick regression tests for /papers endpoints
to ensure all core routes work after DB or model updates.

Run with:
    pytest -v
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ------------------------------------------------------------
# 1️⃣ Base List Endpoint
# ------------------------------------------------------------
def test_list_papers_basic():
    res = client.get("/papers")
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert data["count"] <= data["limit"]


def test_list_papers_sorting():
    res = client.get("/papers?sort=title&order=asc&limit=5")
    assert res.status_code == 200
    data = res.json()
    assert len(data["results"]) <= 5


# ------------------------------------------------------------
# 2️⃣ Single Paper Endpoint
# ------------------------------------------------------------
# replace with real PMIDs from your Supabase table
@pytest.mark.parametrize("pmid", ["40627437", "40635708"])
def test_get_paper_valid(pmid):
    res = client.get(f"/papers/{pmid}")
    assert res.status_code == 200
    data = res.json()
    assert "paper" in data
    assert "summaries" in data


def test_get_paper_invalid():
    res = client.get("/papers/00000000")
    assert res.status_code in [404, 200]  # 404 = expected if not found


# ------------------------------------------------------------
# 3️⃣ Search Endpoint
# ------------------------------------------------------------
@pytest.mark.parametrize(
    "query,author,year",
    [
        ("fatigue", None, None),
        ("immune", "Smith", None),
        ("COVID", None, 2024),
    ],
)
def test_search_papers(query, author, year):
    params = {"q": query}
    if author:
        params["author"] = author
    if year:
        params["year"] = year

    res = client.get("/papers/search", params=params)
    assert res.status_code == 200
    data = res.json()
    assert "results" in data or "message" in data


def test_search_empty_query():
    res = client.get("/papers/search?q=")
    assert res.status_code == 200
    assert "results" in res.json() or "message" in res.json()


# ------------------------------------------------------------
# 4️⃣ Suggest Endpoint
# ------------------------------------------------------------
@pytest.mark.parametrize("query", ["fatigue", "encephalomyelitis", "energy"])
def test_suggest_endpoint(query):
    res = client.get("/papers/suggest", params={"q": query})
    assert res.status_code == 200
    data = res.json()
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)
    if data["suggestions"]:
        assert "title" in data["suggestions"][0]


# ------------------------------------------------------------
# 5️⃣ Metadata Endpoint
# ------------------------------------------------------------
def test_meta_endpoint():
    res = client.get("/papers/meta")
    assert res.status_code == 200
    data = res.json()
    assert any(
        k in data for k in ["file_name", "message"]
    ), "Meta endpoint should return dataset info or a not-found message"
