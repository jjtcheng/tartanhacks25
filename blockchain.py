from dataclasses import dataclass
from datetime import datetime
import json
from typing import List, Dict
import xrpl
from xrpl.models.transactions import NFTokenMint, Payment
from xrpl.models.requests import from_dict, AccountTx
from xrpl.wallet import Wallet, generate_faucet_wallet
import tkinter as tk
from tutorial.mod1 import get_account, get_account_info, send_xrp
from tutorial.mod2 import create_trust_line, send_currency,get_balance, configure_account
from tutorial.mod3 import mint_token,get_tokens, burn_token
from tutorial.mod4 import create_buy_offer, accept_buy_offer, get_offers, create_sell_offer, accept_sell_offer, cancel_offer
from tutorial.mod5 import broker_sale
from tutorial.mod10 import send_check, cash_check, cancel_check, get_checks
import pandas as pd
import requests
from xrpl.utils import get_nftoken_id, hex_to_str



@dataclass
class EggBatch:
    batch_id: str
    farm_id: str
    production_date: str
    expiration_date: str
    quantity: int
    quality_grade: str
@dataclass
class TransportEvent:
    transport_id: str
    batch_id: str
    start_location: str
    end_location: str
    start_time: str
    end_time: str
    start_eggs: int
    end_eggs: int


@dataclass
class SaleEvent:
    sale_id: str
    batch_id: str
    price: float
    quantity: int
    start_eggs: int
    start_location: str
    end_location: str
    seller: str
    buyer: str

@dataclass
class CheckEvent:
    check_id: str
    eggs: int
    time: str
    checker: str

@dataclass
class UserType:
    FARMER = 1
    DISTRIBUTOR = 2
    RETAILER = 3
class EggSupplyChain:
    def __init__(self):
        self.users = pd.read_csv("users.csv") # !!! TODO: need their WALLETS
        wallets = self.users["wallet"].tolist() 
        self.trades = pd.read_csv("transactions.csv")
        for i in range(len(self.trades)):
            if self.trades["from"][i] not in self.users["wallet"]:
                return f"Unauthorized user {self.trades["from"][i]} made trade"
            if self.trades["to"][i] not in self.users["wallet"]:
                return f"Unauthorized user {self.trades["to"][i]} made trade"
        self.client = xrpl.clients.JsonRpcClient("https://s.altnet.rippletest.net:51234")
    def add_user(self, user: Wallet, type: str, name: str, location: str) -> None:
        """Add a user to the supply chain.
        
        Args:
            user (Wallet): User's wallet containing their address
            type (str): Type of user in the supply chain
            name (str): Name of the user
            location (str): Location of the user
        """
        user_data = pd.DataFrame(
            [[user.classic_address, type, name, location]], 
            columns=self.users.columns
        )
        self.users = pd.concat([self.users, user_data], ignore_index=True)
        self.users.to_csv("users.csv", index=False)
    def remove_user(self, user: Wallet):
        """Remove a user from the supply chain"""
        self.users = self.users[self.users["wallet"] != user.classic_address]
        self.users.to_csv("users.csv")
    def get_users(self) -> List[Wallet]:
        """Retrieve all users in the supply chain"""
        return self.users
    def create_metadata_uri(self, batch: EggBatch) -> str:
        """Convert batch data to URI format and upload to IPFS"""
    
        metadata = {
            "batch_id": batch.batch_id,
            "farm_id": batch.farm_id,
            "production_date": batch.production_date,
            "quantity": batch.quantity,
            "quality_grade": batch.quality_grade,
        }
        metadata_json = json.dumps(metadata)
        
        try:
            # Connect to local IPFS API
            response = requests.post(
                'http://127.0.0.1:5001/api/v0/add',
                files={'file': metadata_json}
            )
            if response.status_code != 200:
                raise RuntimeError(f"IPFS API error: {response.text}")
                
            result = response.json()
            return f"ipfs://{result['Hash']}"
        except Exception as e: raise RuntimeError("Error uploading metadata to IPFS") from e
    
    def create_nft(self,wallet: Wallet, batch: EggBatch) -> dict:
        """Mint an NFT representing an egg batch"""
        user_record = self.users[self.users["wallet"] == wallet.classic_address]
        if user_record.empty or user_record.iloc[0]["type"] != UserType.FARMER:
            raise PermissionError("Only farmers can mint NFTs")
        # Convert batch data to URI-compatible format
        batch_uri = self.create_metadata_uri(batch).encode("utf-8").hex()
        
        # Create NFT with batch data
        mint_tx = NFTokenMint(
            account=wallet.classic_address,
            uri=batch_uri,
            flags=8,  # transferable
            transfer_fee=0,
            nftoken_taxon=1
        )
        
        # Sign and submit transaction
        response = xrpl.transaction.submit_and_wait(mint_tx, self.client, wallet)
        
        return response.result
    
    # def record_transport(self, wallet: Wallet, transport: TransportEvent, token_id) -> dict:
    #     """Record a transport event as a payment transaction with memo"""
    #     # Create memo data
        
    #     memo_data = {
    #         "type": "transport / self_sale",
    #         "transport_id": transport.transport_id,
    #         "batch_id": transport.batch_id,
    #         "start_location": transport.start_location,
    #         "end_location": transport.end_location,
    #         "start_time": transport.start_time,
    #         "end_time": transport.end_time,
    #     }
    #     sell_offer = xrpl.models.transactions.NFTokenCreateOffer(
    #         account=wallet.classic_address,
    #         nftoken_id=token_id,
    #         amount=0,
    #         flags=xrpl.models.transactions.NFTokenCreateOfferFlag.TF_SELL_NFTOKEN,
    #         destination=wallet.classic_address,  # Sell to self
    #         memos=[{"Memo": {"MemoData": json.dumps(memo_data)}}]
    #     ) 
    #     # Create payment transaction with memo
    #     payment = Payment(
    #         account=wallet.classic_address,
    #         destination=wallet.classic_address,
    #         amount="1",  # Minimal amount
    #         memos=[{"Memo": {"MemoData": json.dumps(memo_data)}}]
    #     )
        
    #     # Submit sell offer
    #     offer_response = xrpl.transaction.submit_and_wait(sell_offer, self.client, wallet)

    #     # Accept the offer
    #     accept_tx = xrpl.models.transactions.NFTokenAcceptOffer(
    #         account=wallet.classic_address,
    #         nftoken_sell_offer=offer_response.result.get("nft_offer_index")
    #     )
    
    #     accept_response = xrpl.transaction.submit_and_wait(accept_tx, self.client, wallet)

    #     return {
    #         "transport_id": transport.transport_id,
    #         "sell_tx_hash": offer_response.result.get("hash"),
    #         "buy_tx_hash": accept_response.result.get("hash"),
    #         "nft_id": token_id,
    #         "price_xrp": 0,
    #         "status": accept_response.status
    #     }
    def record_sale(self, wallet: Wallet, sale: SaleEvent, token_id) -> dict:
        """Record a sale event as a payment transaction with memo"""
        # Create memo data
        memo_data = {
            "type": "sale",
            "sale_id": sale.sale_id,
            "batch_id": sale.batch_id,
            "price": sale.price,
            "quantity": sale.quantity,
            "start_eggs": sale.start_eggs,
            "start_location": sale.start_location,
            "end_location": sale.end_location,
        }
        
        # Create payment transaction with memo
        payment = Payment(
            account=wallet.classic_address,
            destination=wallet.classic_address,
            amount=str(int(sale.price * 1000000)),  # Convert price to drops
            memos=[{"Memo": {"MemoData": json.dumps(memo_data)}}]
        )
        
        # Submit payment transaction
        response = xrpl.transaction.submit_and_wait(payment, self.client, wallet)
        
        return {
            "sale_id": sale.sale_id,
            "tx_hash": response.result.get("hash"),
            "nft_id": token_id,
            "price_xrp": sale.price,
            "status": response.status
        }

    # def record_check(self, wallet: Wallet, check: CheckEvent) -> dict:
    #     """Record a check event as a payment transaction with memo"""
    #     # Create memo data
    #     memo_data = {
    #         "type": "check",
    #         "check_id": check.check_id,
    #         "eggs": check.eggs,
    #         "time": check.time,
    #     }
        
    #     # Create payment transaction with memo
    #     payment = Payment(
    #         account=wallet.classic_address,
    #         destination=wallet.classic_address,
    #         amount="1",  # Minimal amount
    #         memos=[{"Memo": {"MemoData": json.dumps(memo_data)}}]
    #     )
        
    #     # Submit payment transaction
    #     response = xrpl.transaction.submit_and_wait(payment, self.client, wallet)
        
    #     return {
    #         "check_id": check.check_id,
    #         "tx_hash": response.result.get("hash"),
    #         "status": response.status
    #     }

    
    def get_metadata_from_transaction(self, transaction):
        """Retrieve metadata from transaction"""
        uri = transaction.get("tx_json").get("URI")
        return json.loads(hex_to_str(uri))

    def make_sell_offer(self, wallet: Wallet, token_id: str, price: float) -> dict:
        """Create a sell offer for an NFT"""
        sell_offer = xrpl.models.transactions.NFTokenCreateOffer(
            account=wallet.classic_address,
            nftoken_id=token_id,
            amount=price,
            flags=xrpl.models.transactions.NFTokenCreateOfferFlag.TF_SELL_NFTOKEN
        )
        
        response = xrpl.transaction.submit_and_wait(sell_offer, self.client, wallet)
        
        return response.result
    def make_buy_offer(self, wallet: Wallet, token_id: str, price: float) -> dict:
        """Create a buy offer for an NFT"""
        buy_offer = xrpl.models.transactions.NFTokenCreateOffer(
            account=wallet.classic_address,
            nftoken_id=token_id,
            amount=price,
            flags=xrpl.models.transactions.NFTokenCreateOfferFlag.TF_BUY_NFTOKEN
        )
        
        response = xrpl.transaction.submit_and_wait(buy_offer, self.client, wallet)
        
        return response.result

    def sell_nft(self, wallet: Wallet, buy_offer_index: int,buyer:Wallet) -> dict:
        """Sell an NFT with a buy offer"""
        sell_tx = xrpl.models.transactions.NFTokenAcceptOffer(
            account=wallet.classic_address,
            nftoken_buy_offer=buy_offer_index
        )
        
        response = xrpl.transaction.submit_and_wait(sell_tx, self.client, wallet)
        
        return response.result


    def get_account_transactions(self, wallet_address: str) -> list:
        """Retrieve NFTs via standard account_nfts method"""

        acct_info = AccountTx(
            account=wallet_address,
            ledger_index_min=-1,
            ledger_index_max=-1,
            limit=400,
        )

        response = self.client.request(acct_info)
        result = response.result
        transactions = result['transactions'][:-1] # The last transaction in the list is not relevant
        return transactions
    
    def get_all_account_transactions(self):
        """Retrieve NFTs via standard account_nfts method"""
        all_transactions = []
        for i, row in self.users:
            all_transactions.extend(self.get_account_transactions(self.users.classirow['wallet']return all_transactions))
        # Query for NFT creation and all transactions




