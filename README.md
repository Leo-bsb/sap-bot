
# 🤖 SAP Data Services AI Assistant

![Streamlit](https://img.shields.io/badge/streamlit-deployed-green?logo=streamlit)
![Python](https://img.shields.io/badge/python-3.9%2B-blue?logo=python)
![Google Gemini](https://img.shields.io/badge/Google-Gemini%202.5%20Flash-blueviolet)
![RAG](https://img.shields.io/badge/RAG-Retrieval--Augmented--Generation-orange)
![SAP](https://img.shields.io/badge/SAP-Data%20Services-EBAF16?logo=sap)

---

## 🚀 Project Overview

This project delivers a specialized **chatbot assistant for SAP Data Services ECC**, designed to bridge the knowledge gap left by general-purpose AI models that lack depth on SAP-specific functions. Leveraging Google Gemini 2.5 Flash alongside Retrieval-Augmented Generation (RAG) techniques over the official SAP documentation, it offers precise, context-aware answers for SAP Data Services users.

---

## 🎯 Key Features

- **Advanced Language Model:** Powered by Google Gemini 2.5 Flash for natural, fluent responses.
- **RAG Approach:** Semantic search with vector embeddings on SAP official documentation for accurate retrieval.
- **Intent Detection:** Contextual understanding to recommend relevant SAP functions.
- **Fallback Mechanism:** Robust fallback with template-based responses ensuring consistent availability.
- **User-Friendly UI:** Interactive Streamlit interface optimized for quick, clear SAP queries.
- **Portuguese Language Support:** Answers delivered in natural Portuguese with practical examples.

---

## 🛠️ Technologies

- **LLM:** Google Gemini 2.5 Flash
- **Retrieval-Augmented Generation (RAG)**
- **Vector Embeddings & Semantic Search**
- **Streamlit for UI**
- **SAP Data Services Official Documentation**

---

## 📎 How to Use

Access the deployed app directly here:

[https://sap-bot.streamlit.app/](https://sap-bot.streamlit.app/)

---

## 📚 Architecture Overview

```plaintext
User Query
    ↓
Intent Analysis
    ↓
Vector Search over SAP Docs (RAG)
    ↓
Google Gemini 2.5 Flash (Response Generation)
    ↓
Natural, Contextual Answer in Portuguese
````

---

## 🔍 Example Questions

* How to use the LOOKUP function?
* How to perform data validation?
* Difference between MERGE and INSERT?
* How to work with date functions?
* What is the syntax for CASE WHEN?

---

## ⚙️ Running Locally

1. Clone the repository:

```bash
git clone https://github.com/leo-bsb/sap-bot.git
cd sap-bot
```

2. Set up environment and install dependencies (adjust Python version >=3.9):

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

3. Initialize the index (embedding setup):

```bash
python setup_index.py
```

4. Run the Streamlit app:

```bash
streamlit run app_enhanced.py
```

---

## 🤝 Connect with Me

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Leonardo%20Borges-blue?logo=linkedin)](https://www.linkedin.com/in/leonardo-borges1/)

---

## 📝 Notes & Next Steps

* **Improve multilingual support:** Add English question answering.
* **Expand knowledge base:** Integrate other SAP modules.
* **Enhance RAG pipeline:** Incorporate dynamic updates from SAP releases.
* **Add analytics:** Track usage patterns and refine intent detection.

---

Thank you for checking out the SAP Data Services AI Assistant! This tool aims to empower SAP users with faster, deeper access to key functionality and reduce dependency on generic AI that often misses SAP specifics.

---

*Built with ❤️ by Leonardo Borges*
