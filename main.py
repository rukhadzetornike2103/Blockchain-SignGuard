
from colorama import Fore
import requests
import yfinance as yf
#importing yfinance to gather info about gold, tsla_mcap, etc.




#LTV and Dual-Unit Liquidation
def get_live_aave_params(token_address, symbol):
    #storing avve provider
    aave_provider = "0x7B4EB56E7CD4b454BA8ff71E4518426369a138a3"

    #Solidity has 4-byte keccak selector which is -> "0x3e150141"
    #To pass the user's token address it must have 24 0's in the beggining
                                                            #removing 0x from address
    call_data = "0x3e150141" + "000000000000000000000000" + token_address[2:].lower()

    rpc_payload = {
        "jsonrpc":"2.0",
        "params":[{"to": aave_provider, "data": call_data}, "latest"],
        "id": 1,
        "method": "eth_call"
                   }


    rpc_url = "https://eth.drpc.org"
    #sending Post request
    try:
        aave_resp = requests.post(rpc_url, json=rpc_payload, timeout=5)
        if aave_resp.status_code != 200:
            return Fore.RED + f"Something went wrong {aave_resp.status_code}"

        #if link responds
        hex_result = aave_resp.json()["result"]
        #hex result is gigantic, check if it is actually gigantic
        if len(hex_result) > 260:
            #split up the result
            chunk1 = int(hex_result[2:66], 16)
            #max ltv is stored in basis points like 7050 70.50%
            max_ltv = int(hex_result[66:130], 16) / 100
            #liquidation threshold is also stored in basis points
            liq_threshold = int(hex_result[130:194], 16) / 100
            #same with penalty/bonus
            raw_bonus = int(hex_result[194:258], 16) / 100
            #however, raw bonus should be checked
            if raw_bonus > 100:
                #subtract 100 to retrieve actual percentage
                liq_penalty = raw_bonus - 100
            else:
                liq_penalty = 5.0

            #Meme-coins can't be collateral
            if max_ltv > 0:
                print(Fore.GREEN + f"Aave V3 on-chain parameters were extracted for {symbol} !")
                return max_ltv, liq_threshold, liq_penalty, True
            else:
                print(Fore.YELLOW + f"{symbol} is rejected on Aave V3 (0% Max LTV)\n"
                                    f"Application will load default parameters as a mock test\n"
                                    f"!!! -> DO NOT INTERPRET THIS AS ACTUAL INFO <- !!!\n"
                                    f"Max LTV = 75.0 | Liquidation Threshold = 80.0 | Liquidation Penalty = 5.0")
                return 75.0, 80.0, 5.0, False
        else:
            return 75.0, 80.0, 5.0, False


    except Exception as e1:
        print(Fore.RED + str(e1))
        return None


#Building Aave_liquidation_simulator
def liquidation_simulator(token_address, symbol, price_usd, crashed_price):
    #First, we check if the user wants to run the simulation on the token they have used already
    print(Fore.CYAN + f"{'----Simulation Active----':^60}")
    print(f"----{'This is a pure knowledge based simulation----':^40}")
    print(f"----{'The program and user are not responsible for any money lost----':^40}")
    #Testing Current Coin or switch?
    while True:
        use_current = input(Fore.LIGHTWHITE_EX + f"Run Aave Liquidation Test on Current Token? ").strip().lower()
        if use_current in ["yes", "y", "no", "n"]:
            break
        print(Fore.RED + "Invalid input, please enter 'y'(yes) or 'n'(no)")
    #Grabbing user input
    switched_coin = False

    #Handling the case where user wishes to change the coin for the simulation
    if use_current in ["no", "n"]:
        switched_coin = True
        changing_coin = True
        while changing_coin:
            # this will only run these 4 handwritten coins or a specific address, could use improvement
            new_query = input(Fore.LIGHTWHITE_EX + "Enter the coin you wish to run the simulation on\n"
                                                   "(BTC, ETH, LINK, UNI or 0x address: ").strip()

            # now we code the translator
            if new_query.lower() == "btc":
                symbol = "WBTC"
                token_address = "0x2260FAC5E5542a773aa44fBCfeDf7C193bc2C599"
                print(Fore.YELLOW + f"Translated 'BTC' -> Wrapped Bitcoin ({symbol}) | {token_address}")
                changing_coin = False
            elif new_query.lower() == "eth":
                symbol = "WETH"
                token_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
                print(Fore.YELLOW + f"Translated 'ETH' -> Wrapped Ether ({symbol}) | {token_address}")
                changing_coin = False
            else:
                # resolving the issue of "0x" by calling the existing function
                resolved_addr, _, _ = get_dex_token_data(new_query)
                if not resolved_addr:
                    print(Fore.RED + "Could not resolve the given address, Enter a proper Address")
                    continue
                token_address = resolved_addr
                symbol = new_query.upper()
                changing_coin = False

    if switched_coin:
        new_resp = requests.get(f"https://api.ethplorer.io/getTokenInfo/{token_address}/?apiKey=freekey", timeout=5)
        new_data = new_resp.json()
        price_usd = float(new_data["price"]["rate"])
        crashed_price = price_usd * 0.70

    #now we fetch the live Aave Parameters on this coin
    try:
        maximum_ltv, liquidation_threshold, liquidation_penalty, is_aave_listed = get_live_aave_params(token_address, symbol)
        print(Fore.GREEN + f"{f'----{symbol}----':^30}\n"
              f"Live Price Today       | {price_usd:,.4f} $\n"
              f"Max LTV Allowed        | {maximum_ltv:.2f}%\n"
              f"Liquidation Threshold  | {liquidation_threshold:.2f}%\n"
              f"Liquidator Bot Penalty | {liquidation_penalty:.2f}%\n")

        #now we do the math, Input coin amount and retrieve it's live USD Value
        collateral = float(input(Fore.CYAN + f"Enter the amount of {symbol} you wish to deposit as collateral -> ").strip())
        #calculating Today's live USD value of the collateral
        collateral_usd = collateral * price_usd
        #calculating maximum borrow in both crypto and USD
        max_loan_usd = collateral_usd * (maximum_ltv / 100)
        max_loan_crypto = collateral * (maximum_ltv / 100)
        #Giving the user their results
        print(Fore.GREEN + f"{'----Maximum Borrow/Loan Limit----':^60}\n"
              f"Max {symbol} That Can be Borrowed | {max_loan_crypto:,.2f} {symbol}\n"
              f"Max USD That Can be Borrowed  | {max_loan_usd:,.2f} $")

        loanGranting = True
        loanGranting = True
        while loanGranting:
            try:
                user_choice = int(input(Fore.CYAN + "\nWould you like to estimate your loan?\n"
                                                    f"If yes, in {symbol} or USD?\n"
                                                    f"1. {symbol}\n"
                                                    f"2. USD\n"
                                                    f"3. Exit\n"
                                                    f"--> "))
            except ValueError:
                print(Fore.RED + "Invalid input! Please enter 1, 2, or 3.")
                continue

            if user_choice == 1:
                # If user decides to choose Crypto
                loan_coins = float(input(f"Enter your {symbol} loan amount: "))
                loan_usd = loan_coins * price_usd
                print(f"USD Equivalent of {loan_coins:,.4f} {symbol} | {loan_usd:,.4f} $")

            elif user_choice == 2:
                # If user decides to input dollar value
                loan_usd = float(input("Enter your USD loan amount: "))
                loan_coins = loan_usd / price_usd
                print(f"{symbol} Equivalent of {loan_usd:,.2f} $ | {loan_coins:,.4f} {symbol}")

            elif user_choice == 3:
                loanGranting = False
                continue
            else:
                print(Fore.RED + f"Something went wrong with your input, please enter a valid one: {user_choice}")
                continue

            # Guard against 0 or negative loans so division doesn't break logic
            if loan_usd <= 0:
                print(Fore.RED + "Loan amount must be greater than 0.")
                continue


            print(Fore.CYAN + f"\n{'----Calculation A: Current Position & Liquidation Price----':^60}")
            current_ltv = (loan_usd / collateral_usd) * 100
            min_collateral_usd = loan_usd / (liquidation_threshold / 100)
            liquidation_price_usd = min_collateral_usd / collateral

            print(f"Current Loan-to-Value (LTV) | {current_ltv:.2f}%")
            print(f"Min Collateral Value Needed | ${min_collateral_usd:,.2f}")
            print(f"Exact Liquidation Price     | ${liquidation_price_usd:,.4f} per {symbol}")

            if current_ltv >= liquidation_threshold:
                print(Fore.RED + "STATUS: !!! THIS IS LIQUIDATABLE IMMEDIATELY !!!")
            elif current_ltv > maximum_ltv:
                print(Fore.YELLOW + "STATUS: Exceeds Aave's Max Borrow Rule!")
            else:
                print(Fore.GREEN + "STATUS: Position is Currently Active & Safe")

            print(Fore.CYAN + f"\n{'----Calculation B: 1-Year Unpaid Interest Creep----':^70}")
            supply_apy = 0.01  # 1% collateral growth
            borrow_apy = 0.05  # 5% debt growth

            collateral_usd_1yr = collateral_usd * (1 + supply_apy)
            loan_usd_1yr = loan_usd * (1 + borrow_apy)
            ltv_1yr = (loan_usd_1yr / collateral_usd_1yr) * 100
            loan_coins_1yr = loan_usd_1yr / price_usd

            print(f"1-Yr Collateral Value (+1%) | ${collateral_usd_1yr:,.2f}")
            print(f"1-Yr Debt Value (+5%)       | ${loan_usd_1yr:,.2f} ({loan_coins_1yr:,.4f} {symbol})")
            print(f"1-Yr Projected LTV          | {ltv_1yr:.2f}%")

            if ltv_1yr >= liquidation_threshold:
                print(Fore.RED + f"WARNING: 1 year of unpaid block interest alone will trigger liquidation "
                                 f"even if {symbol}'s price never drops!")
            else:
                print(
                    Fore.GREEN + f"SAFE: Position survives 1 year of unpaid interest (under {liquidation_threshold:.2f}% threshold).")


            print(Fore.CYAN + f"\n{'----Calculation C: Whale Dump & Liquidator Bot Seizure----':^70}")
            crashed_collateral_usd = collateral * crashed_price
            crashed_ltv = (loan_usd / crashed_collateral_usd) * 100

            print(f"Simulated Crash Price       | ${crashed_price:,.4f}")
            print(f"Post-Crash Collateral Value | ${crashed_collateral_usd:,.2f}")
            print(f"Post-Crash LTV              | {crashed_ltv:.2f}%")

            if crashed_ltv >= liquidation_threshold:
                print(Fore.RED + "!!! WHALE DUMP TRIGGERED LIQUIDATION !!!")
                bot_seized_usd = loan_usd * (1 + (liquidation_penalty / 100))
                bot_seized_coins = bot_seized_usd / crashed_price
                leftover_usd = crashed_collateral_usd - bot_seized_usd

                if leftover_usd < 0:
                    leftover_usd = 0.0
                    print(
                        Fore.RED + f"Liquidator Bot Seized       | ${bot_seized_usd:,.2f} ({bot_seized_coins:,.4f} {symbol})")
                    print(Fore.RED + "Remaining User Collateral   | $0.00 (100% Wiped Out -> Protocol Bad Debt!)")
                else:
                    leftover_coins = leftover_usd / crashed_price
                    print(
                        Fore.YELLOW + f"Liquidator Bot Seized       | ${bot_seized_usd:,.2f} ({bot_seized_coins:,.4f} {symbol})")
                    print(
                        Fore.GREEN + f"Remaining User Collateral   | ${leftover_usd:,.2f} ({leftover_coins:,.4f} {symbol})")
            else:
                print(
                    Fore.GREEN + f"SURVIVED: Even after a drop to ${crashed_price:,.4f}, your LTV ({crashed_ltv:.2f}%) "
                                 f"remains below the {liquidation_threshold:.2f}% liquidation threshold.")



    except Exception as e2:
        print(Fore.RED + f"Something went wrong {str(e2)}")




#The Test and Benchmark
def benchmark_test(user_target_price, user_invest_amount, token_price_usd, token_real_supply):
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
            hist = gold.history(period="1d")
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
def determine_cap(marketcap):
    if marketcap < 1000000000.00:
        return Fore.YELLOW + f"{marketcap:,.2f} $\nMarket Cap is less than 1 Billion"
    elif 1000000000.00 < marketcap < 10000000000.00:
        return Fore.LIGHTYELLOW_EX + f"{marketcap:,.2f} $ \nMarket Cap is less than 10 Billion"
    else:
        return Fore.GREEN + f"{marketcap:,.2f} $\nMarket Cap is More than 10 Billion"


#defining a user inputted Coin
def get_dex_token_data(user_query):
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


if __name__ == "__main__":




    while True:
        choice= int(input(Fore.LIGHTWHITE_EX + "Enter what you wish to do?\n"
                          "1. Scan Address\n"
                          "2. Exit\n"
                          "-->"))
        if choice == 1:

            #Changed Token_address handling to implement the above function
            token_symbol = input("Enter token symbol (e.g. PEPE, WBTC, UNI) or 0x address: ")
            #passing the symbol to function get_dex_token_data
            token_address, dex_name, live_pool_tokens = get_dex_token_data(token_symbol)
            #Checking if token_address is available, if not "continue" to restart the loop
            if not token_address:
                continue
            print("Searching Token Info")
            #this is the token Address

            url = f"https://api.ethplorer.io/getTokenInfo/{token_address}/?apiKey=freekey"


            try:
                response = requests.get(url)
                if response.status_code != 200:
                    print(Fore.RED + f"url threw Error | Code: {response.status_code}")

                data = response.json()
                if "error" in data:
                    print(Fore.RED + "Failed to Retrieve Data")

                #Extract data from data = response.json()
                name = data["name"]
                symbol = data["symbol"]
                decimals = int(data["decimals"])
                raw_supply = float(data["totalSupply"])
                price_usd = float(data["price"]["rate"])

                #Calculating real supply by dividing raw_supply by 10 to the power of decimals
                real_supply = raw_supply / (10 ** decimals)
                print(Fore.GREEN + f"Real Supply: | {real_supply:,.2f} {symbol}")

                #calculating Market_Cap
                market_cap = real_supply * price_usd
                print(Fore.GREEN + f"Market Cap:  | {market_cap:,.2f} $")

                #Examining for Smart Contracts
                rpc_url = "https://eth.drpc.org"
                payload = {"jsonrpc":"2.0",
                           "method": "eth_getCode",
                           "params": [token_address, "latest"],
                           "id": 1}

                #Sending POST request
                response = requests.post(rpc_url, json=payload)

                if response.status_code != 200:
                    print(Fore.RED + f"url threw Error Code: {response.status_code}")

                rpc_data = response.json()

                if "result" not in rpc_data:
                    print(Fore.RED + f"Data access failed")

                bytecode = rpc_data["result"]
                contract_risk = []
                #independent "if" statements to keep logging
                if bytecode == "0x" or bytecode.startswith("0xef01"):
                    print(Fore.YELLOW + f"The Address {token_address} is an EOA")
                #Checking for centralized minting risk
                if "40c10f19" in bytecode:
                    contract_risk.append("Centralized minting | Can Create New Tokens")
                #Checking for addresses which might have pause capabilities
                if "8456cb59" in bytecode:
                    contract_risk.append("Pause Function | Can Freeze All Trading")
                #Checking for Blacklist Function
                if "0ecb93c0" in bytecode:
                    contract_risk.append("Blacklist Function | Can Freeze User Balances")
                #Checking for Centralized Owner Control
                if "f2fde38b" in bytecode:
                    contract_risk.append("Centralized Owner Control | Transfer Ownership")

                #Checking if there is no risks first to print that there were no risks found
                if not contract_risk:
                    print(Fore.GREEN + "No Risks Found!")
                #if risks were found print risks
                for risk in contract_risk:

                    #in case empty list variable, still printing no risks found
                    if not risk:
                        print(Fore.GREEN + "No Risks Found!")
                    else:
                        print(Fore.RED + risk)

                #starting a loop to ensure the user enters either yes or not
                while True:
                    user_input1 = input(Fore.LIGHTWHITE_EX + "Would you like to enter a specific number of top holders you wish to list? ")
                    if user_input1.lower() not in ["yes", "y", "no", "n"]:
                        print(Fore.RED + "This is an invalid input, please enter either yes or no")
                    else:
                        break

                if user_input1.lower() == "yes" or user_input1.lower() == "y":
                    n = int(input(Fore.LIGHTWHITE_EX + "Enter the amount of Top holders you wish to list -> "))
                else:
                    n = 5

                #Hunting for whales
                whale_url = f"https://api.ethplorer.io/getTopTokenHolders/{token_address}?apiKey=freekey&limit={n}"
                response = requests.get(whale_url)

                if response.status_code != 200:
                    print(Fore.RED + f"url threw Error | Code: {response.status_code}")


                whale_data = response.json()
                holders_list = whale_data["holders"]
                total_share = 0
                total_amt = 0
                for holder in holders_list:
                    holder_address = holder["address"]
                    share = float(holder["share"])
                    #print(Fore.GREEN + f"Address: {holder_address:<10} | Share: {share:.2f} %")
                    payload["params"][0] = holder_address
                    resp = requests.post(rpc_url, json=payload)
                    bytecode = resp.json()["result"]
                    #Address Token Amount
                    address_amount = real_supply * (share / 100)
                    #creating a single holder's dollar value
                    holder_dollar_value = address_amount * price_usd
                    #Adding Holder's Dollar Value to the total Amount they hold
                    total_amt += holder_dollar_value

                    #Checking if address was permanently removed or burned
                    if holder_address.endswith("dead") or holder_address.endswith("000000"):
                        print(Fore.BLUE + "This is a burn Address")
                    #changed to Elif, since just if would throw out incorrect info
                    elif bytecode == "0x" or bytecode.startswith("0xef01"):
                        if share >= 50.0:
                            print(Fore.RED + f"Address: {holder_address:<10} | Share: {share:.2f}% | Amount: {holder_dollar_value:,.2f} $ \n"
                                             f"Can Crash The Token")
                        else:
                            print(Fore.YELLOW + f"Address: {holder_address:<10} | Share: {share:.2f}% | Amount: {holder_dollar_value:,.2f} $  \n"
                                                f"EOA Address, share is safe")
                    else:                                                                   #amount should hold "holder_dollar_value" Not address_amount
                        print(Fore.GREEN + f"Address: {holder_address:<10} | Share: {share:.2f}% | Amount: {holder_dollar_value:,.2f} $ ")

                    total_share += share
                print("-" * 107)
                print(f"Top {n} Addresses hold {total_share:.2f} % | Total Dollar Amount: {total_amt:,.2f} $ | Real Supply: {real_supply:,.2f} $")



            except requests.exceptions.RequestException as e:
                print(Fore.RED + str(e))



            #Creating a mock AMM, assuming 5% of total token supply is sitting on Uniswap DEX pool
            #checking if live_pool_tokens is more than zero, if yes, pool_tokens = live_pool_tokens
            if live_pool_tokens > 0:
                pool_tokens = live_pool_tokens
            else:
                #fallback to real_supply * 0.05 if live_pool_tokens is not more than 0
                pool_tokens = real_supply * 0.05

            pool_usd = pool_tokens * price_usd
            k = pool_tokens * pool_usd

            current_price = pool_usd / pool_tokens

            #grabbing the biggest whale's balance
            whale_balance = real_supply * (float(holders_list[0]["share"]) / 100)
            #The whale adds their tokens to the pool
            new_pool_tokens = pool_tokens + whale_balance
            #now calculating the new USD reserve to keep K constant

            new_pool_usd = k / new_pool_tokens

            #calculate the crashed price
            crashed_price = new_pool_usd / new_pool_tokens

            #calculating Drop percentage
            price_impact = (1 - (crashed_price / current_price)) * 100
            #Storing Market Cap size
            cap_size = determine_cap(market_cap)

            print(Fore.MAGENTA + "--- WHALE DUMP SIMULATION (x * y = k) ---")
            #Checking weather price is too low
            if current_price < 0.01:
                print(Fore.MAGENTA + f"Current Price | {current_price:.10f} $ \n"
                                     f"Whale Tokens  | {whale_balance:,.2f} {symbol}\n"
                                     f"New Price     | {crashed_price:,.10f} $\n"
                                     f"Price Impact  | {price_impact:,.2f}% \n"
                                     f"Market Cap    | {cap_size} $\n")
            else:

                print(Fore.MAGENTA + f"Current Price | {current_price:.2f} $ \n"
                                     f"Whale Tokens  | {whale_balance:,.2f} {symbol}\n"
                                     f"New Price     | {crashed_price:,.2f} $\n"
                                     f"Price Impact  | {price_impact:,.2f}% \n"
                                     f"Market Cap    | {cap_size} $\n")


            print(Fore.MAGENTA + "-" * 107)
            print(Fore.LIGHTBLUE_EX + f"Information listed")

            #The tester

            while True:
                test_choice = input(
                    Fore.LIGHTWHITE_EX + "Would you like to test a Target Price against market benchmarks (Gold, Tesla, BTC)? (y/n): ")
                if test_choice.lower() not in ["yes", "y", "no", "n"]:
                    print(Fore.RED + "This is an invalid input, please enter either yes or no")
                else:
                    break

            if test_choice.lower() in ["yes", "y"]:
                user_target_price = float(input(Fore.LIGHTWHITE_EX + "Enter your target price in USD (e.g. 1.00): "))
                user_invest_amount = float(
                    input(Fore.LIGHTWHITE_EX + "Enter how much you wish to invest right now in USD (e.g. 100): "))

                # Calling the benchmark test function
                benchmark_test(user_target_price, user_invest_amount, price_usd, real_supply)


            while True:
                user_input2 = input("Would you like to run the Live Aave V3 LTV and Liquidation Simulator? (y/n) ")
                if user_input2.lower() in ["yes", "y"]:
                    liquidation_simulator(token_address, symbol, price_usd, crashed_price)
                    break
                elif user_input2.lower() in ["no", "n"]:
                    break

        elif choice == 2:
            print("Have a Nice Day")
            break
        else:
            print(Fore.RED + "Please Enter a Valid Input")









































