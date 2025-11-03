import requests


def fetch_paper_by_pmid(pmid: str):
    """
    Fetch metadata for a PubMed paper from EuropePMC by PMID.
    Returns normalized fields ready for Supabase storage.
    """

    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:{pmid}&format=json"

    try:
        r = requests.get(url, timeout=10)
    except Exception as e:
        print(f"[EuropePMC] Request failed for PMID {pmid}: {e}")
        return None

    if r.status_code != 200:
        print(f"[EuropePMC] Non-200 response {r.status_code} for PMID {pmid}")
        return None

    try:
        data = r.json()
    except Exception as e:
        print(f"[EuropePMC] JSON parse error for PMID {pmid}: {e}")
        return None

    result = data.get("resultList", {}).get("result", [])
    if not result:
        print(f"[EuropePMC] No result found for PMID {pmid}")
        return None

    p = result[0]

    # ✅ Normalize authors
    authors_raw = p.get("authorString", "") or ""
    authors_list = authors_raw.split(", ") if authors_raw else []

    # ✅ Normalize year to integer if possible
    year_raw = p.get("pubYear")
    year = None
    try:
        if year_raw:
            year = int(year_raw)
    except:
        year = None

    return {
        "pmid": pmid,
        "title": p.get("title") or "",
        "abstract": p.get("abstractText") or "",
        "journal": p.get("journalTitle") or "",
        "year": year,
        "authors": authors_list,    # ✅ JSON array for Supabase
        "authors_text": authors_raw  # ✅ raw author string also stored
    }
