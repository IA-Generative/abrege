import streamlit as st
import streamlit_dsfr as stdsfr
import requests
import json
import os

INTREGRATION_MIRAI = True

# REMOVE AND CONFIGURE
api_service = os.environ["API_BASE"]
base_api_url = f"http://{api_service}:8000"

st.set_page_config(page_title="Demo abrege", initial_sidebar_state="collapsed")
stdsfr.override_font_family()


@st.cache_data
def get_param():
    response = requests.get(base_api_url + "/default_params")
    if response.status_code == 200:
        payload = json.loads(response.content)
        return payload
    else:
        return None


try:
    available_params = get_param()
except requests.exceptions.ConnectionError:
    stdsfr.alert("Erreur lors du chargement de la configuration initiale", type="error")
    st.stop()


params = {}

st.sidebar.header("Paramètres")

for m in ("qwen2", "llama3", "phi3"):
    if m in available_params["models"]:
        index_model = available_params["models"].index(m)
        break
else:
    index_model = 0

params["model"] = st.sidebar.selectbox(
    label="Choisissez un modèle", options=available_params["models"], index=index_model
)
params["method"] = st.sidebar.selectbox(
    label="Choisissez une méthode", options=available_params["methods"]
)
params["temperature"] = st.sidebar.number_input(
    label="Choisissez une température", min_value=0.0, max_value=1.0, step=0.01
)
if 0:
    params["language"] = st.sidebar.text_input(
        label="Choisissez un language pour le résumé", value="French"
    )
else:
    params["language"] = st.sidebar.selectbox(
        label="Choisissez un language pour le résumé",
        options=["French", "English"],
        format_func={
            "French": "Français",
            "English": "Anglais",
        }.__getitem__,
        index=0,
    )


params["size"] = st.sidebar.number_input(
    label="Choissisez un nombre de mots pour votre résumé",
    min_value=50,
    max_value=300,
    step=1,
    value=200,
)

params["context_size"] = st.sidebar.number_input(
    label="Taille de contexte maximale pour le llm",
    min_value=1000,
    max_value=50_000,
    step=500,
    value=10_000,
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
if not INTREGRATION_MIRAI:
    st.header("Résumeur de documents")

    st.write(
        """Cette page web propose un service pour résumer un texte, une page web via une 
url ou bien un document. Le résumé est effectué à l'aide d'un LLM du MIOM, souverain et 
sans collecte de vos données. Les résumés produits peuvent être parametrisés à l'aide 
du menu déroulant à gauche"""
    )   

doc_type = st.selectbox(
    label="Choisissez le type du document à résumer",
    options=["texte", "URL", "document"],
    index=2,
)

if doc_type == "texte":
    user_input = st.text_area(label="Entrer votre texte", placeholder="Texte à résumer")
elif doc_type == "URL":
    user_input = st.text_area(
        label="Entrer votre URL", placeholder="URL vers la page web à résumer"
    )
elif doc_type == "document":
    user_input = stdsfr.dsfr_file_uploader(
        label="Téléverser votre document",
        help="Documents acceptés: .pdf, .docx, .odt, .txt",
    )
    if user_input is not None:
        if user_input.name.rsplit(".", 1)[-1] == "pdf":
            pdf_mode_ocr = st.selectbox(
                label="Dans le cas d'un document PDF. Est-ce que le docuemnt contient des pages scannées, uniquement du texte ou un mixte des deux ?",  # noqa
                options=["full_text", "text_and_ocr", "full_ocr"],
                format_func={
                    "full_text": "que du texte",
                    "full_ocr": "que des pages scannées",
                    "text_and_ocr": "mixte",
                }.__getitem__,
                index=0,
            )




def ask_llm(request_type, params, user_input) -> str:
    with st.spinner("Résumé en cours de fabrication..."):
        if request_type == "texte":
            url = base_api_url + "/text"
            params |= {"text": user_input}
            response = requests.get(url, params=params)
        elif request_type == "URL":
            url = base_api_url + "/url"
            params |= {"url": user_input}
            response = requests.get(url, params=params)
        elif request_type == "document":
            url = base_api_url + "/doc"
            file = {"file": (user_input.name, user_input)}
            params |= {"pdf_mode_ocr": pdf_mode_ocr}
            response = requests.post(url=url, files=file, params=params)

    if response.status_code == 200:
        summary = json.loads(response.content)["summary"]
        return summary
    else:
        if response.status_code == 500:
            stdsfr.alert("Erreur interne au service", type="error")
        elif response.status_code == 400:
            stdsfr.alert(
                "Impossible de traiter les documents. Veuillez vérifier que l'url est bonne ou que les documents ne sont pas scannés."  # noqa
            )


type_to_url_stream = {
    "texte": "text_stream",
    "document": "doc_stream",
}


def ask_llm_stream(request_type, params, user_input):
    url = f"{base_api_url}/{type_to_url_stream[request_type]}"
    s = requests.Session()
    if request_type == "texte":
        params |= {"text": user_input}
        with s.get(url=url, params=params, stream=True) as r:
            for chunk in r.iter_content(1024):
                yield chunk.decode()
    elif request_type == "document":
        file = {"file": (user_input.name, user_input)}
        params |= {"pdf_mode_ocr": pdf_mode_ocr}
        with s.post(url=url, params=params, files=file) as r:
            for chunk in r.iter_content(1024):
                yield chunk.decode()


# stdsfr button not working, seems to rerun to early to let st.spinner work
# maybe should open a pull request
st.session_state.stream = False
if st.button("Générer un résumé"):
    if params["method"] in ["text_rank", "k-means"] and doc_type != "url":
        st.write_stream(ask_llm_stream(doc_type, params, user_input))
        st.session_state.stream = True
    else:
        st.session_state.summary = ask_llm(doc_type, params, user_input)

if "summary" in st.session_state and not st.session_state.stream:
    st.write(st.session_state.summary)
