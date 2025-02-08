import xrpl
from xrpl.models.transactions import NFTokenMint, Payment
from xrpl.wallet import Wallet, generate_faucet_wallet
from xrpl.utils import get_nftoken_id, hex_to_str
import sys
import os
sys.path.append(os.path.abspath("."))  # Adjust this path as needed
from tutorial.mod1 import get_account, get_account_info, send_xrp
from tutorial.mod2 import create_trust_line, send_currency, get_balance, configure_account
from blockchain import EggBatch, EggSupplyChain



supply_chain = EggSupplyChain()




test_wallet = generate_faucet_wallet(supply_chain.client, debug=True)
test_wallet2 = generate_faucet_wallet(supply_chain.client, debug=True)
test_wallet3 = generate_faucet_wallet(supply_chain.client, debug=True)
# test_wallet3 = generate_faucet_wallet(supply_chain.client, debug=True)
supply_chain.add_user(test_wallet, 1, "Farm Fresh Eggs", "37.419489", "-86.302414") 
supply_chain.add_user(test_wallet2, 2, "Big Egg Sender", "87.419489", "-36.302414")
supply_chain.add_user(test_wallet2, 3, "Giant Eagle Retailer", "87.419489", "-36.302414")
# supply_chain.add_user(test_wallet3, 3, "Big Egg Receiver", "57.419489; -106.302414")




# Create an NFT egg

test_batch = EggBatch(
    batch_id="1234567890",
    production_date="2023-01-01",
    quantity=100,
    quality_grade="A",
)
test_nft = supply_chain.create_and_sell_nft(test_wallet, test_batch)
# test_nft_token_id = get_nftoken_id(test_nft.get("meta"))


print(supply_chain.egg_batches)

print(test_nft)




exit()

print("===============================")

info = supply_chain.make_sell_offer(test_wallet, test_nft_token_id, 0)
sell_offer_id =info['meta']['offer_id']
print(info)
hash = info.get("hash")
print("===============================")
print("offer_id", sell_offer_id)
print("===============================")

print(supply_chain.accept_sell_offer(test_wallet2,test_wallet,100,sell_offer_id,100,test_nft_token_id))


print("====")

print(supply_chain.egg_batches)



print("!!!!!!!!!!!!!!!!!!!!!!!!!")
info = supply_chain.make_sell_offer(test_wallet2, test_nft_token_id, 0)
sell_offer_id =info['meta']['offer_id']
print(supply_chain.accept_sell_offer(test_wallet3,test_wallet2,100,sell_offer_id,100,test_nft_token_id))


# print(supply_chain.)




# supply_chain.get_all_account_transactions()