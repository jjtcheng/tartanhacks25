from tutorial.mod1 import get_account, get_account_info, send_xrp
from tutorial.mod2 import create_trust_line, send_currency,get_balance, configure_account
import xrpl
from xrpl.models.transactions import NFTokenMint, Payment
from xrpl.wallet import Wallet, generate_faucet_wallet
import tkinter as tk
from blockchain import EggBatch, EggSupplyChain
from xrpl.utils import get_nftoken_id


supply_chain = EggSupplyChain()
test_wallet = generate_faucet_wallet(supply_chain.client, debug=True)
supply_chain.add_user(test_wallet, "farmer", "Farm Fresh Eggs", "37.419489; -86.302414") 
test_batch = EggBatch(
    batch_id="1234567890",
    farm_id="ABC123",
    production_date="2023-01-01",
    quantity=100,
    quality_grade="A",
    expiration_date="2023-01-31",
)
test_nft = supply_chain.create_nft(test_wallet, test_batch)
test_nft_id = get_nftoken_id(test_nft.get("meta"))
print(test_nft_id)
batch_info= supply_chain.get_batch_info(test_nft_id)
print(batch_info)


# Look up info about your account
from xrpl.models.requests.account_info import AccountInfo
acct_info = AccountInfo(
    account=test_wallet.classic_address,
    ledger_index="validated",
    strict=True,
)
response = supply_chain.client.request(acct_info)
result = response.result
print("response.status: ", response.status)
import json
print(json.dumps(response.result, indent=4, sort_keys=True))
