#!/usr/bin/env python3
"""Generate sample data for dashboard preview/testing."""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)

# Generate 60 days of history
history = []
base_date = datetime(2026, 1, 17)

# Starting values
btc_price = 78000
exchange_btc = 145000
etf_btc = 52000
institution_btc = 28000
unknown_btc = 85000

for i in range(60):
    d = base_date + timedelta(days=i)
    
    # Random walk
    btc_price += random.uniform(-2000, 2500)
    btc_price = max(65000, min(95000, btc_price))
    exchange_btc += random.uniform(-800, 600)
    etf_btc += random.uniform(-200, 500)
    institution_btc += random.uniform(-100, 200)
    unknown_btc += random.uniform(-400, 300)
    
    total = exchange_btc + etf_btc + institution_btc + unknown_btc
    supply = 19850000
    
    # Sort top N from total
    top10 = total * 0.032 + random.uniform(-500, 500)
    top20 = total * 0.055 + random.uniform(-800, 800)
    top50 = total * 0.11 + random.uniform(-1000, 1000)
    
    history.append({
        "date": d.strftime("%Y-%m-%d"),
        "btc_price": round(btc_price, 2),
        "total_tracked_btc": round(total, 2),
        "total_tracked_pct": round(total / supply * 100, 4),
        "top10_pct": round(top10 / supply * 100, 4),
        "top20_pct": round(top20 / supply * 100, 4),
        "top50_pct": round(top50 / supply * 100, 4),
        "exchange_btc": round(exchange_btc, 2),
        "etf_btc": round(etf_btc, 2),
        "institution_btc": round(institution_btc, 2),
        "unknown_btc": round(unknown_btc, 2),
        "exchange_pct": round(exchange_btc / supply * 100, 4),
        "etf_pct": round(etf_btc / supply * 100, 4),
        "institution_pct": round(institution_btc / supply * 100, 4),
        "unknown_pct": round(unknown_btc / supply * 100, 4),
    })

with open(DATA_DIR / "whale_history.json", "w") as f:
    json.dump(history, f, indent=2)

# Latest snapshot with address details
addresses = {
    "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo": {"label": "Binance Cold Wallet", "category": "exchange", "balance_btc": 248597, "balance_usd": 21893336000, "tx_count": 15420, "funded_count": 8200, "spent_count": 7220, "last_outgoing_ts": 1710000000, "days_dormant": 3},
    "bc1qm34lsc65zpw79lxes69zkqmk6ee3ewf0j77s3h": {"label": "Binance Cold 2", "category": "exchange", "balance_btc": 59000, "balance_usd": 5200000000, "tx_count": 5800, "funded_count": 3200, "spent_count": 2600, "last_outgoing_ts": 1710500000, "days_dormant": 2},
    "39884E3j6KZj82FK4vcCrkUvWYL5MQaS3v": {"label": "Coinbase Cold", "category": "exchange", "balance_btc": 32000, "balance_usd": 2816000000, "tx_count": 3200, "funded_count": 1800, "spent_count": 1400, "last_outgoing_ts": 1709000000, "days_dormant": 14},
    "3Kzh9qAqVWQhEsfQz7zEQL1EuSx5tyNLNS": {"label": "Bitfinex Cold", "category": "exchange", "balance_btc": 18500, "balance_usd": 1628000000, "tx_count": 2100, "funded_count": 1200, "spent_count": 900, "last_outgoing_ts": 1708000000, "days_dormant": 25},
    "bc1qazcm763858nkj2dz7g3vafgyvxragcyrtcxy5a": {"label": "Kraken Hot", "category": "exchange", "balance_btc": 12800, "balance_usd": 1126400000, "tx_count": 8500, "funded_count": 4500, "spent_count": 4000, "last_outgoing_ts": 1710800000, "days_dormant": 1},
    "bc1qhxnxfcaq2cx5g9aa5q9gry6yxrjqnx7s64faxv": {"label": "OKX Cold", "category": "exchange", "balance_btc": 9800, "balance_usd": 862400000, "tx_count": 4300, "funded_count": 2400, "spent_count": 1900, "last_outgoing_ts": 1709500000, "days_dormant": 8},
    "bc1qcv8h9hp5clags3wf394kp0qzfnez93sxlj564z": {"label": "BlackRock iShares (IBIT)", "category": "etf", "balance_btc": 285000, "balance_usd": 25080000000, "tx_count": 890, "funded_count": 520, "spent_count": 370, "last_outgoing_ts": 1710200000, "days_dormant": 5},
    "3LtzGMiaKpuLFnyhS7wjyLmJEbzanHCBfR": {"label": "Fidelity FBTC", "category": "etf", "balance_btc": 198000, "balance_usd": 17424000000, "tx_count": 650, "funded_count": 380, "spent_count": 270, "last_outgoing_ts": 1710100000, "days_dormant": 6},
    "bc1qcdqj2smprre85c78d942wx5tauw5n7uw92r7wr": {"label": "Grayscale GBTC", "category": "etf", "balance_btc": 210000, "balance_usd": 18480000000, "tx_count": 1200, "funded_count": 700, "spent_count": 500, "last_outgoing_ts": 1709800000, "days_dormant": 9},
    "3Cbq7aT1tY8kMxWLbitaG7yT6bPbKChq64": {"label": "MicroStrategy", "category": "institution", "balance_btc": 174000, "balance_usd": 15312000000, "tx_count": 420, "funded_count": 280, "spent_count": 140, "last_outgoing_ts": 1705000000, "days_dormant": 62},
    "37XuVSEpWW4trkfmvWzegTHQt7BdktSKUs": {"label": "Tether Treasury", "category": "institution", "balance_btc": 8200, "balance_usd": 721600000, "tx_count": 350, "funded_count": 200, "spent_count": 150, "last_outgoing_ts": 1708500000, "days_dormant": 18},
    "1LQoWist8KkaUXSPKZHNvEyfrEkPHzSsCd": {"label": "Unknown Whale #1", "category": "unknown", "balance_btc": 15200, "balance_usd": 1337600000, "tx_count": 12, "funded_count": 8, "spent_count": 4, "last_outgoing_ts": 1640000000, "days_dormant": 820},
    "1LruNZjwamWJXThX2Y8C2d47QfhANiHLrR": {"label": "Unknown Whale #2", "category": "unknown", "balance_btc": 12500, "balance_usd": 1100000000, "tx_count": 5, "funded_count": 5, "spent_count": 0, "last_outgoing_ts": None, "days_dormant": None},
    "385cR5DM96n1HvBDMzLHPYcw89fZAXULJP": {"label": "Unknown Whale #7", "category": "unknown", "balance_btc": 11800, "balance_usd": 1038400000, "tx_count": 18, "funded_count": 12, "spent_count": 6, "last_outgoing_ts": 1580000000, "days_dormant": 1515},
    "1BvNwfxEQwZNRmYQ3eno6e976XyxhCsRXj": {"label": "Unknown Whale #12", "category": "unknown", "balance_btc": 4881, "balance_usd": 429528000, "tx_count": 38, "funded_count": 38, "spent_count": 0, "last_outgoing_ts": None, "days_dormant": None},
    "1Btud1pqADgGzgBCZzxzc2b1o1ytk1HYWC": {"label": "Unknown Whale #10", "category": "unknown", "balance_btc": 4900, "balance_usd": 431200000, "tx_count": 32, "funded_count": 32, "spent_count": 0, "last_outgoing_ts": None, "days_dormant": None},
    "1Miy5sJZSamDZN6xcJJidp9zYxhSrpDeJm": {"label": "Unknown Whale #13", "category": "unknown", "balance_btc": 4792, "balance_usd": 421696000, "tx_count": 38, "funded_count": 38, "spent_count": 0, "last_outgoing_ts": None, "days_dormant": None},
    "1Kq6hXXiSpdp9bg9hDDyqm8ZfvgZmzchjn": {"label": "Unknown Whale #14", "category": "unknown", "balance_btc": 4699, "balance_usd": 413512000, "tx_count": 29, "funded_count": 29, "spent_count": 0, "last_outgoing_ts": None, "days_dormant": None},
    "3JX2dHyVstG2xbSsmu7wjepY6BCGcFKkU9": {"label": "Unknown Whale #8", "category": "unknown", "balance_btc": 4999, "balance_usd": 439912000, "tx_count": 5, "funded_count": 5, "spent_count": 0, "last_outgoing_ts": None, "days_dormant": None},
    "bc1q0lfp0nn9z9r370rhmp27xsmf3khwtranuegp9k": {"label": "Unknown Whale #9", "category": "unknown", "balance_btc": 4999, "balance_usd": 439912000, "tx_count": 154, "funded_count": 154, "spent_count": 145, "last_outgoing_ts": 1706000000, "days_dormant": 50},
}

latest_date = history[-1]
cat_totals = {"exchange": 0, "etf": 0, "institution": 0, "unknown": 0}
for info in addresses.values():
    cat_totals[info["category"]] += info["balance_btc"]

total_tracked = sum(cat_totals.values())
supply = 19850000

balances_sorted = sorted([v["balance_btc"] for v in addresses.values()], reverse=True)

latest = {
    "date": latest_date["date"],
    "timestamp": f"{latest_date['date']}T01:00:00Z",
    "btc_price": latest_date["btc_price"],
    "total_tracked_btc": round(total_tracked, 2),
    "total_tracked_pct": round(total_tracked / supply * 100, 4),
    "concentration": {
        "top10_btc": round(sum(balances_sorted[:10]), 2),
        "top10_pct": round(sum(balances_sorted[:10]) / supply * 100, 4),
        "top20_btc": round(sum(balances_sorted[:min(20, len(balances_sorted))]), 2),
        "top20_pct": round(sum(balances_sorted[:min(20, len(balances_sorted))]) / supply * 100, 4),
        "top50_btc": round(total_tracked, 2),
        "top50_pct": round(total_tracked / supply * 100, 4),
    },
    "by_category": {
        cat: {"btc": round(v, 2), "pct": round(v / supply * 100, 4)}
        for cat, v in cat_totals.items()
    },
    "addresses": addresses,
    "dormant_alerts": [
        {
            "address": "385cR5DM96n1HvBDMzLHPYcw89fZAXULJP",
            "label": "Unknown Whale #7",
            "category": "unknown",
            "balance_btc": 11800,
            "balance_usd": 1038400000,
            "days_dormant": 1515,
            "last_outgoing_ts": 1580000000,
            "detected_date": "2026-03-15",
        },
        {
            "address": "1LQoWist8KkaUXSPKZHNvEyfrEkPHzSsCd",
            "label": "Unknown Whale #1",
            "category": "unknown",
            "balance_btc": 15200,
            "balance_usd": 1337600000,
            "days_dormant": 820,
            "last_outgoing_ts": 1640000000,
            "detected_date": "2026-03-10",
        },
    ]
}

with open(DATA_DIR / "latest.json", "w") as f:
    json.dump(latest, f, indent=2)

with open(DATA_DIR / "dormant_alerts.json", "w") as f:
    json.dump(latest["dormant_alerts"], f, indent=2)

print("✅ Sample data generated!")
print(f"   History: {len(history)} days")
print(f"   Addresses: {len(addresses)}")
print(f"   Dormant alerts: {len(latest['dormant_alerts'])}")
