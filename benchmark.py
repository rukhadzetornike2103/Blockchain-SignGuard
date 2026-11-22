from colorama import Fore
import requests
import yfinance as yf


class Benchmark:
    #The Test and Benchmark
    def benchmark_test(self, user_target_price, user_invest_amount, token_price_usd, token_real_supply):
        #Guard against zero or negative inputs so we never hit division by zero
        if token_price_usd <= 0:
            print(Fore.RED + "Token price must be greater than 0. Benchmark test skipped.")
            return None
        if token_real_supply <= 0:
            print(Fore.RED + "Token supply must be greater than 0. Benchmark test skipped.")
            return None
        if user_target_price <= 0:
            print(Fore.RED + "Target price must be greater than 0. Benchmark test skipped.")
            return None
        if user_invest_amount < 0:
            print(Fore.RED + "Invest amount cannot be negative. Benchmark test skipped.")
            return None

        #we will fetch market caps from coinGecko
        #try/except to handle communicating with servers
        #initialize the market caps for gold btc and tsla, if fetching fails
        gold_mcap = 29000000000000
        btc_mcap = 1600000000000
        tsla_mcap = 1400000000000
        try:
            geckoURL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_market_cap=true"
            coinResp = requests.get(geckoURL, timeout = 5)
            if coinResp.status_code != 200:
                print(Fore.RED + f"Could Not Access URL | {geckoURL}")



            #Extracting GOLD, BTC, TESLA_MCAP
            try:
                coinData = coinResp.json()
                btc_mcap = coinData["bitcoin"]["usd_market_cap"]
            except Exception as e:
                print(f"Failed Fetching Bitcoing M-CAP {str(e)}")

            try:
                tsla = yf.Ticker("TSLA")
                fetched_tsla_mcap = tsla.info.get("marketCap")
                #added fallback to coin market caps
                if fetched_tsla_mcap:
                    tsla_mcap = fetched_tsla_mcap
            except Exception as e:
                print(f"Failed Fetching TESLA M-CAP {str(e)}")


            try:
                gold = yf.Ticker("GC=F")
                #history set to 5days since sundays prove not to send out proper data
                hist = gold.history(period="5d")
                if not hist.empty:
                    price_per_ounce = float(hist['Close'].iloc[-1])

                    #Convert To Metric scale
                    grams_per_troy_ounce = 31.1034768
                    grams_per_metric_ton = 1000000
                    troy_ounces_per_ton = grams_per_metric_ton / grams_per_troy_ounce

                    total_gold_tons = 212500
                    price_per_ton = price_per_ounce * troy_ounces_per_ton

                    gold_mcap = price_per_ton * total_gold_tons
            except Exception as e:
                print(f"Error fetching Gold Price: {str(e)}")

            #after handling all of these errors and gathering market caps
            #we start the benchmark code
            #Calculating growth
            growth_x = user_target_price / token_price_usd
            #Calculating required Market Cap
            trgt_mcap = token_real_supply * user_target_price
            #Calculate the three Mcap ratios with our target price to determine how realistic it would be
            gld_ratio = trgt_mcap / gold_mcap

            tsla_ratio = trgt_mcap / tsla_mcap

            btc_ratio = trgt_mcap / btc_mcap
            #hypothetical growth
            expected_payout = user_invest_amount * growth_x

            max_price_at_tsla = tsla_mcap / token_real_supply
            max_price_at_btc = btc_mcap / token_real_supply
            max_price_at_gold = gold_mcap / token_real_supply

            print("Analysis Done...")
            #I should add with the print statements the actual price of the coin currently
            if trgt_mcap >= gold_mcap:
                print(Fore.RED + f"!!!CRITICAL MEMECOIN TRAP!!!")
                print(f"Required Target Market Cap | ${trgt_mcap:,.2f}")
                print(f"Ratio to Global Gold       | {gld_ratio:.2f}x Larger than all the Gold")
                print(f"Target Growth (X)          | {growth_x:,.2f}x")
                print(f"Expected Payout            | ${expected_payout:,.2f}")
                print(f"Max Possible Price at Gold | ${max_price_at_gold:,.10f}")


            elif trgt_mcap >= btc_mcap:
                print(Fore.RED + f"!!!CRITICAL MEMECOIN TRAP!!!")
                print(f"Required Target Market Cap | ${trgt_mcap:,.2f}")
                print(f"Ratio to Bitcoin M-Cap     | {btc_ratio:.2f}x Larger than BTC")
                print(f"Target Growth (X)          | {growth_x:,.2f}x")
                print(f"Expected Payout            | ${expected_payout:,.2f}")
                print(f"Max Possible Price at BTC  | ${max_price_at_btc:,.10f}")

            elif trgt_mcap >= tsla_mcap:
                print(Fore.RED + f"!!!CRITICAL MEMECOIN TRAP!!!")
                print(f"Required Target Market Cap | ${trgt_mcap:,.2f}")
                print(f"Ratio to Tesla M-Cap       | {tsla_ratio:.2f}x Larger than TESLA")
                print(f"Target Growth (X)          | {growth_x:,.2f}x")
                print(f"Expected Payout            | ${expected_payout:,.2f}")
                print(f"Max Possible Price at TSLA | ${max_price_at_tsla:,.10f}")


            elif trgt_mcap >= 100000000000:
                print(Fore.YELLOW + "High Ambition: Requires: 100B+ $ (Top 5 Global Crypto Asset)")
                print(f"Required Target Market Cap | ${trgt_mcap:,.2f}")
                print(f"Target Growth (X)          | {growth_x:,.2f}x")
                print(f"Expected Payout            | ${expected_payout:,.2f}")

            else:
                print(Fore.GREEN + "Realistic Target")
                print(f"Required Market Cap        | ${trgt_mcap:,.2f} can be achieved\n"
                      f"Target Growth (X)          | {growth_x:,.2f}x\n"
                      f"Expected Payout            | ${expected_payout:,.2f}\n"
                      f"However, unlikely if Meme-Coin")
            return None



        except requests.exceptions.RequestException as a:
            print(f"Connection Error {str(a)}")


    #Determining Market Cap, to see weather it is a small/medium or Large Cap
    def determine_cap(self, marketcap):
        if marketcap < 1000000000.00:
            return Fore.YELLOW + f"{marketcap:,.2f} $\nMarket Cap is less than 1 Billion"
        elif 1000000000.00 <= marketcap < 10000000000.00:
            return Fore.LIGHTYELLOW_EX + f"{marketcap:,.2f} $ \nMarket Cap is less than 10 Billion"
        else:
            return Fore.GREEN + f"{marketcap:,.2f} $\nMarket Cap is More than 10 Billion"


    #defining a user inputted Coin
    def get_dex_token_data(self, user_query):
        # Layer 1 — Canonical Blue-Chip Dictionary
        # Sanitizing the user_input to ensure proper format
        user_query = user_query.strip()
        token = user_query.lower()

        # Mapping common tickers to their official Ethereum Mainnet contract addresses
        dex_token_dict = {"eth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                          "weth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                          "btc": "0x2260FAC5E5542a773aa44fBCfeDf7C193bc2C599",
                          "wbtc": "0x2260FAC5E5542a773aa44fBCfeDf7C193bc2C599",
                          "usdt": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                          "usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                          "uni": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
                          "link": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
                          "aave": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
                          "xaut": "0x68749665FF8D2d112Fa859AA293F07A622782F38",
                          "wsteth": "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0"
                          }

        #do not send empty queries to DexScreener or CoinGecko
        if not user_query:
            print(Fore.RED + "Empty token query. Please enter a valid token symbol or address.")
            return None, None, 0

        # Check if lowercase input is a key in the dictionary
        if token in dex_token_dict:
            canonical_addr = dex_token_dict[token]
            print(Fore.YELLOW + f"Translated '{token}' -> canonical address {canonical_addr}")
            user_query = canonical_addr

        # Layer 2 — Smart Endpoint Routing + Deepest Pool Selection
        is_address = user_query.startswith("0x") and len(user_query) == 42

        # Build endpoint list based on input type
        if is_address:
            # Address input: query only /tokens/ to bypass cross-chain search noise
            dex_links = [f"https://api.dexscreener.com/latest/dex/tokens/{user_query}"]
        else:
            # Symbol input: use /search/ endpoint
            dex_links = [f"https://api.dexscreener.com/latest/dex/search?q={user_query}"]

        # Initialize "best pool" variables for deepest pool selection
        best_token_addr = None
        best_dex_name = None
        best_pool_reserve = 0.0
        best_usd_liquidity = 0

        # try/except for error handling
        for link in dex_links:
            try:
                resp = requests.get(link, timeout=10)

                # Checking response status code
                if resp.status_code != 200:
                    print(Fore.RED + f"Link has an Issue | {link}")
                    continue
                # if data is good unpack json data
                dex_data = resp.json()
                # Checking if pairs is in dex_data and dex_data["pairs"] does actually contain something
                if "pairs" in dex_data and dex_data["pairs"] is not None:

                    pairs_list = dex_data["pairs"]
                    # looping through ALL pairs to find the deepest pool
                    for pair in pairs_list:
                        if pair.get("chainId") != "ethereum" or "liquidity" not in pair:
                            continue

                        # Check if this pair matches our token (base or quote)
                        is_base_match = (pair["baseToken"]["symbol"].lower() == token or
                                         pair["baseToken"]["address"].lower() == user_query.lower())
                        is_quote_match = (pair["quoteToken"]["symbol"].lower() == token or
                                          pair["quoteToken"]["address"].lower() == user_query.lower())

                        if is_base_match:
                            token_addr = pair["baseToken"]["address"]
                            dex_name = pair["dexId"]
                            pool_reserve = float(pair["liquidity"]["base"])
                            usd_liq = pair["liquidity"].get("usd", 0)

                            # Only overwrite if this pool has deeper USD liquidity
                            if usd_liq > best_usd_liquidity:
                                best_token_addr = token_addr
                                best_dex_name = dex_name
                                best_pool_reserve = pool_reserve
                                best_usd_liquidity = usd_liq

                        elif is_quote_match:
                            token_addr = pair["quoteToken"]["address"]
                            dex_name = pair["dexId"]
                            pool_reserve = float(pair["liquidity"]["quote"])
                            usd_liq = pair["liquidity"].get("usd", 0)

                            # Only overwrite if this pool has deeper USD liquidity
                            if usd_liq > best_usd_liquidity:
                                best_token_addr = token_addr
                                best_dex_name = dex_name
                                best_pool_reserve = pool_reserve
                                best_usd_liquidity = usd_liq

                elif "pairs" not in dex_data or dex_data["pairs"] is None:
                    print(Fore.RED + "dex_data[pairs] is empty")
                    continue
                else:
                    print(Fore.RED + "Something went Wrong!")
                    continue
            except requests.exceptions.RequestException as e:
                print(Fore.RED + f"Connection Error {str(e)}")
                continue

        # If we found the deepest pool, return it
        if best_token_addr is not None:
            print(Fore.GREEN + f"DEX POOL Was Found | {best_dex_name} (deepest pool, ${best_usd_liquidity:,.2f} USD liquidity)")
            return best_token_addr, best_dex_name, best_pool_reserve

        # Layer 3 — CoinGecko Address Fallback
        if not is_address:
            print(Fore.YELLOW + "DexScreener found no Ethereum pairs. Trying CoinGecko fallback...")
            try:
                # Step 1: Search CoinGecko for the ticker
                search_url = f"https://api.coingecko.com/api/v3/search?query={user_query}"
                search_resp = requests.get(search_url, timeout=5)
                if search_resp.status_code == 200:
                    search_data = search_resp.json()
                    coins = search_data.get("coins", [])

                    # Find exact symbol match
                    target_coin_id = None
                    for coin in coins:
                        if coin.get("symbol", "").lower() == token:
                            target_coin_id = coin.get("id")
                            break

                    if target_coin_id:
                        # Step 2: Get coin details to find Ethereum platform address
                        coin_url = f"https://api.coingecko.com/api/v3/coins/{target_coin_id}"
                        coin_resp = requests.get(coin_url, timeout=5)
                        if coin_resp.status_code == 200:
                            coin_data = coin_resp.json()
                            platforms = coin_data.get("platforms", {})
                            cg_eth_addr = platforms.get("ethereum")

                            if cg_eth_addr and cg_eth_addr != "0x0000000000000000000000000000000000000000":
                                print(Fore.YELLOW + f"CoinGecko found Ethereum address: {cg_eth_addr}")
                                # Step 3: Pass the address back into DexScreener /tokens/ endpoint
                                tokens_url = f"https://api.dexscreener.com/latest/dex/tokens/{cg_eth_addr}"
                                tokens_resp = requests.get(tokens_url, timeout=10)
                                if tokens_resp.status_code == 200:
                                    tokens_data = tokens_resp.json()
                                    if "pairs" in tokens_data and tokens_data["pairs"]:
                                        # Find deepest Ethereum pool for this address
                                        for pair in tokens_data["pairs"]:
                                            if pair.get("chainId") == "ethereum" and "liquidity" in pair:
                                                is_base = pair["baseToken"]["address"].lower() == cg_eth_addr.lower()
                                                is_quote = pair["quoteToken"]["address"].lower() == cg_eth_addr.lower()
                                                if is_base or is_quote:
                                                    if is_base:
                                                        t_addr = pair["baseToken"]["address"]
                                                        t_reserve = float(pair["liquidity"]["base"])
                                                    else:
                                                        t_addr = pair["quoteToken"]["address"]
                                                        t_reserve = float(pair["liquidity"]["quote"])
                                                    t_usd = pair["liquidity"].get("usd", 0)
                                                    if t_usd > best_usd_liquidity:
                                                        best_token_addr = t_addr
                                                        best_dex_name = pair["dexId"]
                                                        best_pool_reserve = t_reserve
                                                        best_usd_liquidity = t_usd

                                        if best_token_addr is not None:
                                            print(Fore.GREEN + f"DEX POOL Was Found | {best_dex_name} (via CoinGecko fallback)")
                                            return best_token_addr, best_dex_name, best_pool_reserve

                                # If DexScreener has no pool, fall through to mock
                                print(Fore.YELLOW + "No DEX pool found on DexScreener for CoinGecko address. Using mock pool.")
                                return cg_eth_addr, "Mock 5% pool", 0
                            else:
                                print(Fore.RED + "CoinGecko lists no Ethereum address for this token.")
                        else:
                            print(Fore.RED + f"CoinGecko coin details failed with status {coin_resp.status_code}")
                    else:
                        print(Fore.RED + f"CoinGecko search returned no exact symbol match for '{token}'.")
                else:
                    print(Fore.RED + f"CoinGecko search failed with status {search_resp.status_code}")
            except requests.exceptions.RequestException as e:
                print(Fore.RED + f"CoinGecko fallback connection error: {str(e)}")

        # Final fallback — if user_query is an address, return it with a mock pool
        if user_query.startswith("0x") and len(user_query) == 42:
            #before allowing the mock fallback, verify the 40 chars after 0x are valid hex
            valid_hex = True
            hex_part = user_query[2:]
            for char in hex_part:
                if char not in "0123456789abcdefABCDEF":
                    valid_hex = False
                    break
            if not valid_hex:
                print(Fore.RED + f"Invalid hex characters in address: {user_query}")
                return None, None, 0
            print(Fore.YELLOW + "No live DEX pool found. Using mock pool.")
            return user_query, "Mock 5% pool", 0
        else:
            print(Fore.RED + "Address Was Not Found")
            return None, None, 0
