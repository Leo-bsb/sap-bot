import google.generativeai as genai
import streamlit as st

st.markdown("###Status")

genai.configure(api_key="SUA_API_KEY")

model = genai.GenerativeModel("gemini-2.0-flash")

print(dir(model))





