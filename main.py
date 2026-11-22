from colorama import Fore
import requests
import yfinance as yf
import time
#importing yfinance to gather info about gold, tsla_mcap, etc.

from benchmark import Benchmark
from aave_sim import AaveSim


#Live 12-Second Ethereum Block & Position Monitor
def run_block_monitor():
    print(Fore.CYAN + f"{'---- Live Ethereum Block & Position Monitor ----':^60}")
    print(f"{'(Read-Only / $0 Gas)':^40}")

    #ask user for sample position or use defaults
    while True:
        try:
            collateral_input = input(Fore.LIGHTWHITE_EX + "Enter sample collateral amount (default 1.0 WETH) -> ").strip()
            if not collateral_input:
                collateral = 1.0
            else:
                collateral = float(collateral_input)
            if collateral <= 0:
                print(Fore.RED + "Collateral must be greater than 0.")
                continue
            break
        except ValueError:
            print(Fore.RED + "Invalid input. Please enter a valid number.")

    while True:
        try:
            loan_input = input(Fore.LIGHTWHITE_EX + "Enter sample loan amount in USD (default 1500) -> ").strip()
            if not loan_input:
                loan_usd = 1500.0
            else:
                loan_usd = float(loan_input)
            if loan_usd <= 0:
                print(Fore.RED + "Loan amount must be greater than 0.")
                continue
            break
        except ValueError:
            print(Fore.RED + "Invalid input. Please enter a valid number.")

    #ask how many 12-second block cycles to watch
    while True:
        try:
            cycles_input = input(Fore.LIGHTWHITE_EX + "How many 12-second block cycles to watch? (default 3, or Ctrl+C to stop) -> ").strip()
            if not cycles_input:
                cycles = 3
            else:
                cycles = int(cycles_input)
            if cycles <= 0:
                print(Fore.RED + "Cycles must be greater than 0.")
                continue
            break
        except ValueError:
            print(Fore.RED + "Invalid input. Please enter a whole number.")

    #use default WETH price for simulation
    weth_price = 3000.0
    collateral_usd = collateral * weth_price
    default_ltv_threshold = 80.0

    rpc_url = "https://eth.drpc.org"

    cycle = 0
    try:
        while cycle < cycles:
            cycle += 1

            #fetch live block number
            block_payload = {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
            block_resp = requests.post(rpc_url, json=block_payload, timeout=5)
            block_number = "N/A"
            if block_resp.status_code == 200:
                block_data = block_resp.json()
                if "result" in block_data:
                    block_number = int(block_data["result"], 16)

            #fetch live gas price
            gas_payload = {"jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 2}
            gas_resp = requests.post(rpc_url, json=gas_payload, timeout=5)
            gas_gwei = "N/A"
            if gas_resp.status_code == 200:
                gas_data = gas_resp.json()
                if "result" in gas_data:
                    gas_wei = int(gas_data["result"], 16)
                    gas_gwei = gas_wei / (10 ** 9)

            #calculate simulated LTV status
            current_ltv = (loan_usd / collateral_usd) * 100
            if current_ltv >= default_ltv_threshold:
                ltv_status = Fore.RED + "TBC ALERT TRIGGERED"
            else:
                ltv_status = Fore.GREEN + "SAFE"

            #print the live block info
            print(Fore.WHITE + f"\n--- Block Cycle {cycle}/{cycles} ---")
            print(f"  Ethereum Block Number   | {block_number}")
            print(f"  Live Gas Price          | {gas_gwei:.2f} Gwei" if isinstance(gas_gwei, float) else f"  Live Gas Price          | {gas_gwei}")
            print(f"  Simulated LTV           | {current_ltv:.2f}%")
            print(f"  Position Status         | {ltv_status}")
            print(Fore.GREEN + f"  Monitoring Gas Cost     | $0.00 (Read-Only View Call)")

            #wait 12 seconds before next cycle
            if cycle < cycles:
                print(Fore.YELLOW + f"  Waiting 12 seconds for next block...")
                time.sleep(12)

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nMonitoring stopped by user.")


if __name__ == "__main__":

    #creating instances of our classes
    benchmark = Benchmark()
    aave_sim = AaveSim()



    while True:
        #wrap menu choice in a validation loop so non-integer input doesn't crash
        while True:
            try:
                choice = int(input(Fore.LIGHTWHITE_EX + "Enter what you wish to do?\n"
                                   "1. TBC Collateral Risk & Loan Blueprint (Aave V3 + SignGuard)\n"
                                   "2. Live 12-Second Ethereum Block & Position Monitor (Read-Only / $0 Gas)\n"
                                   "3. Exit\n"
                                   "----> "))
                break
            except ValueError:
                print(Fore.RED + "Invalid input. Please enter a number (1, 2, or 3).")

        if choice == 1:

            #TBC Collateral preset menu — let user pick a known asset or enter custom
            print(Fore.CYAN + "--- TBC Collateral Preset Menu ---")
            print("1. ETH (Wrapped as WETH - Phase 1 Collateral)")
            print("2. BTC (Wrapped as WBTC - Phase 1 Collateral)")
            print("3. XAUT (Tether Gold RWA - Phase 1 Collateral)")
            print("4. wstETH (Lido Liquid Staking ETH - Phase 2 Collateral)")
            print("5. Custom Token Symbol or 0x Address")

            #regulated issuer dictionary for compliance checks
            regulated_issuers = {"0xdac17f958d2ee523a2206206994597c13d831ec7": "Tether USD",
                                 "0x68749665ff8d2d112fa859aa293f07a622782f38": "Tether Gold",
                                 "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "Circle USDC"}

            #flag to skip benchmark test for presets 1-4
            skip_benchmark = False

            while True:
                try:
                    preset_choice = int(input(Fore.LIGHTWHITE_EX + "Select a collateral preset (1-5) ----> "))
                    break
                except ValueError:
                    print(Fore.RED + "Invalid input. Please enter a number (1-5).")

            if preset_choice == 1:
                token_symbol = "WETH"
                token_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
                skip_benchmark = True
            elif preset_choice == 2:
                token_symbol = "WBTC"
                token_address = "0x2260FAC5E5542a773aa44fBCfeDf7C193bc2C599"
                skip_benchmark = True
            elif preset_choice == 3:
                token_symbol = "XAUT"
                token_address = "0x68749665FF8D2d112Fa859AA293F07A622782F38"
                skip_benchmark = True
            elif preset_choice == 4:
                token_symbol = "wstETH"
                token_address = "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0"
                skip_benchmark = True
            elif preset_choice == 5:
                token_symbol = input("Enter token symbol (e.g. PEPE, UNI) or 0x address: ")
                #passing the symbol to function get_dex_token_data
                token_address, dex_name, live_pool_tokens = benchmark.get_dex_token_data(token_symbol)
                #Checking if token_address is available, if not "continue" to restart the loop
                if not token_address:
                    continue
            else:
                print(Fore.RED + "Invalid preset choice. Restarting.")
                continue

            #if preset 1-4, we still need to get dex data for pool tokens
            if preset_choice in [1, 2, 3, 4]:
                _, dex_name, live_pool_tokens = benchmark.get_dex_token_data(token_address)

            print("Searching Token Info")
            #this is the token Address


            url = f"https://api.ethplorer.io/getTokenInfo/{token_address}/?apiKey=freekey"


            try:
                response = requests.get(url)
                if response.status_code != 200:
                    print(Fore.RED + f"url threw Error | Code: {response.status_code}")
                    continue

                data = response.json()
                if "error" in data:
                    print(Fore.RED + "Failed to Retrieve Data")
                    continue

                #Extract data from data = response.json()
                name = data["name"]
                symbol = data["symbol"]

                # verify essential fields exist before extracting
                if "totalSupply" not in data:
                    print(Fore.RED + f"Missing 'totalSupply' in response for {token_address} — skipping.")
                    continue
                if "decimals" not in data:
                    print(Fore.RED + f"Missing 'decimals' in response for {token_address} — skipping.")
                    continue
                if not isinstance(data.get("price"), dict):
                    print(Fore.RED + f"No tracked market price for {token_address} (Ethplorer returned no price data) — skipping.")
                    continue

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
                        #check if this token is a regulated institutional issuer
                        if token_address.lower() in regulated_issuers:
                            issuer_name = regulated_issuers[token_address.lower()]
                            print(Fore.CYAN + f"REGULATED COMPLIANCE CONTROL ({issuer_name}): Authorized Admin/Freeze Function Verified (Institutional Safe)")
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
                    #wrap holders count in validation loop
                    while True:
                        try:
                            n = int(input(Fore.LIGHTWHITE_EX + "Enter the amount of Top holders you wish to list -> "))
                        except ValueError:
                            print(Fore.RED + "Invalid input. Please enter a whole number.")
                            continue
                        if n <= 0:
                            print(Fore.RED + "Holders count must be greater than 0.")
                            continue
                        if n > 100:
                            print(Fore.RED + "Holders count cannot exceed 100.")
                            continue
                        break
                else:
                    n = 5

                #Hunting for whales
                whale_url = f"https://api.ethplorer.io/getTopTokenHolders/{token_address}?apiKey=freekey&limit={n}"
                response = requests.get(whale_url)

                if response.status_code != 200:
                    print(Fore.RED + f"url threw Error | Code: {response.status_code}")
                    continue

                #wrap whale JSON parsing in try/except for safety
                try:
                    whale_data = response.json()
                except Exception:
                    print(Fore.RED + "Failed to parse whale holders JSON response.")
                    continue

                if "holders" not in whale_data:
                    print(Fore.RED + "No holders data in API response.")
                    continue

                holders_list = whale_data["holders"]
                if len(holders_list) == 0:
                    print(Fore.YELLOW + "No holders returned by API. Skipping whale dump.")
                    whale_balance = 0
                    continue
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
                        print(Fore.BLUE + f"Address: {holder_address:<10} | Share: {share:.2f}% | Amount: {holder_dollar_value:,.2f} $ | This is a burn Address")
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
            #only access holders_list[0] if we have holders data
            if len(holders_list) > 0:
                whale_balance = real_supply * (float(holders_list[0]["share"]) / 100)
            else:
                whale_balance = 0

            #The whale adds their tokens to the pool
            new_pool_tokens = pool_tokens + whale_balance
            #now calculating the new USD reserve to keep K constant

            new_pool_usd = k / new_pool_tokens

            #calculate the crashed price
            crashed_price = new_pool_usd / new_pool_tokens

            #calculating Drop percentage
            price_impact = (1 - (crashed_price / current_price)) * 100
            #Storing Market Cap size
            cap_size = benchmark.determine_cap(market_cap)

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
                                     f"New Price     | {crashed_price:.2f} $\n"
                                     f"Price Impact  | {price_impact:,.2f}% \n"
                                     f"Market Cap    | {cap_size} $\n")


            print(Fore.MAGENTA + "-" * 107)
            print(Fore.LIGHTBLUE_EX + f"Information listed")

            #The tester — skip automatically for presets 1-4
            if skip_benchmark:
                test_choice = "no"
            else:
                while True:
                    test_choice = input(
                        Fore.LIGHTWHITE_EX + "Would you like to test a Target Price against market benchmarks (Gold, Tesla, BTC)? (y/n): ")
                    if test_choice.lower() not in ["yes", "y", "no", "n"]:
                        print(Fore.RED + "This is an invalid input, please enter either yes or no")
                    else:
                        break

            if test_choice.lower() in ["yes", "y"]:
                #wrap target price in validation loop
                while True:
                    try:
                        user_target_price = float(input(Fore.LIGHTWHITE_EX + "Enter your target price in USD (e.g. 1.00): "))
                    except ValueError:
                        print(Fore.RED + "Invalid input. Please enter a valid number.")
                        continue
                    if user_target_price <= 0:
                        print(Fore.RED + "Target price must be greater than 0.")
                        continue
                    break

                #wrap invest amount in validation loop
                while True:
                    try:
                        user_invest_amount = float(
                            input(Fore.LIGHTWHITE_EX + "Enter how much you wish to invest right now in USD (e.g. 100): "))
                    except ValueError:
                        print(Fore.RED + "Invalid input. Please enter a valid number.")
                        continue
                    if user_invest_amount <= 0:
                        print(Fore.RED + "Invest amount must be greater than 0.")
                        continue
                    break

                # Calling the benchmark test function
                benchmark.benchmark_test(user_target_price, user_invest_amount, price_usd, real_supply)


            while True:
                user_input2 = input("Would you like to run the Live Aave V3 LTV and Liquidation Simulator? (y/n) ")
                if user_input2.lower() in ["yes", "y"]:
                    #pass price_impact from whale dump simulation to aave simulator
                    aave_sim.liquidation_simulator(token_address, symbol, price_usd, crashed_price, price_impact)
                    break
                elif user_input2.lower() in ["no", "n"]:
                    break

        elif choice == 2:
            #Live 12-Second Ethereum Block & Position Monitor
            run_block_monitor()
        elif choice == 3:
            print("Have a Nice Day")
            break
        else:
            print(Fore.RED + "Please Enter a Valid Input")
