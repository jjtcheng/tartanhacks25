
import streamlit as st
import pandas as pd
import numpy as np

# Create sample data
data = pd.DataFrame({
    'latitude': [37.7749, 34.0522, 40.7128],
    'longitude': [-122.4194, -118.2437, -74.0060] #map location over time, at each time state.
})

# Display the map
st.map(data)
