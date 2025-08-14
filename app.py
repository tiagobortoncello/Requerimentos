import re
from io import BytesIO
from PyPDF2 import PdfReader
import streamlit as st

# Configuração da página
st.set_page_config(page_title="PDF → CSV", layout="centered")
st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
.block-container {padding-top: 2rem;}
</style>
""", unsafe_allow_html=True)

# Upload do PDF
uploaded = st.file_uploader("Enviar PDF", type=["pdf"])

def classify_req(segment: str) -> str:
    s = segment.lower()
    if "voto de congratula" in s:
        return "Voto de congratulações"
    elif "manifestação de pesar" in s:
        return "Manifestação de pesar"
    elif "manifestação de repúdio" in s:
        return "Manifestação de repúdio"
    elif "moção de aplauso" in s:
        return "Moção de aplauso"
    return ""

def process_pdf_to_tsv(file_like) -> BytesIO:
    # Ler PDF garantindo leitura correta
    file_bytes = BytesIO(file_like.read())
    reader = PdfReader(file_bytes)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    # Normalizar múltiplos espaços
    text = re.sub(r"[ \t]+", " ", text)

    requerimentos = []

    # Regex iguais às do Colab
    rqn_pattern = re.compile(r"^(?:\s*)(Nº)\s+(\d{2}\.?\d{3}/\d{4})\s*,\s*(do|da)", re.MULTILINE)
    rqc_pattern = re.compile(r"^(?:\s*)(nº)\s+(\d{2}\.?\d{3}/\d{4})\s*,\s*(do|da)", re.MULTILINE)

    # Processar RQN
    for match in rqn_pattern.finditer(text):
        start_idx = match.start()
        next_match = re.search(r"^(?:\s*)(Nº|nº)\s+(\d{2}\.?\d{3}/\d{4})", text[start_idx + 1:], flags=re.MULTILINE)
        end_idx = (next_match.start() + start_idx + 1) if next_match else len(text)
        block = text[start_idx:end_idx].strip()

        nums_in_block = re.findall(r'\d{2}\.?\d{3}/\d{4}', block)
        if not nums_in_block:
            continue
        num_part, ano = nums_in_block[0].replace(".", "").split("/")
        classif = classify_req(block)
        requerimentos.append(["RQN", num_part, ano, classif])

    # Processar RQC
    for match in rqc_pattern.finditer(text):
        start_idx = match.start()
        next_match = re.search(r"^(?:\s*)(Nº|nº)\s+(\d{2}\.?\d{3}/\d{4})", text[start_idx + 1:], flags=re.MULTILINE)
        end_idx = (next_match.start() + start_idx + 1) if next_match else len(text)
        block = text[start_idx:end_idx].strip()

        nums_in_block = re.findall(r'\d{2}\.?\d{3}/\d{4}', block)
        if not nums_in_block:
            continue
        num_part, ano = nums_in_block[0].replace(".", "").split("/")
        classif = classify_req(block)
        requerimentos.append(["RQC", num_part, ano, classif])

    # Remover duplicatas
    unique_reqs = []
    seen = set()
    for r in requerimentos:
        key = (r[0], r[1])
        if key not in seen:
            seen.add(key)
            unique_reqs.append(r)

    # Gerar TSV em memória
    buf = BytesIO()
    for r in unique_reqs:
        line = f"{r[0]}\t{r[1]}\t{r[2]}\t\t\t{r[3]}\n"
        buf.write(line.encode("utf-8"))
    buf.seek(0)
    return buf

# Interface
if uploaded is not None:
    csv_bytes = process_pdf_to_tsv(uploaded)
    st.download_button(
        label="Baixar CSV",
        data=csv_bytes,
        file_name="requerimentos_extraidos.csv",
        mime="text/csv"
    )
