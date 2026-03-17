#!/usr/bin/env python3
"""
BTC Whale Tracker - Daily Data Collection
Uses mempool.space API (free, no key required)
Fallback: blockchain.info API

Outputs:
  - data/whale_snapshot_{date}.json  (daily snapshot)
  - data/whale_history.json          (accumulated time series)
  - data/dormant_alerts.json         (dormant whale awakening alerts)
  - data/latest.json                 (latest snapshot for dashboard)
"""

import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
BTC_TOTAL_SUPPLY = 19_850_000  # approximate circulating supply as of 2026
DATA_DIR = Path(__file__).parent.parent / "data"
DORMANT_THRESHOLD_DAYS = 365  # consider "dormant" if no outgoing tx for 1 year
REQUEST_DELAY = 0.35  # seconds between API calls (respect rate limits)
MAX_RETRIES = 2

# ── Whale Address Registry ──────────────────────────────────────────────────
# Format: { "address": { "label": str, "category": "exchange"|"etf"|"unknown"|"institution" } }
WHALE_ADDRESSES = {
    # ─── Exchanges ───
    "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo": {"label": "Binance Cold Wallet", "category": "exchange"},
    "bc1qm34lsc65zpw79lxes69zkqmk6ee3ewf0j77s3h": {"label": "Binance Cold 2", "category": "exchange"},
    "3M219KR5vEneNb47ewrPfWyb5jQ2DjxRP6": {"label": "Binance Cold 3", "category": "exchange"},
    "1NDyJtNTjmwk5xPNhjgAMu4HDHigtobu1s": {"label": "Binance Hot", "category": "exchange"},
    "bc1qx9t2l3pyny2spqpqlye8svce70nppwtaxwdrp4": {"label": "Binance Treasury", "category": "exchange"},
    "39884E3j6KZj82FK4vcCrkUvWYL5MQaS3v": {"label": "Coinbase Cold", "category": "exchange"},
    "bc1qjasf9z3h7w3jspkhtgatgpyvvzgpa2wwd2lr0eh5tx44reyn2k7sflc28r": {"label": "Coinbase Prime", "category": "exchange"},
    "bc1qa5wkgaew2dkv56kc6hp23g564k9vm3e3362amu": {"label": "Coinbase Cold 2", "category": "exchange"},
    "bc1qx2x5cqhymfcnjtg902ky8m5kzr5lyghslvftcl": {"label": "Coinbase Cold 3", "category": "exchange"},
    "3Kzh9qAqVWQhEsfQz7zEQL1EuSx5tyNLNS": {"label": "Bitfinex Cold", "category": "exchange"},
    "bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrpmv24sq90ecnvqqjwvw97": {"label": "Bitfinex Cold 2", "category": "exchange"},
    "1Kr6QSydW9bFQG1mXiPNNu6WpJGmUa9i1g": {"label": "Bitfinex Cold 3", "category": "exchange"},
    "3FHNBLobJnbCTFTVakh5TXmEneyf5PT61B": {"label": "Bitstamp Cold", "category": "exchange"},
    "3D2oetdNuZUqQHPJmcMDDHYoqkyNVsFk9r": {"label": "Bitstamp Cold 2", "category": "exchange"},
    "bc1qazcm763858nkj2dz7g3vafgyvxragcyrtcxy5a": {"label": "Kraken Hot", "category": "exchange"},
    "bc1qr4dl5wa7kl8yu792dceg9z5knl2gkn220lk7a9": {"label": "Kraken Cold", "category": "exchange"},
    "3AfP3p2kePiSrrmPHN1vni7b4ZWVKpYjUE": {"label": "Kraken Cold 2", "category": "exchange"},
    "bc1qhxnxfcaq2cx5g9aa5q9gry6yxrjqnx7s64faxv": {"label": "OKX Cold", "category": "exchange"},
    "1Ay8vMC7R1UbyCCZRVULMV7iQpHSAbguJP": {"label": "OKX Cold 2", "category": "exchange"},
    "3LQUu4v9z6KNch71j7kbj8GPeAGUo1FW6a": {"label": "Bybit Cold", "category": "exchange"},
    "1LdRcdxfbSnmCYYNdeYRV97vMosVR8dPak": {"label": "Bybit Cold 2", "category": "exchange"},
    "18rnfoQgGo1HqvVQaAN4QnxjYE7Sez9o4a": {"label": "Huobi Cold", "category": "exchange"},
    "1HckjUpRGcrrRAtFaaCAUaGjsPx9oYmLaZ": {"label": "Huobi Cold 2", "category": "exchange"},
    "1PJiGp2yDLvUgqeBsuZVCBADArNsk6XEiN": {"label": "Gemini Cold", "category": "exchange"},

    # ─── ETFs / Institutions ───
    "bc1qcv8h9hp5clags3wf394kp0qzfnez93sxlj564z": {"label": "BlackRock iShares (IBIT)", "category": "etf"},
    "bc1qlz2h9scmmn7cphsnw4k5gv7wgklegf5ttu7qd4": {"label": "BlackRock IBIT 2", "category": "etf"},
    "3LtzGMiaKpuLFnyhS7wjyLmJEbzanHCBfR": {"label": "Fidelity FBTC", "category": "etf"},
    "bc1qcdqj2smprre85c78d942wx5tauw5n7uw92r7wr": {"label": "Grayscale GBTC", "category": "etf"},
    "bc1q4c8n5t00jmj8temxdgcc3t32nkg2wjwz24lywv": {"label": "Grayscale Mini BTC", "category": "etf"},
    "3Cbq7aT1tY8kMxWLbitaG7yT6bPbKChq64": {"label": "MicroStrategy", "category": "institution"},
    "bc1qazcm763858nkj2dz7g3vafgyvxragcyrtcxy5a": {"label": "MicroStrategy 2", "category": "institution"},
    "bc1q7e6qu5smalrpgqrx9k2gnf0hgjyref5p36ru2m": {"label": "Block.one", "category": "institution"},
    "37XuVSEpWW4trkfmvWzegTHQt7BdktSKUs": {"label": "Tether Treasury", "category": "institution"},

    # ─── Unknown Whales (from bitinfocharts top list) ───
    "1LQoWist8KkaUXSPKZHNvEyfrEkPHzSsCd": {"label": "Unknown Whale #1", "category": "unknown"},
    "1LruNZjwamWJXThX2Y8C2d47QfhANiHLrR": {"label": "Unknown Whale #2", "category": "unknown"},
    "bc1qjysjfd9t9aspttpjqzv68k0ydpe7pvyd5v0z3p": {"label": "Unknown Whale #3", "category": "unknown"},
    "bc1qd4ysezhmypwty5dnw7c8nqy5h5nxg0xqsvaefd0qn5kq32vwnwqqgv4rzr": {"label": "Unknown Whale #4", "category": "unknown"},
    "1PeizMg76Cf96nUQrYg8xuoZWLQozU5zGW": {"label": "Unknown Whale #5", "category": "unknown"},
    "bc1qa5wkgaew2dkv56kc6hp23g564k9vm3e3362amu": {"label": "Unknown Whale #6", "category": "unknown"},
    "385cR5DM96n1HvBDMzLHPYcw89fZAXULJP": {"label": "Unknown Whale #7", "category": "unknown"},
    "3JX2dHyVstG2xbSsmu7wjepY6BCGcFKkU9": {"label": "Unknown Whale #8", "category": "unknown"},
    "bc1q0lfp0nn9z9r370rhmp27xsmf3khwtranuegp9k": {"label": "Unknown Whale #9", "category": "unknown"},
    "1Btud1pqADgGzgBCZzxzc2b1o1ytk1HYWC": {"label": "Unknown Whale #10", "category": "unknown"},
    "1BXZng4dcXDnYNRXRgHqWjzT5RwxHHBSHo": {"label": "Unknown Whale #11", "category": "unknown"},
    "1BvNwfxEQwZNRmYQ3eno6e976XyxhCsRXj": {"label": "Unknown Whale #12", "category": "unknown"},
    "1Miy5sJZSamDZN6xcJJidp9zYxhSrpDeJm": {"label": "Unknown Whale #13", "category": "unknown"},
    "1Kq6hXXiSpdp9bg9hDDyqm8ZfvgZmzchjn": {"label": "Unknown Whale #14", "category": "unknown"},
    "14f3x5v48f7b7QN6Lqt56Fg8jBQ7nVn26N": {"label": "Unknown Whale #15", "category": "unknown"},
    "bc1qhevexnspmmx69gna47dfs09vr9wd9x27qzlzq5": {"label": "Unknown Whale #16", "category": "unknown"},
    "bc1qfnyjgneu98mfxhr4yz7vgvpkqrnsfcje08uy9j": {"label": "Unknown Whale #17", "category": "unknown"},
    "bc1qaehnshqyej90d59928qjcwz2x7mr9ml3uxtmzx": {"label": "Unknown Whale #18", "category": "unknown"},
    "bc1qe2kzhqnctjvungel58vtcgykdmdwrw57d20e69": {"label": "Unknown Whale #19", "category": "unknown"},
    "bc1q904x3fw23mwxvmpnpm0w468y2k2egzx56cq44n": {"label": "Unknown Whale #20", "category": "unknown"},
    "bc1q9n8enkshdgez0eay34kwj33r5eh68uczwr4yz6": {"label": "Unknown Whale #21", "category": "unknown"},
    "bc1qz2ccfezdgjcv6eznldw4r36zkvxhdceslj7l7z": {"label": "Unknown Whale #22", "category": "unknown"},
    "bc1ql70e2mw70ax52j847gg3yxvygcnsde3vx4t8hk": {"label": "Unknown Whale #23", "category": "unknown"},
    "bc1q3zqs5efuvt8dvzk3juza898ch9ke9fdafxr9n9": {"label": "Unknown Whale #24", "category": "unknown"},
    "3N4M72xVMeuTSrsamQHTBHwhF4NQAJPWXp": {"label": "Unknown Whale #25", "category": "unknown"},
    "3BHXygmhNMaCcNn76S8DLdnZ5ucPtNtWGb": {"label": "Unknown Whale #26", "category": "unknown"},
    "bc1qncsa0qdrgsr58303gsnuwhd5vrm7hlkpd6klmf": {"label": "Unknown Whale #27", "category": "unknown"},
    "bc1qtf50my2qjmpcrxd6lj8gmx35eeevu4mfrjzmeh": {"label": "Unknown Whale #28", "category": "unknown"},
    "bc1qxef8ncsv6ghy8x6ermse47h7hksl0p0fmggx6z": {"label": "Unknown Whale #29", "category": "unknown"},
}

# ── API Helpers ─────────────────────────────────────────────────────────────

def fetch_json(url, retries=MAX_RETRIES):
    """Fetch JSON from URL with retries."""
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HerdVibe-WhaleTracker/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            if attempt < retries:
                time.sleep(2 ** attempt)
            else:
                print(f"  ✗ Failed: {url} → {e}")
                return None


def get_address_data_mempool(address):
    """Fetch address data from mempool.space API."""
    data = fetch_json(f"https://mempool.space/api/address/{address}")
    if not data:
        return None

    chain = data.get("chain_stats", {})
    mempool = data.get("mempool_stats", {})

    funded = chain.get("funded_txo_sum", 0)
    spent = chain.get("spent_txo_sum", 0)
    balance_sat = funded - spent
    balance_btc = balance_sat / 1e8

    return {
        "balance_btc": round(balance_btc, 8),
        "tx_count": chain.get("tx_count", 0),
        "funded_txo_count": chain.get("funded_txo_count", 0),
        "spent_txo_count": chain.get("spent_txo_count", 0),
    }


def get_address_data_blockchain(address):
    """Fallback: blockchain.info API."""
    data = fetch_json(f"https://blockchain.info/rawaddr/{address}?limit=1")
    if not data:
        return None

    balance_btc = data.get("final_balance", 0) / 1e8
    txs = data.get("txs", [])
    last_tx_time = txs[0]["time"] if txs else None

    return {
        "balance_btc": round(balance_btc, 8),
        "tx_count": data.get("n_tx", 0),
        "funded_txo_count": data.get("n_tx", 0),  # approximate
        "spent_txo_count": 0,
        "last_tx_time": last_tx_time,
    }


def get_btc_price():
    """Get current BTC price from CoinGecko (free, no key)."""
    data = fetch_json("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
    if data and "bitcoin" in data:
        return data["bitcoin"]["usd"]
    # Fallback: mempool.space
    data = fetch_json("https://mempool.space/api/v1/prices")
    if data:
        return data.get("USD", 0)
    return 0


def get_last_tx_info(address):
    """Get recent transactions for dormancy detection."""
    data = fetch_json(f"https://mempool.space/api/address/{address}/txs")
    if not data or not isinstance(data, list):
        return None

    # Find last outgoing tx (where this address is in inputs)
    last_outgoing = None
    last_any = None
    for tx in data[:10]:  # check last 10 txs
        tx_time = tx.get("status", {}).get("block_time")
        if tx_time and (not last_any or tx_time > last_any):
            last_any = tx_time

        # Check if address appears in inputs (outgoing)
        for vin in tx.get("vin", []):
            prevout = vin.get("prevout", {})
            if prevout.get("scriptpubkey_address") == address:
                if tx_time and (not last_outgoing or tx_time > last_outgoing):
                    last_outgoing = tx_time

    return {
        "last_any_tx": last_any,
        "last_outgoing_tx": last_outgoing,
    }


# ── Main Collection ─────────────────────────────────────────────────────────

def collect_all():
    """Main collection routine."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    print(f"🐋 BTC Whale Tracker — Collecting data for {date_str}")

    # Get BTC price
    btc_price = get_btc_price()
    print(f"💰 BTC Price: ${btc_price:,.0f}")

    # Collect address data
    results = {}
    dormant_alerts = []
    total = len(WHALE_ADDRESSES)

    for i, (addr, meta) in enumerate(WHALE_ADDRESSES.items()):
        print(f"  [{i+1}/{total}] {meta['label']}...", end=" ")

        # Get balance
        data = get_address_data_mempool(addr)
        if not data:
            data = get_address_data_blockchain(addr)
        if not data:
            print("SKIP")
            continue

        balance = data["balance_btc"]
        print(f"{balance:,.2f} BTC")

        # Get tx info for dormancy check
        tx_info = get_last_tx_info(addr)
        time.sleep(REQUEST_DELAY)

        last_outgoing = None
        days_dormant = None
        if tx_info and tx_info["last_outgoing_tx"]:
            last_outgoing = tx_info["last_outgoing_tx"]
            days_dormant = (now.timestamp() - last_outgoing) / 86400

        # Check for dormant whale awakening
        was_dormant = False
        if tx_info and tx_info["last_any_tx"]:
            last_any = tx_info["last_any_tx"]
            # If had recent activity (last 7 days) but was dormant before
            recent_activity = (now.timestamp() - last_any) < 7 * 86400
            if recent_activity and days_dormant and days_dormant > DORMANT_THRESHOLD_DAYS:
                was_dormant = True
                dormant_alerts.append({
                    "address": addr,
                    "label": meta["label"],
                    "category": meta["category"],
                    "balance_btc": balance,
                    "balance_usd": round(balance * btc_price, 2),
                    "days_dormant": round(days_dormant, 1),
                    "last_outgoing_ts": last_outgoing,
                    "detected_date": date_str,
                })

        results[addr] = {
            "label": meta["label"],
            "category": meta["category"],
            "balance_btc": balance,
            "balance_usd": round(balance * btc_price, 2),
            "tx_count": data.get("tx_count", 0),
            "funded_count": data.get("funded_txo_count", 0),
            "spent_count": data.get("spent_txo_count", 0),
            "last_outgoing_ts": last_outgoing,
            "days_dormant": round(days_dormant, 1) if days_dormant else None,
        }

        time.sleep(REQUEST_DELAY)

    # ── Compute aggregates ──────────────────────────────────────────────
    exchange_btc = sum(v["balance_btc"] for v in results.values() if v["category"] == "exchange")
    etf_btc = sum(v["balance_btc"] for v in results.values() if v["category"] == "etf")
    institution_btc = sum(v["balance_btc"] for v in results.values() if v["category"] == "institution")
    unknown_btc = sum(v["balance_btc"] for v in results.values() if v["category"] == "unknown")
    total_tracked = sum(v["balance_btc"] for v in results.values())

    # Top N concentration
    balances_sorted = sorted([v["balance_btc"] for v in results.values()], reverse=True)
    top10_btc = sum(balances_sorted[:10])
    top20_btc = sum(balances_sorted[:20])
    top50_btc = sum(balances_sorted[:50])

    snapshot = {
        "date": date_str,
        "timestamp": now.isoformat(),
        "btc_price": btc_price,
        "total_tracked_btc": round(total_tracked, 2),
        "total_tracked_pct": round(total_tracked / BTC_TOTAL_SUPPLY * 100, 4),
        "concentration": {
            "top10_btc": round(top10_btc, 2),
            "top10_pct": round(top10_btc / BTC_TOTAL_SUPPLY * 100, 4),
            "top20_btc": round(top20_btc, 2),
            "top20_pct": round(top20_btc / BTC_TOTAL_SUPPLY * 100, 4),
            "top50_btc": round(top50_btc, 2),
            "top50_pct": round(top50_btc / BTC_TOTAL_SUPPLY * 100, 4),
        },
        "by_category": {
            "exchange": {"btc": round(exchange_btc, 2), "pct": round(exchange_btc / BTC_TOTAL_SUPPLY * 100, 4)},
            "etf": {"btc": round(etf_btc, 2), "pct": round(etf_btc / BTC_TOTAL_SUPPLY * 100, 4)},
            "institution": {"btc": round(institution_btc, 2), "pct": round(institution_btc / BTC_TOTAL_SUPPLY * 100, 4)},
            "unknown": {"btc": round(unknown_btc, 2), "pct": round(unknown_btc / BTC_TOTAL_SUPPLY * 100, 4)},
        },
        "addresses": results,
        "dormant_alerts": dormant_alerts,
    }

    # ── Save daily snapshot ─────────────────────────────────────────────
    snapshot_file = DATA_DIR / f"whale_snapshot_{date_str}.json"
    with open(snapshot_file, "w") as f:
        json.dump(snapshot, f, indent=2)
    print(f"\n📁 Snapshot saved: {snapshot_file}")

    # ── Save latest.json ────────────────────────────────────────────────
    latest_file = DATA_DIR / "latest.json"
    with open(latest_file, "w") as f:
        json.dump(snapshot, f, indent=2)
    print(f"📁 Latest saved: {latest_file}")

    # ── Update history.json (time series) ───────────────────────────────
    history_file = DATA_DIR / "whale_history.json"
    history = []
    if history_file.exists():
        with open(history_file) as f:
            history = json.load(f)

    # Remove duplicate date entry if re-running
    history = [h for h in history if h["date"] != date_str]

    history.append({
        "date": date_str,
        "btc_price": btc_price,
        "total_tracked_btc": snapshot["total_tracked_btc"],
        "total_tracked_pct": snapshot["total_tracked_pct"],
        "top10_pct": snapshot["concentration"]["top10_pct"],
        "top20_pct": snapshot["concentration"]["top20_pct"],
        "top50_pct": snapshot["concentration"]["top50_pct"],
        "exchange_btc": snapshot["by_category"]["exchange"]["btc"],
        "etf_btc": snapshot["by_category"]["etf"]["btc"],
        "institution_btc": snapshot["by_category"]["institution"]["btc"],
        "unknown_btc": snapshot["by_category"]["unknown"]["btc"],
        "exchange_pct": snapshot["by_category"]["exchange"]["pct"],
        "etf_pct": snapshot["by_category"]["etf"]["pct"],
        "institution_pct": snapshot["by_category"]["institution"]["pct"],
        "unknown_pct": snapshot["by_category"]["unknown"]["pct"],
    })

    # Keep max 365 days
    history = history[-365:]
    history.sort(key=lambda x: x["date"])

    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)
    print(f"📁 History updated: {len(history)} days")

    # ── Update dormant_alerts.json (accumulated) ────────────────────────
    alerts_file = DATA_DIR / "dormant_alerts.json"
    all_alerts = []
    if alerts_file.exists():
        with open(alerts_file) as f:
            all_alerts = json.load(f)

    all_alerts.extend(dormant_alerts)
    # Keep last 100 alerts
    all_alerts = all_alerts[-100:]

    with open(alerts_file, "w") as f:
        json.dump(all_alerts, f, indent=2)
    print(f"🚨 Dormant alerts: {len(dormant_alerts)} new, {len(all_alerts)} total")

    print(f"\n✅ Collection complete!")
    print(f"   Tracked: {len(results)} addresses / {total_tracked:,.0f} BTC")
    print(f"   Exchange: {exchange_btc:,.0f} | ETF: {etf_btc:,.0f} | Institution: {institution_btc:,.0f} | Unknown: {unknown_btc:,.0f}")


if __name__ == "__main__":
    collect_all()
