# utils/europepmc.py

import requests


def fetch_pmc_data(pmid: str):
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
        print(f"[EuropePMC] Failed to parse JSON for PMID {pmid}: {e}")
        return None

    result = data.get("resultList", {}).get("result", [])
    if not result:
        print(f"[EuropePMC] No result found on EuropePMC for PMID {pmid}")
        return None

    p = result[0]

    return {
        "title": p.get("title"),
        "abstract": p.get("abstractText"),
        "journal": p.get("journalTitle"),
        "year": p.get("pubYear"),
        # Ensure authors is always a list
        "authors": p.get("authorString", "").split(", ") if p.get("authorString") else [],
    }
