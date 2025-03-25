import os
import streamlit as st
import requests
from openai import OpenAI
from dotenv import load_dotenv

# 🔐 Load OpenAI key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🌸 Femme theory guidance
femcite_concepts = """
Core concepts from femininities studies that guide your answers include:
- Femininity is not inherently tied to womanhood. It is a socially constructed, often devalued mode of gender expression.
- Femmephobia refers to the systemic devaluation and regulation of femininity, regardless of who expresses it.
- Femininity is often perceived as less rational, less serious, or less powerful — contributing to its marginalization across gender, race, and class.
- Masculinity is often seen as the default for credibility, authority, and strength — even within feminist, queer, or academic spaces.
- Resistance to anti-femininity may involve reclaiming or revaluing femininity, asserting femme identity, or challenging dominant gender hierarchies.
"""

# 🧠 Call FemCite backend to get semantically relevant sources
def search_femcite_api(query, top_k=10):
    url = "https://femcite-api.onrender.com/search"
    payload = {"query": query, "top_k": top_k}
    response = requests.post(url, json=payload)
    results = response.json()["results"]

    entries = []
    for item in results:
        title = item["title"]
        abstract = item["abstract"]
        authors = item["authors"]
        year = item["year"]
        doi = item["doi"]

        citation = f"{title} ({year}) by {authors}"
        if doi:
            citation += f" — [DOI link](https://doi.org/{doi})"

        entries.append({
            "citation": citation,
            "doi": doi,
            "title": title,
            "authors": authors,
            "year": year,
            "abstract": abstract
        })
    return entries

# ✨ Format citations with GPT
@st.cache_data(show_spinner=False)
def format_citations(entries, style):
    refs = "\n".join(f"{i+1}. {e['citation']}" for i, e in enumerate(entries))
    prompt = f"""
Format the following references in {style} style. Do not add any references. Only return formatted references.

References:
{refs}
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# 🎨 UI Setup
st.set_page_config(page_title="FemCite", layout="centered")
st.title("🌸 FemCite – Femininities Citation Assistant")

st.markdown("""
_Helping you integrate femininities scholarship into your research, writing, and teaching — with a scholarly assistant for discovering, understanding, and citing work on femininities._
""")
st.divider()

st.markdown("""
📌 **FemCite is live!** You can share this tool using: [https://femcite-ui.streamlit.app](https://femcite-ui.streamlit.app)

---

### 📝 How to Use FemCite

1. **Type your topic** (e.g., _femininity and leadership_) in the box above. You can also ask more complex questions!
2. **Choose APA** from the dropdown (more styles coming soon).
3. **Submit your query.**

💡 _You can ask multiple questions — type a new one when ready._

⚠️ **Important:** Be sure to copy or download your output immediately. If the app refreshes before you ask a new question, your answer may disappear.
""")

# 🧠 Memory
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "citations" not in st.session_state:
    st.session_state.citations = ""
if "last_question" not in st.session_state:
    st.session_state.last_question = ""

# 💬 User prompt
user_question = st.text_input("💬 What are you researching or thinking about?")
style = st.selectbox("📖 Choose citation style (reference list only — APA used for in-text)", ["APA", "MLA", "Chicago"])

# 🚀 Handle new question
if user_question and user_question != st.session_state.last_question:
    with st.spinner("Fetching sources and generating response..."):

        entries = search_femcite_api(user_question, top_k=10)

        if not entries:
            st.info("🤔 I couldn’t locate anything in the library that connects to that topic. Try rephrasing your question or narrowing the focus.")
            st.stop()

        source_block = "\n\n".join(
            f"Title: {e['title']}\nAuthors: {e['authors']}\nYear: {e['year']}\nAbstract: {e['abstract']}" for e in entries
        )

        # 🧠 GPT annotation
        prompt = f"""
You are FemCite, a scholarly research assistant grounded in the field of femininities. 
You draw on a curated and continually growing library of real scholarship — not the entire internet.

{femcite_concepts}

A researcher has asked the following:
"{user_question}"

Your task:
- Provide a thoughtful, citation-grounded response to the user's topic.
- Always use APA-style in-text citations (author, year), regardless of reference list format. 
    - Use "&" for two authors (e.g., Blair & Hoskin, 2019)
    - Use "et al." for more than 2 authors (e.g., Blair, Hoskin, & Courtice, 2020 becomes Blair et al., 2020)
- Highlight how one or more of the sources connect to their area of interest, using author names not source numbers.
- Avoid generic openings or abstract summaries — start with a precise, grounded statement that engages directly with the user's topic.
- Avoid phrases like "the provided sources" or "Source 1." Refer to authors and years only.
- Use the term "femininity" consistently and correctly. Do not use alternate forms like "feminicity."
- Do not invent or hallucinate any sources. Only refer to the actual sources below.
- Encourage the user to reflect critically on their assumptions through the lens of femme theory.
- Prioritize truth and clarity over agreement. If the user's logic is weak, gently explain why.
- Do not critique femme theory.
- Be supportive and constructive in all feedback.
- If you don’t know, say so. Never fabricate information.
- Make sure in-text citations follow proper APA grammar for ampersands and et al.


Sources:
{source_block}
"""
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.choices[0].message.content

        # 💬 Save to memory
        st.session_state.chat_history = []
        st.session_state.chat_history.append(("You", user_question))
        st.session_state.chat_history.append(("FemCite", answer))

        st.session_state.citations = format_citations(entries, style)
        st.session_state.chat_history.append((f"{style} citations", st.session_state.citations))
        st.session_state.last_question = user_question

        # 💾 Save files
        chat_txt = "\n\n".join(f"{speaker}:\n{msg}" for speaker, msg in st.session_state.chat_history)
        with open("femcite_chat.txt", "w", encoding="utf-8") as f:
            f.write(chat_txt)

        bib_entries = [
            f"""@article{{femcite{i+1},
  title={{ {e['title']} }},
  author={{ {e['authors']} }},
  year={{ {e['year']} }},
  doi={{ {e['doi']} }}
}}""" for i, e in enumerate(entries) if e['doi']
        ]
        bib_text = "\n\n".join(bib_entries)
        with open("femcite.bib", "w", encoding="utf-8") as f:
            f.write(bib_text)

# 💬 Display history
if st.session_state.chat_history:
    st.subheader("🗣️ Conversation History")
    for speaker, msg in st.session_state.chat_history:
        st.markdown(f"**{speaker}:**\n{msg}\n")
        st.markdown("---")

    with open("femcite_chat.txt", "r") as f:
        st.download_button("💾 Download Chat (.txt)", f.read(), file_name="femcite_chat.txt")

    with open("femcite.bib", "r") as f:
        st.download_button("📚 Export Citations (.bib)", f.read(), file_name="femcite.bib")

st.markdown("⬆️ Add a new question anytime using the box above.")

# 📚 Journal of Femininities
st.divider()
st.markdown("### 📖 Journal of Femininities")
st.markdown("""
Are you conducting research or scholarship related to femininities?  
Consider the [**Journal of Femininities**](https://brill.com/view/journals/fem/fem-overview.xml?language=en) as an outlet for your next manuscript.
""")

col1, col2 = st.columns([1, 3])
with col1:
    st.image(
        "https://brill.com/coverimage?doc=%2Fjournals%2Ffem%2Ffem-overview.xml&width=200&type=webp",
        caption="Journal of Femininities",
        use_container_width=True
    )
with col2:
    st.markdown("""
The *Journal of Femininities* is a peer-reviewed, interdisciplinary journal for innovative scholarship on femininities.  
Explore current and past issues on [Brill’s website](https://brill.com/view/journals/fem/fem-overview.xml?language=en).
""")
