import streamlit as st
import base64

st.set_page_config(page_title="ApplAI", page_icon="💼", layout="centered")

st.markdown(
    """
    <div style='text-align: center;'>
        <img src="data:image/png;base64,{}" width="400">
    </div>
    """.format(
        base64.b64encode(open("imgs/applai_logo.png", "rb").read()).decode()
    ),
    unsafe_allow_html=True
)

st.markdown(
    """
    <h3 style='text-align: center;'>
        Fast Hiring. Better Jobs. Powered by AI 🤖
    </h3>
    """,
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)


st.title("What is ApplAI ?")

st.markdown("**ApplAI** is an intelligent platform designed to **transform job searching and hiring**, using artificial intelligence to ensure **the best candidates find the most suitable roles**.")

st.markdown("At **ApplAI**, we believe **a fairer and more efficient labor market is possible**. By connecting people with opportunities they truly deserve, we don’t just advance careers. We elevate workplace productivity and culture.")

st.title("What are the features of ApplAI ?")

st.subheader("***Compatibility Score Calculator*** 📊")

st.markdown("""Calculate your **compatibility score** between your **experience, skills and achievements** and the description of a **job** you would like to apply for using **AI**. Share your **profile** (LinkedIn, resume, or portfolio) and the **job ad**. We'll instantly analyze **how well you match the role**.""")

st.subheader("***Smart Applicant Information Finder*** 🗃️ ")

st.markdown("""FALTA DESCRIPCION""")

st.subheader("***Smart Job Finder*** 🔍")

st.markdown("""FALTA DESCRIPCION""")

st.title("Who are the creators of ApplAI ?")

st.markdown("""
            - ##### ***Matias Antezana***
            - ##### ***Mateo Giacometti*** 
            - ##### ***Tiziano Leví Martin Bernal***
            - ##### ***Fausto Pettinari***
            """)

st.markdown("---")
st.markdown("© 2025 ApplAI. All rights reserved.")