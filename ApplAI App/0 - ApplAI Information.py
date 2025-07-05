import streamlit as st
import base64

st.set_page_config(page_title="ApplAI", page_icon="💼", layout="centered")

st.markdown(
    """
    <div style='text-align: center;'>
        <img src="data:image/png;base64,{}" width="420">
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

st.subheader("***Smart Job Finder*** 🔍")

st.markdown("This system analyzes your **professional profile** and identifies **matching job opportunities** on **LinkedIn**. Simply **upload your profile** in any of the supported formats to receive a **personalized list of the best openings**, **ranked** by **relevance** and **compatibility** with your qualifications.")

st.subheader("***Smart Applicant Information Finder*** 🗃️")

st.markdown("This feature uses a **RAG** (Retrieval-Augmented Generation)-based system to **identify the most suitable candidates** in your **database** for a **specific job position**. Simply **upload the job description** in any format and receive a list ordered by **score** of the **best-matched profiles**.")

st.subheader("***Add a new candidate*** 💾")

st.markdown("Easily add **new applicants to your database** by uploading **files** or entering **LinkedIn/website links**. Our system automatically **processes** and **standardizes** all information.")

st.title("Who are the creators of ApplAI ?")

st.markdown("""
            The people in charge of creating this project were:
            - ##### ***Matias Antezana***
            - ##### ***Mateo Giacometti*** 
            - ##### ***Tiziano Leví Martin Bernal***
            - ##### ***Fausto Pettinari***
            """)

st.markdown("All of them are **Artificial Intelligence Engineering Students** at the ***University of San Andrés***. This project originated as the **final assignment** for the ***Natural Language Processing*** course.")

st.markdown("---")
st.markdown("© 2025 ApplAI. All rights reserved.")