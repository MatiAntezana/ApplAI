import streamlit as st
import base64

st.set_page_config(page_title="ApplAI", page_icon="💼", layout="centered")

st.markdown(
    """
    <div style='text-align: center;'>
        <img src="data:image/png;base64,{}" width="400">
    </div>
    """.format(
        base64.b64encode(open("ApplAI logo.png", "rb").read()).decode()
    ),
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

st.title("What is ApplAI ?")

st.title("Cuales son los modos de ApplAI ?")

st.title("Quienes son los creadores de ApplAI ?")

# Footer
st.markdown("---")
st.markdown("© 2025 ApplAI. All rights reserved.")


