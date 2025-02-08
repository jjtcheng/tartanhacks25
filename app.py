import streamlit as st
import xrpl
import json
from xrpl.wallet import Wallet
import hmac
import csv
import pandas as pd
import json


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






def check_credentials(example_dict, df):
    """Show login form and verify credentials"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.wallet = None

    if not st.session_state.logged_in:
        with st.form("Login"):
            st.header("XRPL Eggs Manager Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                if (username in passwords and 
                    hmac.compare_digest(password, st.secrets.passwords[username])):
                    
                    # Get role from CSV
                    
                    wallet = example_dict[(username, password)]
                    if not wallet:
                        st.error("No role assigned for this user")
                        return
                    
                    
                    role = df[df['wallet'] == wallet]['role']
                    
                    # Get wallet from CSV
                    
                    
                    # Store in session state
                    st.session_state.logged_in = True
                    
                    st.session_state.role = role
                    st.session_state.wallet = wallet
                    
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        st.stop()
dictionary = construct_refererence_dictionary(df2, passwords)
check_credentials(dictionary, df2)
# Then display the role and wallet in sidebar

st.sidebar.subheader(f"Role: {st.session_state.role.to_string(index=False).capitalize()}")
st.sidebar.write(f"Wallet: {st.session_state.wallet}")

# Use the role in your main interface
# Role-specific portals after login
if st.session_state.role.to_string(index=False) == 'farmer':
    st.header("🥚 Farmer Batch Management")
    
    with st.expander("🍳 Create New Batch", expanded=True):
        with st.form("Create Batch"):
            batch_id = st.text_input("Batch ID")
            quantity = st.number_input("Quantity", min_value=1, value=100)
            price = st.number_input("XRP per Unit", min_value=1, value=15)
            
            if st.form_submit_button("Mint NFT Batch"):
                # NFT minting logic here
                new_batch = {
                    "id": batch_id,
                    "owner": st.session_state.wallet,
                    "quantity": quantity,
                    "price": price,
                    "history": []
                }
                st.session_state.batches.append(new_batch)
                st.success(f"Batch {batch_id} minted successfully!")

    st.subheader("📦 My Inventory")
    farmer_batches = [b for b in st.session_state.get('batches', []) 
                     if b['owner'] == st.session_state.wallet]
    
    for batch in farmer_batches:
        with st.container(border=True):
            cols = st.columns([2,1,1,2])
            cols[0].metric("Batch ID", batch['id'])
            cols[1].metric("Units", batch['quantity'])
            cols[2].metric("Price", f"{batch['price']} XRP")
            cols[3].button("Remove Listing", key=f"del_{batch['id']}")

elif st.session_state.role.to_string(index=False) == 'distributor':
    st.header("📦 Distributor Portal")
    
    tab1, tab2 = st.tabs(["🛒 Available Batches", "📊 Manage Inventory"])
    
    with tab1:
        st.subheader("Purchase from Farmers")
        available_batches = [b for b in st.session_state.get('batches', []) 
                            if b['owner'] != st.session_state.wallet]
        
        for batch in available_batches:
            with st.expander(f"Batch {batch['id']} - {batch['quantity']} units"):
                cols = st.columns([3,1,2])
                cols[0].write(f"**Seller:** {batch['owner']}")
                cols[1].number_input("Purchase Qty", key=f"qty_{batch['id']}", 
                                   min_value=1, max_value=batch['quantity'])
                if cols[2].button("Acquire Batch", key=f"buy_{batch['id']}"):
                    # Update ownership logic
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

elif st.session_state.role.to_string(index=False) == 'retailer':
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