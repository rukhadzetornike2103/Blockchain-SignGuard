import colorama
from colorama import Fore
import requests



if __name__ == "__main__":




    while True:
        choice= int(input(Fore.WHITE + "Enter what you wish to do?\n"
                          "1. Scan Address\n"
                          "2. Exit\n"
                          "-->"))
        if choice == 1:

            token_address = input("Enter your token address: ")
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

                for risk in contract_risk:
                    if not contract_risk:
                        print(Fore.GREEN + "No Risks Found!")

                    if not risk:
                        print(Fore.GREEN + "No Risks Found!")
                    else:
                        print(Fore.RED + risk)


                user_input1 = input("Would you like to enter a specific number of top holders you wish to list? ")
                if user_input1.lower() == "yes" or user_input1.lower() == "y":
                    n = int(input("Enter the amount of Top holders you wish to list -> "))
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
                    address_d_amount = real_supply * (share / 100)
                    total_amt += (address_d_amount * price_usd)
                    if bytecode == "0x" or bytecode.startswith("0xef01"):
                        if share >= 50.0:
                            print(Fore.RED + f"Address: {holder_address:<10} | Share: {share:.2f}% | Amount: {address_d_amount:,.2f} $ \n"
                                             f"Can Crash The Token")
                        else:
                            print(Fore.YELLOW + f"Address: {holder_address:<10} | Share: {share:.2f}% | Amount: {address_d_amount:,.2f} $  \n"
                                                f"EOA Address, share is safe")
                    else:
                        print(Fore.GREEN + f"Address: {holder_address:<10} | Share: {share:.2f}% | Amount: {address_d_amount:,.2f} $ ")

                    total_share += share
                print("-" * 107)
                print(f"Top {n} Addresses hold {total_share:.2f} % | Total Dollar Amount: {total_amt:,.2f} $ | Real Supply: {real_supply:,.2f} $")



            except requests.exceptions.RequestException as e:
                print(Fore.RED + str(e))



            #Creating a mock AMM, assuming 5% of total token supply is sitting on Uniswap DEX pool
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









































