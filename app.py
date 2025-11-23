import google.generativeai as genai
import streamlit as st

st.title("Teste Gemini Model - Listagem de métodos e atributos")

API_KEY = st.text_input("Insira sua API Key do Google Generative AI", type="password")

if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")
    attrs = dir(model)

    st.subheader("Atributos e métodos do modelo Gemini:")
    st.code("\n".join(attrs))
else:
    st.info("Por favor, insira sua API Key para testar.")
