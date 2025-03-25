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
st.set_page_config(
    page_title="FemCite",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 👩‍🎨 Style tweak: increase input font size to match body text
st.markdown("""
    <style>
    /* Increase font size for input boxes */
    div[data-baseweb="input"] input {
        font-size: 1.1rem;
    }
    div[data-baseweb="select"] > div {
        font-size: 1.1rem;
    }

    /* Tighten spacing between form elements */
    .stTextInput, .stSelectbox {
        margin-bottom: 0.5rem;
    }

    label {
        margin-bottom: 0.25rem !important;
    }
    </style>
""", unsafe_allow_html=True)


st.title("🌸 FemCite – Femininities Citation Assistant")
st.markdown("""
_Helping you integrate femininities scholarship into your research, writing, and teaching — with a scholarly assistant for discovering, understanding, and citing work on femininities._
""")

st.divider()

st.markdown("""
📌 **FemCite is live!** You can share this tool: [https://femcite-ui.streamlit.app](https://femcite-ui.streamlit.app)

---

### 📝 How to Use FemCite

1. **Type your topic or question** (e.g., *femininity and leadership*) in the box above.
2. **Choose the citation style** you would like for the reference list.
3. **Submit your query.**

💡 *Ask more than one question — just type a new one when you're ready.*

⚠️ **Important:** Copy or download your output right away. If the app refreshes before you ask your next question, your original answer may disappear.
""")

st.divider()

# 🧠 Memory
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "citations" not in st.session_state:
    st.session_state.citations = ""
if "last_question" not in st.session_state:
    st.session_state.last_question = ""

# 💬 User prompt
st.markdown("### 💬 What are you researching or thinking about?")
user_question = st.text_input(label="", placeholder="Type your topic here...")

st.markdown("#### 📖 Choose citation style")
style = st.selectbox(label="", options=["APA", "MLA", "Chicago"])

# 🚀 Handle new question
if user_question and user_question != st.session_state.last_question:
    with st.spinner("🔍 FemCite is scanning the literature and thinking deeply... this may take a few minutes - hang tight!"):
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
You draw on a curated and continually growing library of real scholarship, not the entire internet.

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

        # 📂 Save files
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
    st.subheader("🧣️ Conversation History")
    for speaker, msg in st.session_state.chat_history:
        st.markdown(f"**{speaker}:**\n{msg}\n")
        st.markdown("---")

    with open("femcite_chat.txt", "r") as f:
        st.download_button("📂 Download Chat (.txt)", f.read(), file_name="femcite_chat.txt")

    with open("femcite.bib", "r") as f:
        st.download_button("📚 Export Citations (.bib)", f.read(), file_name="femcite.bib")

st.markdown("⬆️ Add a new question anytime using the box above.")


# 👇 Footer content shown after the results
st.markdown("""
---
### 📚 Journal of Femininities
Are you conducting research or scholarship related to femininities? Consider the [*Journal of Femininities*](https://brill.com/view/journals/fem/fem-overview.xml?language=en) as an outlet for your next manuscript.
""")

st.image(
    "https://brill.com/coverimage?doc=%2Fjournals%2Ffem%2Ffem-overview.xml&width=200&type=webp",
    caption="Journal of Femininities",
    use_container_width=False,  # or True if you prefer
    width=150  # thumbnail size!
)

st.markdown("""
💖 **Found this helpful?** Support us by donating to [LGBTQ Psychology Canada](https://lgbtqpsychology.com/make-an-online-donation).

---

📬 **Want to share feedback or report a bug?** Email us at [lgbtqpsychology@gmail.com](mailto:lgbtqpsychology@gmail.com)
""")

st.markdown(
    "Made with ❤️ by [LGBTQ Psychology Canada](https://lgbtqpsychology.com) • [Support our work](https://lgbtqpsychology.com/make-an-online-donation)",
    unsafe_allow_html=True
)
