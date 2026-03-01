import httpx
import asyncio
import json

async def test_analyze_api():
    url = "http://127.0.0.1:8000/api/analyze"
    headers = {"Content-Type": "application/json"}
    payload = {
        "countries": ["USA", "IND", "JPN"],
        "risk_tolerance": "moderate",
        "duration": "long-term"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client: # Increased timeout to 30 seconds
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            print("API Response:")
            print(json.dumps(response.json(), indent=2))
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        print(f"Request error occurred: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(test_analyze_api())
