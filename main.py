import colorama
from colorama import Fore
import requests

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
                    if pair.get("chainId") == "ethereum" and "liquidity" in pair and pair["baseToken"]["symbol"].lower() == user_query.lower():
                        token_addrs = pair["baseToken"]["address"]
                        dex_name = pair["dexId"]
                        pool_token_reserve = float(pair["liquidity"]["base"])
                        print(Fore.GREEN + f"DEX POOL Was Found | {dex_name}")
                        #returning gathered values
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

                    if bytecode == "0x" or bytecode.startswith("0xef01"):
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

            print(Fore.MAGENTA + "--- WHALE DUMP SIMULATION (x * y = k) ---")
            #Checking weather price is too low
            if current_price < 0.01:
                print(Fore.MAGENTA + f"Current Price | {current_price:.10f} $ \n"
                                     f"Whale Tokens  | {whale_balance:,.2f} {symbol}\n"
                                     f"New Price     | {crashed_price:,.10f} $\n"
                                     f"Price Impact  | {price_impact:,.2f}% \n")
            else:

                print(Fore.MAGENTA + f"Current Price | {current_price:.2f} $ \n"
                                     f"Whale Tokens  | {whale_balance:,.2f} {symbol}\n"
                                     f"New Price     | {crashed_price:,.2f} $\n"
                                     f"Price Impact  | {price_impact:,.2f}% \n")
            print("-" * 107)
            print(Fore.LIGHTBLUE_EX + f"Information listed")
        elif choice == 2:
            print("Have a Nice Day")
            break
        else:
            print(Fore.RED + "Please Enter a Valid Input")









































