import streamlit as st
import pandas as pd

st.title("📑 Reports")
st.markdown("---")

# Example static table (placeholder)
data = {
    "Incident": ["Theft", "Break-in", "Vandalism"],
    "Count": [120, 80, 45],
    "Status": ["Closed", "In Progress", "Open"]
}
df = pd.DataFrame(data)

st.subheader("Incident Summary")
st.table(df)
