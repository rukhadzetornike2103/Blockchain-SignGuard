# Recent Changes & Release Notes

## Bug Fixes

### `benchmark.py`
* **`benchmark_test()`:** Added input validation guards at the top for `token_price_usd <= 0`, `token_real_supply <= 0`, `user_target_price <= 0`, and `user_invest_amount < 0`. Prints a red error and returns `None` instead of crashing with a `ZeroDivisionError`.
* **`determine_cap()`:** Fixed a boundary bug where an exact $1B market cap fell into the wrong range (`1000000000.00 < marketcap` updated to `1000000000.00 <= marketcap`).
* **`get_dex_token_data()`:** Added `wstETH` to the canonical blue-chip dictionary, added an empty query check returning `(None, None, 0)` before hitting external APIs, and added hex character validation before the mock pool fallback to reject invalid addresses (e.g., `0xGGGG...`).

### `aave_sim.py`
* **`get_live_aave_params()`:** Added strict address validation (`isinstance(str)`, `0x` prefix, 42-character length, valid hex characters). All error paths now consistently return `(75.0, 80.0, 5.0, False)` instead of strings or `None`.
* **`liquidation_simulator()`:** Removed duplicate `loanGranting = True` dead code, wrapped all `float(input())` calls in `while True` / `try-except ValueError` validation loops rejecting zero, negative, and infinite values, and added division-by-zero guards prior to liquidation math calculations.

### `main.py`
* Wrapped menu selection, holders count (`1 <= n <= 100`), target price, and investment amount inputs in `while True` validation loops.
* Added safety checks for Ethplorer JSON parsing (`status_code == 200`, `"error" not in data`, `"totalSupply" in data`, `"decimals" in data`, and `isinstance(data.get("price"), dict)`).
* Wrapped whale data JSON parsing in `try/except`, verified `"holders"` presence and non-empty `holders_list`, and defaulted `whale_balance = 0` when empty to prevent `IndexError` on `holders_list[0]`.
* Fixed burn address output to display the address, share percentage, and dollar value.

---

## New Features

1. **Institutional Collateral Preset Menu (`main.py`)**
   * Added 5 main menu presets: **WETH**, **WBTC**, **XAUT**, **wstETH**, and **Custom Token**. Presets 1–4 skip the benchmark test automatically and route directly into the Aave V3 + SignGuard simulator.
2. **Regulated Issuer Compliance Check (`main.py`)**
   * Added a dictionary of regulated institutional issuers (Tether USD, Tether Gold, Circle USDC). When bytecode selectors are detected on a regulated issuer, they are flagged in cyan as `REGULATED COMPLIANCE CONTROL` rather than a red security trap.
3. **TBC Safe LTV Buffer & Auto-Shield Calculator (`aave_sim.py`)**
   * Updated `liquidation_simulator` to accept `price_impact` and display the **TBC SignGuard Safe LTV Cap** (`max LTV - 12%`, minus an additional `5%` if `price_impact > 20%`). Added Calculation D featuring alert price, 1-tap top-up in USD/GEL, bot penalty vs. shield fee comparison, and client savings.
4. **Live 12-Second Ethereum Block & Position Monitor (`main.py`, Menu Option 2)**
   * Polls live `eth_blockNumber` and `eth_gasPrice` from `https://eth.drpc.org` every 12 seconds, displays simulated LTV status, and indicates `$0.00 (Read-Only View Call)`.

---

## Test Suite Updates (`input_tests.py`)
* Updated math edge-case tests to align with `aave_sim.py` division-by-zero guards so zero-collateral and zero-threshold cases pass cleanly.
* Updated the summary report to enumerate all 16 bug fixes and 4 new features in place of the static `"Key findings"` placeholder[cite: 1, 2].
