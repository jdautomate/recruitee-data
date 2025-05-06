import httpx

from server_config import RECRUITEE_COMPANY_ID, RECRUITEE_API_TOKEN, mcp



@mcp.tool()
async def list_candidates() -> dict:
    """
    Lists all candidates from the Recruitee API using pagination.
    """
    base_url = f"https://api.recruitee.com/c/{RECRUITEE_COMPANY_ID}/candidates"
    headers = {
        "Authorization": f"Bearer {RECRUITEE_API_TOKEN}"
    }
    limit = 100  # Adjust as needed; Recruitee may have a maximum limit
    offset = 0
    all_candidates = []

    async with httpx.AsyncClient() as client:
        while True:
            params = {"limit": limit, "offset": offset}
            response = await client.get(base_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                break
            all_candidates.extend(candidates)
            offset += limit

    return {"candidates": all_candidates}