from colorama import Fore
import requests


class AaveSim:
    #LTV and Dual-Unit Liquidation
    def get_live_aave_params(self, token_address, symbol):
        #check that token_address is a valid string before we try to use it
        if not isinstance(token_address, str):
            print(Fore.RED + f"Invalid token address type. Expected a string, got {type(token_address).__name__}.")
            return 75.0, 80.0, 5.0, False

        #check it starts with 0x and is 42 chars long
        if not token_address.startswith("0x") or len(token_address) != 42:
            print(Fore.RED + f"Invalid token address format: {token_address}. Must be a 42-char 0x address.")
            return 75.0, 80.0, 5.0, False

        #check the 40 chars after 0x are valid hex characters
        hex_part = token_address[2:]
        for char in hex_part:
            if char not in "0123456789abcdefABCDEF":
                print(Fore.RED + f"Invalid hex characters in address: {token_address}")
                return 75.0, 80.0, 5.0, False

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
                print(Fore.RED + f"Aave provider HTTP error: {aave_resp.status_code}")
                return 75.0, 80.0, 5.0, False

            #if link responds, parse the JSON result
            resp_json = aave_resp.json()
            if "result" not in resp_json:
                print(Fore.RED + f"Aave provider response missing 'result' field")
                return 75.0, 80.0, 5.0, False

            hex_result = resp_json["result"]
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
                elif max_ltv == 0 and liq_threshold > 0:
                    print(Fore.YELLOW + f"----------------------------WARNING!!!-------------------------------\n"
                                        f"Aave V3 governance currently blocks new loans against asset {symbol}\n"
                                        f"Existing borrowers still face liquidation on {liq_threshold}%\n")
                    return 0, liq_threshold, liq_penalty, False
                elif max_ltv == 0 and liq_threshold == 0:

                    print(Fore.YELLOW + f"{symbol} is rejected on Aave V3 (0% Max LTV)\n"
                                        f"Application will load default parameters as a mock test\n"
                                        f"!!! -> DO NOT INTERPRET THIS AS ACTUAL INFO <- !!!\n"
                                        f"Max LTV = 75.0 | Liquidation Threshold = 80.0 | Liquidation Penalty = 5.0")
                    return 75.0, 80.0, 5.0, False
            else:
                return 75.0, 80.0, 5.0, False


        except Exception as e1:
            print(Fore.RED + f"Error fetching Aave parameters: {str(e1)}")
            return 75.0, 80.0, 5.0, False


    #Building Aave_liquidation_simulator
    def liquidation_simulator(self, token_address, symbol, price_usd, crashed_price, price_impact=0.0):
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
                    from benchmark import Benchmark
                    benchmark = Benchmark()
                    resolved_addr, _, _ = benchmark.get_dex_token_data(new_query)
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
            maximum_ltv, liquidation_threshold, liquidation_penalty, is_aave_listed = self.get_live_aave_params(token_address, symbol)
            #TBC SignGuard Safe LTV Cap calculation
            if maximum_ltv > 12.0:
                tbc_safe_ltv = maximum_ltv - 12.0
            else:
                tbc_safe_ltv = 0.0

            #if price impact is high, add extra DEX liquidity buffer
            extra_buffer = 0.0
            if price_impact > 20.0:
                extra_buffer = 5.0
                tbc_safe_ltv = tbc_safe_ltv - 5.0
                if tbc_safe_ltv < 0:
                    tbc_safe_ltv = 0.0

            print(Fore.GREEN + f"{f'----{symbol}----':^30}\n"
                  f"Live Price Today       | {price_usd:,.4f} $\n"
                  f"Aave V3 Protocol Max LTV | {maximum_ltv:.2f}%\n"
                  f"TBC SignGuard Safe LTV Cap | {tbc_safe_ltv:.2f}%\n"
                  f"Liquidation Threshold  | {liquidation_threshold:.2f}%\n"
                  f"Liquidator Bot Penalty | {liquidation_penalty:.2f}%\n")

            #if extra buffer was applied, explain why
            if extra_buffer > 0:
                print(Fore.YELLOW + f"  Note: High DEX price impact ({price_impact:.1f}%) detected. Extra 5% liquidity buffer applied to Safe LTV Cap.")

            #now we do the math, Input coin amount and retrieve it's live USD Value
            while True:
                try:
                    collateral_input = input(Fore.CYAN + f"Enter the amount of {symbol} you wish to deposit as collateral -> ").strip()
                    collateral = float(collateral_input)
                except ValueError:
                    print(Fore.RED + "Invalid input. Please enter a valid number for collateral amount.")
                    continue

                #reject zero, negative, or infinity collateral
                if collateral <= 0:
                    print(Fore.RED + "Collateral amount must be greater than 0.")
                    continue
                try:
                    import math
                    if math.isinf(collateral):
                        print(Fore.RED + "Collateral amount cannot be infinity.")
                        continue
                except Exception:
                    pass
                break
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
                    while True:
                        try:
                            loan_coins_input = input(f"Enter your {symbol} loan amount: ").strip()
                            loan_coins = float(loan_coins_input)
                        except ValueError:
                            print(Fore.RED + "Invalid input. Please enter a valid number for loan amount.")
                            continue
                        if loan_coins <= 0:
                            print(Fore.RED + "Loan amount must be greater than 0.")
                            continue
                        try:
                            import math
                            if math.isinf(loan_coins):
                                print(Fore.RED + "Loan amount cannot be infinity.")
                                continue
                        except Exception:
                            pass
                        break
                    loan_usd = loan_coins * price_usd
                    print(f"USD Equivalent of {loan_coins:,.4f} {symbol} | {loan_usd:,.4f} $")

                elif user_choice == 2:
                    # If user decides to input dollar value
                    while True:
                        try:
                            loan_usd_input = input("Enter your USD loan amount: ").strip()
                            loan_usd = float(loan_usd_input)
                        except ValueError:
                            print(Fore.RED + "Invalid input. Please enter a valid number for loan amount.")
                            continue
                        if loan_usd <= 0:
                            print(Fore.RED + "Loan amount must be greater than 0.")
                            continue
                        try:
                            import math
                            if math.isinf(loan_usd):
                                print(Fore.RED + "Loan amount cannot be infinity.")
                                continue
                        except Exception:
                            pass
                        break
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
                #Guard against division by zero in liquidation calculations
                if collateral <= 0 or collateral_usd <= 0 or liquidation_threshold <= 0:
                    print(Fore.RED + "Cannot calculate liquidation: collateral or liquidation threshold is zero or invalid.")
                    continue

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

                #Calculation D: TBC SignGuard Auto-Shield & Savings
                print(Fore.CYAN + f"\n{'----Calculation D: TBC SignGuard Auto-Shield & Savings----':^70}")

                #calculate the alert LTV threshold
                if liquidation_threshold > 10.0:
                    alert_ltv = liquidation_threshold - 10.0
                else:
                    alert_ltv = liquidation_threshold * 0.85

                #calculate the exact collateral price where the TBC Mobile Bank Push-Alert triggers
                alert_price_usd = (loan_usd / (alert_ltv / 100)) / collateral

                #calculate the 1-Tap TBC Card Top-Up needed at alert_price to drop LTV back to 65%
                target_safe_debt = (collateral * alert_price_usd) * 0.65
                topup_usd = loan_usd - target_safe_debt
                if topup_usd < 0:
                    topup_usd = 0.0

                #convert top-up to Georgian Lari for TBC Mobile Bank
                gel_rate = 2.70  # USD to GEL exchange rate
                topup_gel = topup_usd * gel_rate

                #calculate the business proof numbers
                bot_penalty_usd = loan_usd * (liquidation_penalty / 100)  # e.g. 5% Aave bot penalty
                shield_fee_low = loan_usd * 0.0025  # 0.25% TBC shield fee
                shield_fee_high = loan_usd * 0.0050  # 0.50% TBC shield fee
                client_savings = bot_penalty_usd - shield_fee_low

                print(Fore.GREEN + f"TBC Alert LTV Trigger    | {alert_ltv:.2f}%")
                print(Fore.GREEN + f"Alert Price per {symbol}      | ${alert_price_usd:,.4f}")
                print(Fore.CYAN + f"1-Tap Top-Up Needed (USD)  | ${topup_usd:,.2f}")
                print(Fore.CYAN + f"1-Tap Top-Up Needed (GEL)  | {topup_gel:,.2f} GEL")
                print(Fore.GREEN + f"Aave Bot Penalty (if liquidated) | ${bot_penalty_usd:,.2f}")
                print(Fore.GREEN + f"TBC Shield Fee (0.25%-0.50%)  | ${shield_fee_low:,.2f} - ${shield_fee_high:,.2f}")
                print(Fore.CYAN + f"Client Savings (Bot Penalty - Shield Fee) | ${client_savings:,.2f}")

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
                #Guard against division by zero in crashed LTV calculation
                if crashed_collateral_usd <= 0:
                    print(Fore.RED + "Cannot calculate crashed LTV: crashed collateral value is zero or invalid.")
                    continue
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
