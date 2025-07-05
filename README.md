# **ApplAI - Fast Hiring. Better Jobs. Powered by AI** 🤖

<p align="center">
  <img src="ApplAI App/imgs/logo_og.png", width="300"/>
</p>


<div style='text-align: center;'>
    <img src="data:image/png;base64,{BASE64_STRING}" width="500">
</div>

## What is ApplAI ?

**ApplAI** is an intelligent platform designed to **transform job searching and hiring**, using artificial intelligence to ensure **the best candidates find the most suitable roles**.

At **ApplAI**, we believe **a fairer and more efficient labor market is possible**. By connecting people with opportunities they truly deserve, we don’t just advance careers. We elevate workplace productivity and culture.

## What are the features of ApplAI ?

### ***Compatibility Score Calculator*** 📊

Calculate your **compatibility score** between your **experience, skills and achievements** and the description of a **job** you would like to apply for using **AI**. Share your **profile** (LinkedIn, resume, or portfolio) and the **job ad**. We'll instantly analyze **how well you match the role**.

### ***Smart Job Finder*** 🔍

This system analyzes your **professional profile** and identifies **matching job opportunities** on **LinkedIn**. Simply **upload your profile** in any of the supported formats to receive a **personalized list of the best openings**, **ranked** by **relevance** and **compatibility** with your qualifications.

### ***Smart Applicant Information Finder*** 🗃️

This feature uses a **RAG** (Retrieval-Augmented Generation)-based system to **identify the most suitable candidates** in your **database** for a **specific job position**. Simply **upload the job description** in any format and receive a list ordered by **score** of the **best-matched profiles**.

### ***Add a new candidate*** 💾

Easily add **new applicants to your database** by uploading **files** or entering **LinkedIn/website links**. Our system automatically **processes** and **standardizes** all information.

## Installation

To get **ApplAI** up and running, follow these steps:

### 1. Clone the repository

Download or clone this repository to your local machine.

### 2. Install dependencies

Navigate to the main application folder:

```bash
cd "ApplAI App"
```

Install the required Python dependencies using `pip` and the provided `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### 3. Install Tesseract OCR

The application uses **Tesseract for Optical Character Recognition (OCR)** allowing it to extract text from images (e.g., screenshots or scanned resumes).

Install it according to your operating system:

- Linux (Debian/Ubuntu):
```bash
sudo apt install tesseract-ocr
```
- macOS:
```bash
brew install tesseract
```
- Windows:
```bash
choco install tesseract
```

### 4. Obtain API Keys

To use the AI features, you need to obtain API keys for the following services:

- [**Enrich Layer**](https://enrichlayer.com/): For web scraping and job search (only for LinkedIn Profiles and job ads).
- [**SerpAPI**](https://serpapi.com/): For web scraping and job search.
- [**Azure OpenAI**](https://azure.microsoft.com/es-es/free/students): For natural language processing and core AI capabilities.

### 5. Run the Application

From within the `ApplAI App` folder, launch the app with:
```bash
streamlit run "0 - ApplAI Information.py"
```
### Additional Notes
The main application is entirely contained within the `ApplAI App` folder.

The `development_and_research` directory includes **experiments**, **tests**, and **exploratory work** carried out during development. While it's not required to run the app, we recommend reviewing it to better understand the development process and how the final version was built.

## Who are the creators of ApplAI ?

The people in charge of creating this project were:
- ##### ***Matias Antezana***
- ##### ***Mateo Giacometti*** 
- ##### ***Tiziano Leví Martin Bernal***
- ##### ***Fausto Pettinari***

All of them are **Artificial Intelligence Engineering Students** at the ***University of San Andrés***. This project originated as the **final assignment** for the ***Natural Language Processing*** course.

---

© 2025 ApplAI. All rights reserved.