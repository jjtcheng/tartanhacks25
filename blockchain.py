from dataclasses import dataclass
from datetime import datetime
import json
from typing import List, Dict
import xrpl
from xrpl.models.transactions import NFTokenMint, Payment
from xrpl.wallet import Wallet
import tkinter as tk
from tutorial.mod1 import get_account, get_account_info, send_xrp
from tutorial.mod2 import create_trust_line, send_currency,get_balance, configure_account
from tutorial.mod3 import mint_token,get_tokens, burn_token
from tutorial.mod4 import create_buy_offer, accept_buy_offer, get_offers, create_sell_offer, accept_sell_offer, cancel_offer
from tutorial.mod5 import broker_sale
from tutorial.mod10 import send_check, cash_check, cancel_check, get_checks
try:
    import ipfshttpclient
except ImportError:
    raise ImportError("ipfshttpclient is not installed. Please install")

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
class EggSupplyChain:
    def __init__(self):
        self.client = xrpl.clients.JsonRpcClient("https://s.altnet.rippletest.net:51234")
    def _create_metadata_uri(self, batch: EggBatch) -> str:
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
            # Connect to the local IPFS daemon. Ensure your daemon is running.
            client = ipfshttpclient.connect()
            # Upload the JSON metadata to IPFS
            res = client.add_str(metadata_json)
            # The result is the IPFS hash; return a URI-compliant string
            return f"ipfs://{res}"
        except Exception as e:
            raise RuntimeError("Error uploading metadata to IPFS") from e
    
    def create_nft(self,wallet: Wallet, batch: EggBatch) -> dict:
        """Mint an NFT representing an egg batch"""
        # Convert batch data to URI-compatible format
        batch_uri = self._create_metadata_uri(batch)
        
        # Create NFT with batch data
        mint_tx = NFTokenMint(
            account=wallet.classic_address,
            uri=batch_uri,
            flags=8,  # transferable
            transfer_fee=0,
            taxon=1,  # Use taxon 1 for egg batches
            nftoken_taxon=1
        )
        
        # Sign and submit transaction
        response = xrpl.transaction.submit_and_wait(mint_tx, self.client, wallet)
        
        return {
            "batch_id": batch.batch_id,
            "nft_id": response.result.get("nft_id"),
            "status": response.status
        }
    def record_transport(self, wallet: Wallet, transport: TransportEvent, token_id) -> dict:
        """Record a transport event as a payment transaction with memo"""
        # Create memo data
        
        memo_data = {
            "type": "transport / self_sale",
            "transport_id": transport.transport_id,
            "batch_id": transport.batch_id,
            "start_location": transport.start_location,
            "end_location": transport.end_location,
            "start_time": transport.start_time,
            "end_time": transport.end_time,
        }
        sell_offer = xrpl.models.transactions.NFTokenCreateOffer(
        account=wallet.classic_address,
        nftoken_id=token_id,
        amount=0,
        flags=xrpl.models.transactions.NFTokenCreateOfferFlag.TF_SELL_NFTOKEN,
        destination=wallet.classic_address,  # Sell to self
        memos=[{"Memo": {"MemoData": json.dumps(memo_data)}}]) 
        # Create payment transaction with memo
        payment = Payment(
            account=wallet.classic_address,
            destination=wallet.classic_address,
            amount="1",  # Minimal amount
            memos=[{"Memo": {"MemoData": json.dumps(memo_data)}}]
        )
        
        # Submit sell offer
        offer_response = xrpl.transaction.submit_and_wait(sell_offer, self.client, wallet)

        # Accept the offer
        accept_tx = xrpl.models.transactions.NFTokenAcceptOffer(
        account=wallet.classic_address,
        nftoken_sell_offer=offer_response.result.get("nft_offer_index")
    )
    
        accept_response = xrpl.transaction.submit_and_wait(accept_tx, self.client, wallet)

        return {
        "transport_id": transport.transport_id,
        "sell_tx_hash": offer_response.result.get("hash"),
        "buy_tx_hash": accept_response.result.get("hash"),
        "nft_id": token_id,
        "price_xrp": 0,
        "status": accept_response.status
        }
    def get_batch_info(self, batch_id: str) -> List[Dict]:
        """Retrieve complete history for a batch"""
        try:
            req = {
            "method": "nft_info",
            "params": [{
                "nft_id": batch_id,
                "ledger_index": "validated"
            }]
            }
            response = self.client.request(req)
            nft_details = response.result.get("nft")
            return [nft_details] if nft_details else []
        except Exception as e:
            raise RuntimeError("Error retrieving NFT information") from e
        
    
        
        # Query for NFT creation and all transactions