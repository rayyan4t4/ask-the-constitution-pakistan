import streamlit as st
from rag import retrieve, generate

st.set_page_config(page_title="Ask the Constitution — Pakistan", page_icon="⚖️", layout="centered")

st.title("⚖️ Ask the Constitution")
st.caption("Ask questions about the Constitution of Pakistan in plain language. Answers are grounded in the actual articles, with citations.")

EXAMPLES = [
    "What does the constitution say about freedom of speech?",
    "Is there a right to a fair trial?",
    "How can the constitution be amended?",
    "When can emergency be proclaimed?",
]

query = st.text_input("Your question", placeholder="e.g. What are the qualifications to become a member of parliament?")
cols = st.columns(len(EXAMPLES))
for col, ex in zip(cols, EXAMPLES):
    if col.button(ex, key=ex[:20]):
        query = ex

if st.button("Ask", type="primary") and query and query.strip():
    with st.spinner("Searching the constitution..."):
        results = retrieve(query.strip(), k=5)

    if results and results[0]["score"] < 0.25:
        st.warning("I couldn't find a relevant article for that question. Try rephrasing, e.g. asking about a specific right, institution, or procedure.")
        st.stop()

    st.subheader("Answer")
    api_key = st.secrets.get("OPENROUTER_API_KEY", "")
    if not api_key:
        st.warning("The answer generator needs an API key (OPENROUTER_API_KEY) configured in this app's secrets. Showing retrieved articles below.")
    else:
        try:
            with st.spinner("Drafting answer from the articles..."):
                answer = generate(query.strip(), results, api_key)
            st.markdown(answer)
        except Exception as e:
            st.error(f"Answer generation failed ({e}). The retrieved articles below still answer your question.")

    st.subheader("Sources")
    seen = set()
    for r in results:
        key = r["article"]
        if key in seen:
            continue
        seen.add(key)
        with st.expander(f"Article {r['article']}: {r['title']}"):
            st.markdown(r["text"][:1500] + ("…" if len(r["text"]) > 1500 else ""))
            st.caption(f"[Read full article]({r['source']})")

st.divider()
st.caption("Informational only — not legal advice. Text: Constitution of Pakistan (1973, as amended), via pakistani.org. 323 articles + 5 schedules.")
