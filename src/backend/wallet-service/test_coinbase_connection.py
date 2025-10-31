import os
import asyncio
import ccxt.async_support as ccxt
from ccxt.base.errors import AuthenticationError, NetworkError

# Optional: toggle verbose HTTP logs by setting VERBOSE=1 in your env
VERBOSE = os.getenv("VERBOSE", "0") == "1"

async def test_coinbase_connectivity():
    """
    A standalone script to test Coinbase Advanced Trade API connectivity using CCXT.
    Uses CCXT's unified balance format, with a safe fallback for raw payloads.
    """

    print("🚀 Starting Coinbase connection test...")

    # --- Credentials ---
    # Prefer env vars in real use; keep your local hardcoded values if needed.
    # API Key 'name' (CDP format: organizations/.../apiKeys/...)
    api_key_name = os.getenv(
        "COINBASE_API_KEY_NAME",
        "organizations/0500b409-d385-4dad-a6a7-0e1ea9315b33/apiKeys/9e354295-d0c5-41ba-b971-0a82bdce01bb",  # <-- replace if not using env
    )

    # PEM private key (full PEM, including BEGIN/END lines)
    private_key = os.getenv(
        "COINBASE_API_PRIVATE_KEY",
        """-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIIfiOhzP6wwdlLZq0j/NlbotaYs0abdwbo2wDD4eKO6YoAoGCCqGSM49\nAwEHoUQDQgAEP/1dEO9dGVSjzx+6hdo8Nyc+mmsbXbYCtZU3W6abgVtDE6ZNGVCI\ncaBjPPQQMQDqnBJTbVLAFblOB/ga+oV7kA==\n-----END EC PRIVATE KEY-----\n""",  # <-- replace if not using env
    )

    # --- Exchange init ---
    exchange_config = {
        "apiKey": api_key_name,
        "secret": private_key,
        "enableRateLimit": True,
        "timeout": 60000,
        # Synchronize local clock with server to avoid timestamp skews
        "options": {"fetchTime": True},
    }

    exchange = ccxt.coinbase(exchange_config)
    exchange.verbose = VERBOSE

    try:
        print("📡 Attempting to fetch balances from Coinbase...")

        # NOTE: Many CCXT methods call load_markets() internally; that's fine.
        # If your key lacks product-read perms, you'll see a 401 earlier.
        balance_data = await exchange.fetch_balance()

        print("\n✅ SUCCESS: Connection and authentication successful!")

        # ---------- Print balances (safe + robust) ----------
        print("\n--- Sample Balances ---")

        # Prefer CCXT's unified "total" balances
        totals = (balance_data or {}).get("total", {}) or {}
        nonzero = [(c, v) for c, v in totals.items() if (v or 0) > 0]

        printed = 0
        if nonzero:
            for c, v in nonzero[:5]:
                print(f"  - {c}: {v}")
                printed += 1

        # Fallback to raw payload if unified is empty
        if printed == 0:
            info = (balance_data or {}).get("info", {}) or {}

            # Common raw layouts seen in Coinbase Advanced responses
            # Sometimes "accounts", sometimes "data"
            accounts = info.get("accounts") or info.get("data") or []

            for acc in accounts:
                if not isinstance(acc, dict):
                    continue

                cur = acc.get("currency") or acc.get("currency_code")

                # Try several common places Coinbase puts values
                val = (
                    # { "available_balance": { "value": "..." } }
                    (acc.get("available_balance") or {}).get("value")
                    # { "balance": { "value": "..." } }
                    or (acc.get("balance") or {}).get("value")
                    # sometimes plain "value"
                    or acc.get("value")
                )

                try:
                    if cur and val is not None and float(val) > 0:
                        print(f"  - {cur}: {val}")
                        printed += 1
                        if printed >= 5:
                            break
                except Exception:
                    # Ignore cast issues quietly
                    continue

            if printed == 0:
                print("  No assets with a balance greater than 0 found.")

    except AuthenticationError as e:
        print(f"\n❌ FAILURE: Authentication Failed. This is a '401 Unauthorized' error.")
        print("   Common Causes:")
        print("     1. The API Key 'name' or Private Key is incorrect (check for whitespace).")
        print("     2. The key lacks required read permissions for the target portfolio.")
        print("     3. IP allowlist mismatch (if enabled).")
        print(f"   Error: {e}")
    except NetworkError as e:
        print(f"\n❌ FAILURE: Network Error. Could not reach Coinbase.")
        print(f"   Error: {e}")
    except Exception as e:
        print(f"\n❌ FAILURE: An unexpected error occurred.")
        print(f"   Type: {type(e).__name__}")
        print(f"   Error: {e}")
        # Optional: show shape to help debug unexpected schemas
        # import json; print(json.dumps(balance_data, indent=2, default=str))
    finally:
        # Always close the connection
        await exchange.close()
        print("\n🔌 Connection closed.")

if __name__ == "__main__":
    # Ensure you have a recent CCXT: pip install -U "ccxt>=4.4.60"
    asyncio.run(test_coinbase_connectivity())
