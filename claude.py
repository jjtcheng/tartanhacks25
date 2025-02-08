# Supply Chain Modules
from dataclasses import dataclass
from datetime import datetime
import json
from typing import List, Dict
import xrpl
from xrpl.models.transactions import NFTokenMint, Payment
from xrpl.wallet import Wallet
import tkinter as tk

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
class EggBatch:
    batch_id: str
    farm_id: str
    production_date: str
    quantity: int
    quality_grade: str
    Transports: List[TransportEvent]


class EggSupplyChain:
    def __init__(self):
        self.client = xrpl.clients.JsonRpcClient("https://s.altnet.rippletest.net:51234")
        
    def create_batch_nft(self, wallet: Wallet, batch: EggBatch) -> dict:
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

    def record_transport(self, wallet: Wallet, transport: TransportEvent) -> dict:
        """Record a transport event as a payment transaction with memo"""
        # Create memo data
        memo_data = {
            "type": "transport",
            "transport_id": transport.transport_id,
            "batch_id": transport.batch_id,
            "start_location": transport.start_location,
            "end_location": transport.end_location,
            "start_time": transport.start_time,
            "end_time": transport.end_time,
        }
        
        # Create payment transaction with memo
        payment = Payment(
            account=wallet.classic_address,
            destination=wallet.classic_address,
            amount="1",  # Minimal amount
            memos=[{"Memo": {"MemoData": json.dumps(memo_data)}}]
        )
        
        # Submit transaction
        response = xrpl.transaction.submit_and_wait(payment, self.client, wallet)
        
        return {
            "transport_id": transport.transport_id,
            "tx_hash": response.result.get("hash"),
            "status": response.status
        }

    def get_batch_history(self, batch_id: str) -> List[Dict]:
        """Retrieve complete history for a batch"""
        history = []
        
        # Query for NFT creation and all transactions
        # This is a simplified version - you'd need to implement proper XRPL queries
        nft_query = {
            "command": "account_nfts",
            "account": batch_id,
            "ledger_index": "validated"
        }
        
        # Get transaction history
        tx_query = {
            "command": "account_tx",
            "account": batch_id,
            "ledger_index_min": -1,
            "ledger_index_max": -1,
            "binary": False,
            "forward": False
        }
        
        # Process and return results
        return history

    def _create_metadata_uri(self, batch: EggBatch) -> str:
        """Convert batch data to URI format"""
        metadata = {
            "batch_id": batch.batch_id,
            "farm_id": batch.farm_id,
            "production_date": batch.production_date,
            "quantity": batch.quantity,
            "quality_grade": batch.quality_grade,
        }
        return f"ipfs://{json.dumps(metadata)}"  # In practice, you'd upload to IPFS

