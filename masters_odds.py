import requests
import json

API_KEY = "97cb8b654ed9acfd64eeb7e6e5837ed7"

url = "https://api.the-odds-api.com/v4/sports/golf_masters_tournament_winner/odds"

params = {
    "apiKey": API_KEY,
    "regions": "us",
    "markets": "outrights",
    "oddsFormat": "american",
    "bookmakers": "draftkings"  # Single bookmaker = costs only 1 credit
}

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    
    print(f"Requests remaining: {response.headers.get('x-requests-remaining')}")
    print(f"Requests used: {response.headers.get('x-requests-used')}")
    print(f"This call cost: {response.headers.get('x-requests-last')}\n")
    
    # Extract and sort players by odds (favorites first)
    players = []
    for event in data:
        for bookmaker in event.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                if market["key"] == "outrights":
                    for outcome in market["outcomes"]:
                        players.append({
                            "name": outcome["name"],
                            "odds": outcome["price"]
                        })
    
    # Sort: negatives (favorites) first, then positives ascending
    players.sort(key=lambda x: (x["odds"] >= 0, abs(x["odds"])))
    
    print(f"Total players found: {len(players)}\n")
    print(f"{'Rank':<6} {'Player':<30} {'Odds':<10}")
    print("-" * 46)
    for i, p in enumerate(players, 1):
        odds_str = f"+{p['odds']}" if p['odds'] > 0 else str(p['odds'])
        print(f"{i:<6} {p['name']:<30} {odds_str:<10}")
    
    # Also save clean JSON for pasting into Claude
    with open("masters_odds.json", "w") as f:
        json.dump(players, f, indent=2)
    
    print(f"\n✅ Full data saved to masters_odds.json")

else:
    print(f"Error {response.status_code}: {response.text}")

