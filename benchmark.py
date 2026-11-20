from colorama import Fore
import requests
import yfinance as yf


class Benchmark:
    #The Test and Benchmark
    def benchmark_test(self, user_target_price, user_invest_amount, token_price_usd, token_real_supply):
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
        elif 1000000000.00 < marketcap < 10000000000.00:
            return Fore.LIGHTYELLOW_EX + f"{marketcap:,.2f} $ \nMarket Cap is less than 10 Billion"
        else:
            return Fore.GREEN + f"{marketcap:,.2f} $\nMarket Cap is More than 10 Billion"


    #defining a user inputted Coin
    def get_dex_token_data(self, user_query):
        #Sanitizing the user_input to ensure proper format
        user_query = user_query.strip()
        token = user_query.lower()

        #initiating fallback links for data gathering
        dex_links = [
            f"https://api.dexscreener.com/latest/dex/search?q={user_query}",
            f"https://api.dexscreener.com/latest/dex/tokens/{user_query}"
        ]

        #try/except for error handling
        for link in dex_links:
            try:
                resp = requests.get(link)

                #Checking response status code
                if resp.status_code != 200:
                    print(Fore.RED + f"Link has an Issue | {link}")
                    continue
                #if data is good unpack json data
                dex_data = resp.json()
                #Checking if pairs is in dex_data and dex_data["pairs"] does actually contain something
                if "pairs" in dex_data and dex_data["pairs"] is not None:

                    pairs_list = dex_data["pairs"]
                    #looping through the pairs
                    for pair in pairs_list:
                        #Checking for conditions, and if our list data matches everything we are trying to retrieve
                        if pair.get("chainId") == "ethereum" and "liquidity" in pair and (pair["baseToken"]["symbol"].lower() == user_query.lower()
                                or pair["baseToken"]["address"].lower() == user_query.lower()):
                            token_addrs = pair["baseToken"]["address"]
                            dex_name = pair["dexId"]
                            pool_token_reserve = float(pair["liquidity"]["base"])
                            print(Fore.GREEN + f"DEX POOL Was Found | {dex_name}")
                            #returning gathered values
                            return token_addrs, dex_name, pool_token_reserve
                        #checking if a query matches the quote token or a 0x address
                        elif pair.get("chainId") == "ethereum" and "liquidity" in pair and (pair["quoteToken"]["symbol"].lower() == user_query.lower() or pair["quoteToken"]["address"].lower() == user_query.lower()):
                            token_addrs = pair["quoteToken"]["address"]
                            dex_name = pair["dexId"]
                            pool_token_reserve = float(pair["liquidity"]["quote"])
                            print(Fore.GREEN + f"DEX POOL Was Found | {dex_name}")
                            # returning gathered values
                            return token_addrs, dex_name, pool_token_reserve

                elif "pairs" not in dex_data or dex_data["pairs"] is None:
                    print(Fore.RED + "dex_data[pairs] is empty")
                    #Continuing to second link
                    continue
                else:
                    print(Fore.RED + "Something went Wrong!")
                    continue
            except requests.exceptions.RequestException as e:
                print(Fore.RED + f"Connection Error {str(e)}")
                continue
        #if All fails, fallback to address
        if user_query.startswith("0x") and len(user_query) == 42:
            dex_name = "Mock 5% pool"
            pool_token_reserve = 0
            return user_query,dex_name, pool_token_reserve
        else:
            print(Fore.RED + "Address Was Not Found")
            return None, None, 0
