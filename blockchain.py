from dataclasses import dataclass
from datetime import datetime
import json
from typing import List, Dict
import xrpl
from xrpl.models.transactions import NFTokenMint, Payment
from xrpl.models.requests import AccountTx
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet, generate_faucet_wallet
import pandas as pd
from xrpl.utils import get_nftoken_id, hex_to_str

@dataclass
class EggBatch:
    batch_id: str
    quantity: int
    production_date: str
    quality_grade: str

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
class UserType:
    FARMER = 1
    DISTRIBUTOR = 2
    RETAILER = 3

class EggSupplyChain:
    def __init__(self):
        self.users = pd.read_csv("users.csv") # !!! TODO: need their WALLETS
        # self.users = self.users.iloc[0:0]
        # self.users.to_csv("users.csv", index=False)
        self.trades = pd.read_csv("transactions.csv")
        # self.trades = self.trades.iloc[0:0]
        # self.trades.to_csv("transactions.csv", index=False)
        for i in range(len(self.trades)):
            if self.trades["from"][i] not in self.users["wallet"]:
                return f"Unauthorized user {self.trades["from"][i]} made trade"
            if self.trades["to"][i] not in self.users["wallet"]:
                return f"Unauthorized user {self.trades["to"][i]} made trade"
        self.client = xrpl.clients.JsonRpcClient("https://s.altnet.rippletest.net:51234")

        # HACK
        self.egg_batches = json.load(open("egg_batches.json"))

        try:
            with open("address_to_wallet.json", "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = {}
        self.address_to_wallet = {}
        for addr, creds in data.items():
            self.address_to_wallet[addr] = Wallet(
                seed=creds["seed"],
                public_key=creds["public_key"],
                private_key=creds["private_key"],
            )
        # self.address_to_wallet = {} # wallet.classic_address : wallet

    def new_user (self, type: int, name: str, longitude: str, latitude: str):
        """Add a user to the supply chain.
        
        Args:
            type (str): Type of user in the supply chain
            name (str): Name of the user
            location (str): Location of the user
        """
        user = generate_faucet_wallet(self.client, debug=True)
        return (user, self.add_user(user, type, name, longitude, latitude))
    def add_user(self, user: Wallet, type: int, name: str, longitude: str, latitude: str):
        user_data = pd.DataFrame(
            [[user.classic_address, type, name, longitude, latitude]], 
            columns=self.users.columns
        )
        self.users = pd.concat([self.users, user_data], ignore_index=True)
        self.users.to_csv("users.csv", index=False)

        self.address_to_wallet[user.classic_address] = user
        json.dump(
            {
                addr: {
                    "seed": wallet.seed,
                    "public_key": wallet.public_key,
                    "private_key": wallet.private_key,
                }
                for addr, wallet in self.address_to_wallet.items()
            },
            open("address_to_wallet.json", "w"),
        )

        return user.classic_address
        
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
            "production_date": batch.production_date,
            "quantity": batch.quantity,
            "quality_grade": batch.quality_grade,
        }
        metadata_json = json.dumps(metadata)
        return metadata_json


    def create_and_sell_nft(self, wallet, batch:EggBatch) -> dict:
        """Mint an NFT representing an egg batch"""
        # user_record = self.users[self.users["wallet"] == wallet]
        # if user_record.empty or user_record.iloc[0]["type"] != UserType.FARMER:
        #     raise PermissionError("Only farmers can mint NFTs")
        # Convert batch data to URI-compatible format
        batch_uri = self.create_metadata_uri(batch).encode("utf-8").hex()
        true_wallet = self.address_to_wallet[wallet]
        # Create NFT with batch data
        mint_tx = NFTokenMint(
            account=wallet,
            uri=batch_uri,
            flags=8,  # transferable
            transfer_fee=0,
            nftoken_taxon=1
        )
        
        # Sign and submit transaction
        response = xrpl.transaction.submit_and_wait(mint_tx, self.client,true_wallet)
        result = response.result
        nftoken_id = get_nftoken_id(result.get("meta"))
        self.egg_batches[nftoken_id] = {
            "batch_id": batch.batch_id,
            "production_date": batch.production_date,
            "quantity": batch.quantity,
            "quality_grade": batch.quality_grade,
            "owner": wallet,
            "sell_offer_id": None, 
            "transports": []
        }
        json.dump(self.egg_batches, open("egg_batches.json", "w"))

        # Now sell it
        sell_offer_response = self.make_sell_offer(wallet, nftoken_id, 0)
        sell_offer_id = sell_offer_response['meta']['offer_id']
        self.egg_batches[nftoken_id]["sell_offer_id"] = sell_offer_id
        json.dump(self.egg_batches, open("egg_batches.json", "w"))
        return (nftoken_id, sell_offer_response)



    
    # def create_nft(self, wallet: Wallet, batch: EggBatch) -> dict:
    #     """Mint an NFT representing an egg batch"""
    #     user_record = self.users[self.users["wallet"] == wallet.classic_address]
    #     if user_record.empty or user_record.iloc[0]["type"] != UserType.FARMER:
    #         raise PermissionError("Only farmers can mint NFTs")
    #     # Convert batch data to URI-compatible format
    #     batch_uri = self.create_metadata_uri(batch).encode("utf-8").hex()
        
    #     # Create NFT with batch data
    #     mint_tx = NFTokenMint(
    #         account=wallet.classic_address,
    #         uri=batch_uri,
    #         flags=8,  # transferable
    #         transfer_fee=0,
    #         nftoken_taxon=1
    #     )
        
    #     # Sign and submit transaction
    #     response = xrpl.transaction.submit_and_wait(mint_tx, self.client, wallet)
    #     sell_offer = self.make_sell_offer(wallet, nftoken_id, 0)
    #     ind = sell_offer['meta']['offer_id']
        
    #     # HACK Add to egg batch store
    #     result = response.result
    #     nftoken_id = get_nftoken_id(result.get("meta"))
    #     self.egg_batches[nftoken_id] = {
    #         "batch_id": batch.batch_id,
    #         "production_date": batch.production_date,
    #         "quantity": batch.quantity,
    #         "quality_grade": batch.qusality_grade,
    #         # "owner" : wallet.classic_address,
    #         # "sell_offer_index" : ind,
    #         "transports": []
    #     }
        
    #     return result
    
    def make_sell_offer(self, wallet, token_id: str, price: int) -> dict:
        """Create a sell offer for an NFT"""
        sell_offer = xrpl.models.transactions.NFTokenCreateOffer(
            account=wallet,
            nftoken_id=token_id,
            amount=str(price),
            flags=xrpl.models.transactions.NFTokenCreateOfferFlag.TF_SELL_NFTOKEN
        )
        true_wallet = self.address_to_wallet[wallet]
        response = xrpl.transaction.submit_and_wait(sell_offer, self.client, true_wallet)
        
        return response.result
    
    def accept_sell_offer(self, buyer_wallet, seller_wallet, number:int, sell_offer_index: int, price: int, batch_id: str) -> dict:
        """Accept an existing sell offer"""

        buy_offfer =  xrpl.models.transactions.NFTokenCreateOffer(
            account=buyer_wallet,
            nftoken_id=batch_id,
            amount=str(price),
            owner = seller_wallet.classic_address,
            flags=0
        )
        true_buyer_wallet = self.address_to_wallet[buyer_wallet]    
        response = xrpl.transaction.submit_and_wait(buy_offfer, self.client, true_buyer_wallet)
        buy_offer_index = response.result.get("offer_index")
        accept_offer_tx=xrpl.models.transactions.NFTokenAcceptOffer(
            account=buyer_wallet,
            nftoken_sell_offer=sell_offer_index,
            nftoken_buy_offer=buy_offer_index,
        )
        transaction = pd.DataFrame([[seller_wallet, buyer_wallet, price]], columns=self.trades.columns)
        self.trades = pd.concat([self.trades, transaction], ignore_index=True)
        self.trades.to_csv("transactions.csv", index=False)
        sell = self.make_sell_offer(buyer_wallet, batch_id, 0)
        ind = sell['meta']['offer_id']
        
        self.egg_batches[batch_id]["owner"]= buyer_wallet
        self.egg_batches[batch_id]["sell_offer_index"]= ind
        json.dump(self.egg_batches, open("egg_batches.json", "w"))
        self.users.loc[self.users["wallet"] == seller_wallet, "token"] = self.users.loc[self.users["wallet"] == seller_wallet, "token"].values[0].replace(batch_id, "")
        self.users.loc[self.users["wallet"] == buyer_wallet, "token"] = self.users.loc[self.users["wallet"] == buyer_wallet, "token"].values[0] + ";" + batch_id
        self.users.to_csv("users.csv", index=False)


        try:
            response=xrpl.transaction.submit_and_wait(accept_offer_tx,self.client,true_buyer_wallet)
            result = response.result

            # HACK Add transaction info
            # (seller info, buyer info, timestamp)
            self.egg_batches[batch_id]["transports"].append((seller_wallet, buyer_wallet, result['close_time_iso']))
        
            return result
        except xrpl.transaction.XRPLReliableSubmissionException as e:
            reply=f"Submit failed: {e}"
            return reply

    
    def make_buy_offer(self, wallet: Wallet, token_id: str, price: int) -> dict:
        """Create a buy offer for an NFT"""
        buy_offer = xrpl.models.transactions.NFTokenCreateOffer(
            account=wallet.classic_address,
            nftoken_id=token_id,
            amount=str(price),
            flags=0
        )
        
        response = xrpl.transaction.submit_and_wait(buy_offer, self.client, wallet)
        
        return response.result
    def accept_buy_offer(self, buyer_wallet: Wallet, seller_wallet:Wallet, number:int, buy_offer_index: int, price: int, batch_id: str) -> dict:
        """Accept an existing buy offer"""
        sell_offfer =  xrpl.models.transactions.NFTokenCreateOffer(
            account=seller_wallet.classic_address,
            nftoken_id=batch_id,
            amount=str(price),
            owner = buyer_wallet.classic_address,
            flags=0
        )
        response = xrpl.transaction.submit_and_wait(sell_offfer, self.client, seller_wallet)
        sell_offer_index = response.result.get("offer_index")
        accept_offer_tx=xrpl.models.transactions.NFTokenAcceptOffer(
            account=seller_wallet.classic_address,
            nftoken_sell_offer=sell_offer_index,
            nftoken_buy_offer=buy_offer_index,
        )
        transaction = pd.DataFrame([[buyer_wallet.classic_address, seller_wallet.classic_address, price]], columns=self.trades.columns)
        self.trades = pd.concat([self.trades, transaction], ignore_index=True)
        self.trades.to_csv("transactions.csv", index=False)
        self.make_sell_offer(buyer_wallet, batch_id, 0)
        try:
            response=xrpl.transaction.submit_and_wait(accept_offer_tx,self.client,seller_wallet)
            result = response.result
            return result
        except xrpl.transaction.XRPLReliableSubmissionException as e:
            reply=f"Submit failed: {e}"
            return reply
        
    
    def get_metadata_from_transaction(self, transaction):
        """Retrieve metadata from transaction"""
        uri = transaction.get("tx_json").get("URI")
        return json.loads(hex_to_str(uri))

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
        for _, row in self.users.iterrows():
            all_transactions.extend(self.get_account_transactions(row['wallet']))
        all_transactions_df = pd.DataFrame(all_transactions)
        all_transactions_df.columns = ["tx_hash", "ledger_index", "tx_type", "tx_result", "tx_date", "tx_fee", "tx_account", "tx_destination", "tx_amount", "tx_uri"]
        all_transactions_df.to_csv("all_transactions.csv", index=False)
        return all_transactions
        # Query for NFT creation and all transactions




