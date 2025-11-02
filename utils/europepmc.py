# utils/europepmc.py

import aiohttp


async def fetch_pmc_data(pmid: str):
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:{pmid}&format=json"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None

            data = await resp.json()
            result = data.get("resultList", {}).get("result", [])

            if not result:
                return None

            p = result[0]

            return {
                "title": p.get("title"),
                "abstract": p.get("abstractText"),
                "journal": p.get("journalTitle"),
                "year": p.get("pubYear"),
                "authors": p.get("authorString", "").split(", "),
            }
