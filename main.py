import requests
import time
import json

# ==========================================
# CONFIGURATION
# ==========================================
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1560338637206323361/Oow9JBBzc4GyUKEnKBCANpTWEofxp3D4LY9RAZ0_G474bISWsA_pSgHOkLBHydHcuh1I"
ZIP_CODE = "92253" # Replace with your target ZIP code
CHECK_INTERVAL_SECONDS = 300 # Checks every 5 minutes (300 seconds)

# List of items to monitor across all 5 major retailers
ITEMS_TO_MONITOR = [
    {"store": "Target", "id": "89102345", "name": "Pokemon Elite Trainer Box"},
    {"store": "BestBuy", "id": "6543210", "name": "Pokemon Booster Bundle"},
    {"store": "Walmart", "id": "12345678", "name": "Pokemon Tin Bundle"},
    {"store": "SamsClub", "url": "https://www.samsclub.com/p/pokemon-item-example/prod2600000", "name": "Pokemon Trading Card Box"},
    {"store": "Costco", "url": "https://www.costco.com/pokemon-item-example.html", "name": "Pokemon Card Multi-Pack"}
]

def send_alert(message):
    """Sends an instant push notification to your Discord Webhook."""
    payload = {"content": f"🚨 **POKEMON RESTOCK ALERT** 🚨\n{message}"}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except Exception as e:
        print(f"Failed to send alert: {e}")

def check_target_stock(tcin, zip_code):
    """Checks localized Target inventory status via RedSky API."""
    url = f"https://redsky.target.com/v3/pdp/tcin/{tcin}?key=eb250ba6ea4f27303e2c694a159f81a711677c72&nearby={zip_code}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        res = requests.get(url, headers=headers, timeout=10).json()
        fulfillment = res.get("product", {}).get("fulfillment", {})
        store_options = fulfillment.get("store_options", [])
        for store in store_options:
            status = store.get("location_available_to_promise_quantity", 0)
            order_pickup = store.get("order_pickup", {}).get("availability_status")
            if status > 0 or order_pickup == "IN_STOCK":
                return True, f"In Stock at Target store #{store.get('location_id')}!"
        return False, "Out of Stock"
    except Exception:
        return False, "Error checking Target API"

def check_bestbuy_stock(sku, zip_code):
    """Checks Best Buy local store availability."""
    url = f"https://www.bestbuy.com/site/async/swu/byLocation?skuId={sku}&postalCode={zip_code}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200 and ("pickup" in res.text.lower() or "available" in res.text.lower()):
            return True, "Available for local pickup at Best Buy!"
        return False, "Out of Stock"
    except Exception:
        return False, "Error checking Best Buy API"

def check_walmart_stock(item_id, zip_code):
    """Checks Walmart online/local stock indicators."""
    url = f"https://www.walmart.com/ip/{item_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            if "add to cart" in res.text.lower() and "out of stock" not in res.text.lower():
                return True, "Add to Cart active on Walmart!"
        return False, "Out of Stock"
    except Exception:
        return False, "Error checking Walmart"

def check_generic_web_stock(store_name, url):
    """Checks Costco or Sam's Club product pages for active order buttons."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            text = res.text.lower()
            if "out of stock" not in text and ("add to cart" in text or "add to order" in text or "delivery" in text):
                return True, f"Stock available online at {store_name}!"
        return False, "Out of Stock"
    except Exception:
        return False, f"Error checking {store_name}"

def monitor():
    print(f"Starting Multi-Store Stock Monitor for ZIP {ZIP_CODE}...")
    while True:
        for item in ITEMS_TO_MONITOR:
            store = item["store"]
            name = item["name"]
            in_stock = False
            msg = ""
            
            if store == "Target":
                in_stock, msg = check_target_stock(item["id"], ZIP_CODE)
            elif store == "BestBuy":
                in_stock, msg = check_bestbuy_stock(item["id"], ZIP_CODE)
            elif store == "Walmart":
                in_stock, msg = check_walmart_stock(item["id"], ZIP_CODE)
            elif store in ["SamsClub", "Costco"]:
                in_stock, msg = check_generic_web_stock(store, item["url"])
                
            if in_stock:
                send_alert(f"**{name}** ({store}): {msg}")
                print(f"[ALERT SENT] {name} found at {store}!")
            else:
                print(f"[{time.strftime('%H:%M:%S' )}] {name} ({store}): {msg}")
                
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    monitor()
