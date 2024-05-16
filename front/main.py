import streamlit as st
import streamlit_dsfr as stdsfr
import requests
import json

# REMOVE AND CONFIGURE
base_api_url = "http://127.0.0.1:8000"

st.set_page_config(page_title="Demo abrege", initial_sidebar_state="collapsed")
stdsfr.override_font_family()


@st.cache_data
def get_param():
    try:
        response = requests.get(base_api_url + "/default_params")
        if response.status_code == 200:
            payload = json.loads(response.content)
            return payload
        else:
            return None
    except requests.exceptions.ConnectionError:
        return None


available_params = get_param()

if available_params is None:
    stdsfr.alert("Erreur lors du chargement de la configuration initiale", type="error")
    st.stop()

params = {}

st.sidebar.header("Paramètres")

params["model"] = st.sidebar.selectbox(
    label="Choisissez un modèle", options=available_params["models"]
)
params["method"] = st.sidebar.selectbox(
    label="Choisissez une méthode", options=available_params["methods"]
)
params["temperature"] = st.sidebar.number_input(
    label="Choisissez une température", min_value=0.0, max_value=1.0, step=0.01
)
params["language"] = st.sidebar.text_input(
    label="Choisissez un language pour le résumé", value="French"
)
st.sidebar.header("Personalisation des prompts")

expander1 = st.sidebar.expander("Prompt pour les méthodes text_rank, k-means et stuff")
params["summarize_template"] = expander1.text_area(
    label="summarize_prompt", value=available_params["prompt_template"]["summarize"]
)

expander2 = st.sidebar.expander("Prompt pour la méthod map_reduce")
params["map_template"] = expander2.text_area(
    label="map_template", value=available_params["prompt_template"]["map"]
)
params["reduce_template"] = expander2.text_area(
    label="reduce_template", value=available_params["prompt_template"]["reduce"]
)

expander3 = st.sidebar.expander("Prompt pour la méthode refine")
params["question_template"] = expander3.text_area(
    label="question_template", value=available_params["prompt_template"]["question"]
)
params["refine_template"] = expander3.text_area(
    label="refine_template", value=available_params["prompt_template"]["refine"]
)
