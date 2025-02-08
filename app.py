import streamlit as st
import pandas as pd

# Initialize session state
if 'show_map' not in st.session_state:
    st.session_state.show_map = False

# Create toggle button
if st.button('Toggle Map Visibility'):
    st.session_state.show_map = not st.session_state.show_map

# Only show map when state is True
if st.session_state.show_map:
    # Create sample data
    data = pd.DataFrame({
        'latitude': [37.7749, 34.0522, 40.7128],
        'longitude': [-122.4194, -118.2437, -74.0060]
    })
    
    # Display the map
    st.map(data)
else:
    # Blank screen with just the button
    st.write("")  # Empty space to maintain layout
