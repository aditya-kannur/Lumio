import streamlit as st
import requests
from dotenv import load_dotenv
load_dotenv()

st.title("VersionQuery")
st.caption("Version-aware Q&A over Notion API docs")

if "history" not in st.session_state:
    st.session_state.history = []

question = st.chat_input("Ask a question about the Notion API...")

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if question:
    st.session_state.history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                r = requests.post(
                    "http://localhost:8000/ask",
                    json={"question": question},
                    timeout=120,
                )
                r.raise_for_status()
                resp = r.json()
            except requests.exceptions.ConnectionError:
                content = "⚠️ Could not reach the backend. Make sure the FastAPI server is running on port 8000."
                st.error(content)
                st.session_state.history.append({"role": "assistant", "content": content})
                st.stop()
            except Exception as e:
                content = f"⚠️ Backend error: {e}"
                st.error(content)
                st.session_state.history.append({"role": "assistant", "content": content})
                st.stop()

            if resp["type"] == "clarification":
                content = resp["message"]
            elif resp["type"] == "not_found":
                content = resp["message"]
            elif resp["type"] == "error":
                content = f"⚠️ Server error: {resp['message']}"
            else:
                citations = "\n".join(f"- {c}" for c in resp.get("citations", []))
                content = f"{resp['answer']}\n\n**Sources:**\n{citations}" if citations else resp["answer"]

            st.write(content)
            st.session_state.history.append({"role": "assistant", "content": content})
