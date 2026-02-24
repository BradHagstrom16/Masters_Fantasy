import requests
import json
from collections import defaultdict
from statistics import median

API_KEY = "97cb8b654ed9acfd64eeb7e6e5837ed7"

url = "https://api.the-odds-api.com/v4/sports/golf_masters_tournament_winner/odds"

# Pull ALL bookmakers for maximum player coverage
# Note: "us" region with no bookmaker filter costs more credits but gets every player
params = {
    "apiKey": API_KEY,
    "regions": "us,uk,eu,au",       # All regions for maximum coverage
    "markets": "outrights",
    "oddsFormat": "american",
    # No "bookmakers" filter = pull from ALL available books
}

print("Fetching 2026 Masters odds from ALL bookmakers across all regions...")
print("(This will use more API credits but maximizes player coverage)\n")

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    
    remaining = response.headers.get('x-requests-remaining', '?')
    used = response.headers.get('x-requests-used', '?')
    cost = response.headers.get('x-requests-last', '?')
    print(f"API Credits — Remaining: {remaining} | Used: {used} | This call: {cost}\n")
    
    # Collect ALL odds per player across ALL bookmakers
    player_odds = defaultdict(list)   # name -> [list of american odds from each book]
    player_books = defaultdict(list)  # name -> [list of bookmaker names]
    
    for event in data:
        for bookmaker in event.get("bookmakers", []):
            book_name = bookmaker.get("title", bookmaker.get("key", "unknown"))
            for market in bookmaker.get("markets", []):
                if market["key"] == "outrights":
                    for outcome in market["outcomes"]:
                        name = outcome["name"]
                        odds = outcome["price"]
                        player_odds[name].append(odds)
                        player_books[name].append(book_name)
    
    print(f"Total unique players found across all books: {len(player_odds)}\n")
    
    # --- Helper: Convert American odds to implied probability ---
    def american_to_implied_prob(odds):
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)
    
    def implied_prob_to_american(prob):
        if prob >= 0.5:
            return round(-prob / (1 - prob) * 100)
        else:
            return round((1 - prob) / prob * 100)
    
    # --- Build consensus odds per player ---
    # Use MEDIAN implied probability across all books, then convert back to American
    players = []
    for name, odds_list in player_odds.items():
        probs = [american_to_implied_prob(o) for o in odds_list]
        median_prob = median(probs)
        consensus_american = implied_prob_to_american(median_prob)
        
        players.append({
            "name": name,
            "consensus_odds": consensus_american,
            "implied_prob": round(median_prob * 100, 2),
            "num_books": len(odds_list),
            "books": sorted(set(player_books[name])),
            "min_odds": min(odds_list),
            "max_odds": max(odds_list),
            "all_odds": sorted(odds_list),
        })
    
    # Sort: favorites first (lowest consensus odds = highest implied prob)
    players.sort(key=lambda x: -x["implied_prob"])
    
    # --- Print summary ---
    print(f"{'Rank':<5} {'Player':<30} {'Consensus':<12} {'Impl%':<8} {'Books':<6} {'Range'}")
    print("-" * 90)
    for i, p in enumerate(players, 1):
        odds_str = f"+{p['consensus_odds']}" if p['consensus_odds'] > 0 else str(p['consensus_odds'])
        min_str = f"+{p['min_odds']}" if p['min_odds'] > 0 else str(p['min_odds'])
        max_str = f"+{p['max_odds']}" if p['max_odds'] > 0 else str(p['max_odds'])
        print(f"{i:<5} {p['name']:<30} {odds_str:<12} {p['implied_prob']:<8} {p['num_books']:<6} {min_str} to {max_str}")
    
    # --- Save full detailed JSON ---
    with open("masters_odds_2026_detailed.json", "w") as f:
        json.dump(players, f, indent=2)
    
    # --- Save clean/simple JSON (just name + consensus odds for Claude analysis) ---
    simple = [{"name": p["name"], "odds": p["consensus_odds"], "implied_prob": p["implied_prob"]} 
              for p in players]
    with open("masters_odds_2026.json", "w") as f:
        json.dump(simple, f, indent=2)
    
    print(f"\n✅ Detailed data saved to masters_odds_2026_detailed.json")
    print(f"✅ Clean data saved to masters_odds_2026.json")
    print(f"\n📊 Summary:")
    print(f"   Total players: {len(players)}")
    print(f"   Bookmakers sampled: {len(set(b for books in player_books.values() for b in books))}")
    
    # List bookmakers found
    all_books = sorted(set(b for books in player_books.values() for b in books))
    print(f"   Books: {', '.join(all_books)}")
    
    # Coverage stats
    single_book = sum(1 for p in players if p["num_books"] == 1)
    multi_book = sum(1 for p in players if p["num_books"] > 1)
    print(f"   Players with 1 book only: {single_book}")
    print(f"   Players with 2+ books: {multi_book}")

elif response.status_code == 422:
    print("⚠️  2026 Masters odds may not be available yet.")
    print(f"Response: {response.text}")
    print("\nTip: Check available sports with:")
    print(f"  https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}")
    
else:
    print(f"Error {response.status_code}: {response.text}")
