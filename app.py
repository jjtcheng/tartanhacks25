import streamlit as st
import xrpl
import json
from xrpl.wallet import Wallet
import hmac
import csv
import pandas as pd
import json 
import pydeck as pdk
import os
from pathlib import Path
from blockchain import *
from datetime import date
import header
import blockchain
from xrpl.utils import get_nftoken_id, hex_to_str

from download_data import read_data
from graph import analyze_source_shock, analyze_transactions, display_graph, construct_graph
import matplotlib.pyplot as plt
import numpy as np
import ast




USER_TYPE_MAP = {"Farmer": blockchain.UserType.FARMER, "Distributor": blockchain.UserType.DISTRIBUTOR, "Retailer": blockchain.UserType.RETAILER}
Reverse_type_map = {blockchain.UserType.FARMER: "Farmer", blockchain.UserType.DISTRIBUTOR: "Distributor", blockchain.UserType.RETAILER: "Retailer"}

def get_user_type(user_type_str: str) -> int:
    return USER_TYPE_MAP.get(user_type_str, None)

def get_user_type_str(user_type: int) -> str:
    return Reverse_type_map.get(user_type, None)
def update_secrets(new_user, new_pass):
    """Update secrets.toml with new credentials"""
    secrets_dir = Path(".streamlit")
    secrets_file = secrets_dir / "secrets.toml"
    
    # Create directory if needed
    secrets_dir.mkdir(exist_ok=True)
    
    # Read existing content
    try:
        with open(secrets_file, "r") as f:
            content = f.read()
    except FileNotFoundError:
        content = ""
    
    # Parse existing passwords
    passwords = {}
    in_passwords = False
    other_sections = []
    
    for line in content.splitlines():
        if line.strip().startswith("[passwords]"):
            in_passwords = True
        elif line.startswith("["):
            in_passwords = False
            other_sections.append(line)
        elif in_passwords and "=" in line:
            key, value = line.split("=", 1)
            passwords[key.strip()] = value.strip().strip('"')
    
    # Add new password
    passwords[new_user] = new_pass
    
    # Rebuild content
    new_content = "\n".join(other_sections)
    new_content += "\n\n[passwords]\n"
    new_content += "\n".join([f'{k} = "{v}"' for k, v in passwords.items()])
    
    # Write back to file
    with open(secrets_file, "w") as f:
        f.write(new_content.strip())


#log into with wallet_id and password
#No Sell Account

# Initialize session state
CSV_PATH = "users.csv"


passwords = st.secrets["passwords"]

df2 = pd.read_csv(CSV_PATH)
token_lists = []
if "token" in df2.columns:
    for col_value in df2["token"]:
        # If the cell is a string representation of a list, convert it
        if isinstance(col_value, str):
            try:
                token_list = ast.literal_eval(col_value)
            except Exception:
                token_list = []
        elif isinstance(col_value, list):
            token_list = col_value
        else:
            token_list = []
        token_lists.extend(token_list)
st.session_state.batches = token_lists
supplyChain = blockchain.EggSupplyChain()
st.session_state.FarmerSell = []
st.session_state.DistributorSell = []
st.session_state.allBlocks = []

def construct_refererence_dictionary(dataframe, passwords):

    example_dict = {}
    for index, key in enumerate(passwords):
        if index >= len(dataframe):
            break
        password = passwords[key]
        example_dict[(key, password)] = dataframe.loc[index, 'wallet']
    return example_dict



if 'Sell' not in st.session_state:
    st.session_state.Sell = {'seed': '', 'address': '', 'balance': ''}
if 'Buy' not in st.session_state:
    st.session_state.Buy = {'seed': '', 'address': '', 'balance': ''}

st.title("XRPL Eggs Manager")




# Update the create_account function


def create_account():
    """Handle account creation with credentials in secrets"""
    with st.form("Create Account", clear_on_submit=True):
        st.header("📍 Location Registration Portal")
        
        # User metadata inputs
        new_user = st.text_input("Username*")
        new_pass = st.text_input("Password*", type="password")
        new_name = st.text_input("Company Name")
        confirm_pass = st.text_input("Confirm Password*", type="password")
        role = st.selectbox("Role*", ["Farmer", "Distributor", "Retailer"])
        
        # Coordinate input section
        st.subheader("Location Details")
        
        # Manual coordinate input
        col1, col2 = st.columns(2)
        with col1:
            manual_lat = st.number_input("Latitude*", 
                                       min_value=-90.0, 
                                       max_value=90.0,
                                       format="%.6f")
        with col2:
            manual_lon = st.number_input("Longitude*", 
                                       min_value=-180.0, 
                                       max_value=180.0,
                                       format="%.6f")

        if st.form_submit_button("Complete Registration"):
            errors = []
            
            # Validation
            if not all([new_user, new_pass, confirm_pass]):
                errors.append("Missing required fields (marked with *)")
                
            if new_pass != confirm_pass:
                errors.append("Passwords do not match")
                
            if new_user in passwords:
                errors.append("Username already exists")
                
            if not (-90 <= manual_lat <= 90) or not (-180 <= manual_lon <= 180):
                errors.append("Invalid coordinates (Lat: -90 to 90, Lon: -180 to 180)")
            
            if errors:
                for error in errors:
                    st.error(error)
                return


            user_type = get_user_type(role)
            
            wallet, _ = supplyChain.new_user(user_type, new_name, manual_lon, manual_lat)
                        
            # Create user entry
            
            
            # Save to CSV
            
            
            # Show secret addition instructions
            st.success("Account created! Add to secrets.toml:")
            st.code(f"""
            [passwords]
            {new_user} = "{new_pass}"
            """)
            update_secrets(new_user, new_pass)
            st.balloons()
            st.session_state.logged_in = True
            st.session_state.role = user_type
            st.session_state.wallet = wallet.classic_address
            st.session_state.show_create_account = False
            st.rerun()






# Update your CSV structure to include:
# wallet,role,name,latitude,longitude




def check_credentials(dictionary, df2):
    """Show login form with account creation option"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.show_create_account = False

    if not st.session_state.logged_in:
        col1, col2 = st.columns([3, 2])
        with col1:
            with st.form("Login"):
                st.header("Existing Users")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    if (username in st.secrets.passwords and 
                        hmac.compare_digest(password, st.secrets.passwords[username])):
                        # Get user data from CSV
                        df2.head()
                        user_data = df2[df2['wallet'] == dictionary[(username, password)]].iloc[0]
                        st.session_state.logged_in = True
                        st.session_state.role = user_data['type']
                        st.session_state.wallet = user_data['wallet']
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
        
        with col2:
            st.header("New Users")
            if st.button("Create Account"):
                st.session_state.show_create_account = True
                st.rerun()
        
        st.stop()

dictionary = construct_refererence_dictionary(df2, passwords)

# Main app flow
if not st.session_state.get('logged_in'):
    if st.session_state.get('show_create_account'):
        create_account()  # Your existing create_account function
    else:
        check_credentials(dictionary, df2)

check_credentials(dictionary, df2)
# Then display the role and wallet in sidebar
st.sidebar.subheader(f"Role: {get_user_type_str(st.session_state.role)}")
st.sidebar.write(f"Wallet: {st.session_state.wallet}")



# Use the role in your main interface
# Role-specific portals after login
if st.session_state.role == get_user_type('Farmer'):
    st.header("🥚 Farmer Batch Management")
    
    with st.expander("🍳 Create New Batch", expanded=True):
        with st.form("Create Batch"):
            batch_id = st.text_input("Batch ID")
            quantity = st.number_input("Quantity", min_value=1, value=100)
            quality = st.text_input("Quality")
            
            if st.form_submit_button("Mint NFT Batch"):
                # NFT minting logic here

                new_batch = blockchain.EggBatch(
                    batch_id=batch_id,
                    quantity=quantity,
                    production_date=date.today().strftime("%Y-%m-%d"),
                    quality_grade=quality
                )

                (nft_token_id, sell_offer_response) = supplyChain.create_and_sell_nft(st.session_state.wallet, new_batch)
                
                st.session_state.batches.append(nft_token_id)
                st.success(f"Batch {batch_id} minted and put on sale successfully!")
                


    st.subheader("📦 My Inventory")
    for token_id in st.session_state.batches:
        batch = supplyChain.egg_batches[token_id]
        if batch['owner'] == st.session_state.wallet:

            with st.container(border=True):
                cols = st.columns([2,1,2,1,1])
                cols[0].metric("Batch ID", batch["batch_id"])
                cols[1].metric("Units", batch["quantity"])
                cols[2].metric("Quality", batch["quality_grade"])
                
                sell_key = f"sell_{token_id}_{batch['batch_id']}"
                del_key = f"del_{token_id}_{batch['batch_id']}"

                cols[3].button("Sell Batch", key=sell_key)
                cols[4].button("Remove Listing", key=del_key)

            
            

elif st.session_state.role == get_user_type('Distributor'):
    st.header("📦 Distributor Portal")
    
    tab1, tab2, tab3 = st.tabs(["🛒 Available Batches", "📊 Manage Inventory","📈 Analyze the Chain"])
    
    for nft in  st.session_state.batches:
        batch = supplyChain.egg_batches[nft]
        owner = batch['owner']
        if owner != st.session_state.wallet and df2[df2['wallet'] == owner].iloc[0]['type'] == 1:
            st.session_state.FarmerSell.append(batch)
            with st.expander(f"Batch {batch["farm_id"]} has {batch["quantity"]} eggs"):
                cols = st.columns([3,1,2])
                cols[0].write(f"**Farm of origin:** {batch["farm_id"]}")
                cols[1].number_input("Purchase Qty", key=f"qty_{batch[batch_id]}", 
                                    min_value=1, max_value=batch['quantity'])
                if cols[2].button("Acquire Batch", key=f"buy_{batch['batch_id']}"):
                    #TODO: Update ownership logic
                    supplyChain.accept_sell_offer(st.session_state.wallet,batch["owner"],batch["quantity"],batch["sell_offer_index"],batch["price"],batch["batch_id"])
                    batch['owner'] = st.session_state.wallet
                    available_batches.remove(batch)
                    st.rerun()

    with tab2:
        
        for token_id in st.session_state.batches:
            batch = supplyChain.egg_batches[token_id]
            with st.container(border=True):
                new_price = st.number_input("Update Price", value=batch['price'],
                                          key=f"price_{batch['batch_id']}")
                if st.button("Update", key=f"update_btn_{batch['batch_id']}"):
                    batch['price'] = new_price
                    st.success("Inventory updated!")
    
    with tab3:
        st.subheader("Supply Analysis")
        transactions, users = read_data("t.csv", "u.csv")
        G = construct_graph(transactions)
        fig = display_graph(G)
        node_bc = analyze_transactions(transactions)
        print(list(node_bc.items()))
        df_bc = pd.DataFrame(
            np.array(list(node_bc.items())), columns=("User", "Betweenness Centrality")
        )
        st.pyplot(fig)
        st.text("This shows the unweighted betweenness centrality of each user in our network")
        st.table(df_bc.sort_values(by="Betweenness Centrality", ascending=False))
        with st.form("Simulate supply shock", clear_on_submit=True):
            sources = users[users[:, 1] == 1, 0]
            source = st.selectbox("Source", sources)
            reduction_factor = st.number_input("Reduction Factor", min_value=0, max_value=1)
            if st.form_submit_button("Simulate"):
                stat, G_new = analyze_source_shock(G, source, sources)
                st.text(f"{source} produces {stat}% of eggs")
                fig = display_graph(G_new)
                st.pyplot(fig)
                st.caption(f"Supply graph upon a reduction of {reduction_factor} on {source}")
            
elif st.session_state.role == get_user_type('Retailer'):
    st.header("🏪 Retail Marketplace")
    st.subheader("Available Distributor Stock")
    

    for token in st.session_state.batches:
        batch = supplyChain.egg_batches[token]
        with st.container(border=True):
            cols = st.columns([2,1,1,2])
            cols[0].write(f"**Batch {batch['batch_id']}**")
            cols[1].metric("Units", batch['quantity'])
            cols[2].metric("Unit Price", f"{batch['price']} XRP")
            purchase_qty = cols[3].number_input("Qty", min_value=1, 
                                               max_value=batch['quantity'],
                                               key=f"ret_{batch['batch_id']}")
            if cols[3].button("Purchase", key=f"retbuy_{batch['batch_id']}"):
                # Handle purchase transaction
                batch['quantity'] -= purchase_qty
                if batch['quantity'] <= 0:
                    st.session_state.batches.remove(batch)
                st.success(f"Purchased {purchase_qty} units!")
