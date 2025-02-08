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



def construct_refererence_dictionary(dataframe, passwords):
    index = 0
    example_dict = {}
    for key in passwords:
        password = passwords[key]
        example_dict[(key, password)] = dataframe.loc[:, 'wallet'][index]
        index += 1
    return example_dict



if 'Sell' not in st.session_state:
    st.session_state.Sell = {'seed': '', 'address': '', 'balance': ''}
if 'Buy' not in st.session_state:
    st.session_state.Buy = {'seed': '', 'address': '', 'balance': ''}

st.title("XRPL Eggs Manager")




# Update the create_account function
import streamlit as st
import pandas as pd

from xrpl.wallet import Wallet

CSV_PATH = "users.csv"

self.EggSupplyChain()
def create_account():
    """Handle account creation with credentials in secrets"""
    with st.form("Create Account", clear_on_submit=True):
        st.header("📍 Location Registration Portal")
        
        # User metadata inputs
        new_user = st.text_input("Username*")
        new_pass = st.text_input("Password*", type="password")
        new_name = st.text_input("Company Name")
        confirm_pass = st.text_input("Confirm Password*", type="password")
        role = st.selectbox("Role*", ["farmer", "distributor", "retailer"])
        
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

            # Generate wallet

            new_user = self.
            new_wallet = Wallet.create()
            
            # Create user entry
            new_entry = {
                'wallet': new_wallet.seed,
                'role': role,
                'name': new_name,
                'latitude': manual_lat,
                'longitude': manual_lon
            }
            
            # Save to CSV
            try:
                df = pd.read_csv("users.csv")
            except FileNotFoundError:
                df = pd.DataFrame(columns=new_entry.keys())
                
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
            df.to_csv("users.csv", index=False)
            
            # Show secret addition instructions
            st.success("Account created! Add to secrets.toml:")
            st.code(f"""
            [passwords]
            {new_user} = "{new_pass}"
            """)
            update_secrets(new_user, new_pass)
            st.balloons()
            st.session_state.logged_in = True
            st.session_state.role = role
            st.session_state.wallet = new_wallet.seed
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
                        user_data = df2[df2['wallet'] == dictionary[(username, password)]].iloc[0]
                        st.session_state.logged_in = True
                        st.session_state.role = user_data['role']
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

st.sidebar.subheader(f"Role: {st.session_state.role.capitalize()}")
st.sidebar.write(f"Wallet: {st.session_state.wallet}")



# Use the role in your main interface
# Role-specific portals after login
if st.session_state.role == 'farmer':
    st.header("🥚 Farmer Batch Management")
    
    with st.expander("🍳 Create New Batch", expanded=True):
        with st.form("Create Batch"):
            batch_id = st.text_input("Batch ID")
            quantity = st.number_input("Quantity", min_value=1, value=100)
            quality = st.number_input("Quality", min_value=1, value=15)
            
            if st.form_submit_button("Mint NFT Batch"):
                # NFT minting logic here
                #TODO: Get farm_id
                farm_id = None

                new_batch = EggBatch(
                    batch_id=batch_id,
                    farm_id=farm_id,
                    quantity=quantity,
                    production_date=date.today().strftime("%Y-%m-%d"),
                    quality=quality
                )


                st.session_state.batches.append(new_batch)
                st.success(f"Batch {batch_id} minted successfully!")

    st.subheader("📦 My Inventory")
    farmer_batches = [b for b in st.session_state.get('batches', []) 
                     if b['owner'] == st.session_state.wallet]
    
    for batch in farmer_batches:
        with st.container(border=True):
            cols = st.columns([2,1,2])
            cols[0].metric("Batch ID", batch.batch_id)
            cols[1].metric("Units", batch.quantity)
            cols[2].button("Remove Listing", key=f"del_{batch.batch_id}")

elif st.session_state.role == 'distributor':
    st.header("📦 Distributor Portal")
    
    tab1, tab2 = st.tabs(["🛒 Available Batches", "📊 Manage Inventory"])
    
    with tab1:
        st.subheader("Purchase from Farmers")
        available_batches = [b for b in st.session_state.get('batches', []) 
                            if b['owner'] != st.session_state.wallet]
        
        for batch in available_batches:
            with st.expander(f"Batch {batch.batch_id} - {batch.quantity} units"):
                cols = st.columns([3,1,2])
                cols[0].write(f"**Farm of origin:** {batch.farm_id}")
                cols[1].number_input("Purchase Qty", key=f"qty_{batch.batch_id}", 
                                   min_value=1, max_value=batch['quantity'])
                if cols[2].button("Acquire Batch", key=f"buy_{batch['id']}"):
                    #TODO: Update ownership logic

                    batch['owner'] = st.session_state.wallet
                    st.rerun()

    with tab2:
        st.subheader("Inventory Management")
        my_batches = [b for b in st.session_state.get('batches', []) 
                     if b['owner'] == st.session_state.wallet]
        
        for batch in my_batches:
            with st.container(border=True):
                new_qty = st.number_input("Update Quantity", value=batch['quantity'],
                                        key=f"update_{batch['id']}")
                new_price = st.number_input("Update Price", value=batch['price'],
                                          key=f"price_{batch['id']}")
                if st.button("Update", key=f"update_btn_{batch['id']}"):
                    batch['quantity'] = new_qty
                    batch['price'] = new_price
                    st.success("Inventory updated!")

elif st.session_state.role == 'retailer':
    st.header("🏪 Retail Marketplace")
    st.subheader("Available Distributor Stock")
    
    distributor_batches = [b for b in st.session_state.get('batches', []) 
                          if b['owner'] not in ['farmer', st.session_state.wallet]]
    
    for batch in distributor_batches:
        with st.container(border=True):
            cols = st.columns([2,1,1,2])
            cols[0].write(f"**Batch {batch['id']}**")
            cols[1].metric("Units", batch['quantity'])
            cols[2].metric("Unit Price", f"{batch['price']} XRP")
            purchase_qty = cols[3].number_input("Qty", min_value=1, 
                                               max_value=batch['quantity'],
                                               key=f"ret_{batch['id']}")
            if cols[3].button("Purchase", key=f"retbuy_{batch['id']}"):
                # Handle purchase transaction
                batch['quantity'] -= purchase_qty
                if batch['quantity'] <= 0:
                    st.session_state.batches.remove(batch)
                st.success(f"Purchased {purchase_qty} units!")

# Initialize session state variables
if 'batches' not in st.session_state:
    st.session_state.batches = []
