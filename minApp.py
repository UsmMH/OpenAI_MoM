# minApp.py - Simplified Version (env-based API key, no sidebar, better error details)
import os
import time
import streamlit as st
from dotenv import load_dotenv, find_dotenv

from minNode import OpenAIClient, extract_text_from_pdf, extract_text_from_docx

st.set_page_config(page_title="Meeting Minutes Generator", page_icon="📝")

# Load environment variables from .env (anywhere up the tree)
load_dotenv(find_dotenv())

@st.cache_resource
def get_openai_client():
    return OpenAIClient()

def format_minutes_as_markdown(minutes):
    # This function is updated for the new, more flexible data structure.
    sections = [
        ("## 📝 Summary", minutes.get("summary", "")),
        ("## 👥 Participants", "\n".join(f"- {p}" for p in minutes.get("participants", []))),
        ("## 🗣️ Discussion Points", "\n".join(f"- {t}" for t in minutes.get("discussion_points", []))),
        ("## ✅ Outcomes or Decisions", "\n".join(f"- {d}" for d in minutes.get("outcomes_or_decisions", []))),
        ("## 🚀 Next Steps", "\n".join(f"- {s}" for s in minutes.get("next_steps", [])))
    ]
    # Creates the full markdown document, skipping any empty sections.
    return "\n\n".join(f"{header}\n{content}" for header, content in sections if content)

# def format_action_items(items):
#     if not items:
#         return ""
#     formatted = []
#     for item in items:
#         line = f"- {item.get('task', '')}"
#         if item.get('assignee'):
#             line += f" (Assigned: {item['assignee']})"
#         if item.get('deadline'):
#             line += f" (Due: {item['deadline']})"
#         formatted.append(line)
#     return "\n".join(formatted)

def main():
    st.title("📝 Meeting Minutes Generator")
    st.caption("Transform meeting transcripts into professional minutes using AI")

    # --- 1. API Key Handling & Connection Test ---
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not os.getenv("OPENAI_API_KEY"):
        st.error("🔴 Missing OPENAI_API_KEY. Please create a .env file with your key.")
        st.info("Example .env file:\n\n`OPENAI_API_KEY=\"your_api_key_here\"`")
        st.stop()

    client = get_openai_client()
    # Set the key, but don't show a message yet.
    client.set_api_key(api_key)

    # Test the connection. The app functioning is the confirmation, so we only show an error on failure.
    ok, msg = client.test_connection()
    if not ok:
        st.error(f"OpenAI connection failed: {msg}")
        st.stop()

    # --- 2. File Input ---
    st.subheader("Input Transcript")
    uploaded_file = st.file_uploader("Upload transcript file (.txt, .pdf, .docx)", type=["txt", "pdf", "docx"])
    transcript_text = st.text_area("Or paste transcript here:", height=200, placeholder="Paste your meeting transcript content here...")

    final_transcript = ""
    if uploaded_file:
        with st.spinner("Reading file..."):
            if uploaded_file.type == "text/plain":
                final_transcript = uploaded_file.read().decode("utf-8", errors="ignore")
            elif uploaded_file.type == "application/pdf":
                final_transcript = extract_text_from_pdf(uploaded_file)
            elif "wordprocessingml" in uploaded_file.type:
                final_transcript = extract_text_from_docx(uploaded_file)

        if final_transcript:
            st.success(f"✅ Successfully loaded {len(final_transcript):,} characters from {uploaded_file.name}")
        else:
            st.warning("Could not extract text from the uploaded file.")
    elif transcript_text.strip():
        final_transcript = transcript_text.strip()

    # --- 3. Generation ---
    if st.button("🚀 Generate Minutes", type="primary", disabled=not final_transcript, use_container_width=True):
        with st.spinner("Generating minutes... This may take a moment."):
            minutes = client.generate_meeting_minutes(final_transcript)

        if "Could not automatically generate minutes" in minutes.get("summary", ""):
            st.error(f"Failed to generate minutes. Error: {client.last_error or 'The AI could not process this transcript.'}")
            st.stop()

        st.success("✅ Minutes generated successfully!")
        st.session_state.minutes = minutes # Save to session state to persist

    # --- 4. Display Results (using st.expander for a cleaner look) ---
    if 'minutes' in st.session_state:
        minutes = st.session_state.minutes
        tab1, tab2 = st.tabs(["📊 Structured View", "📄 Markdown & Export"])

        with tab1:
            st.header("Analysis Results")
            
            # Use expanders for a clean, organized layout
            with st.expander("📝 **Summary**", expanded=True):
                st.write(minutes.get("summary", "Not available."))

            with st.expander("👥 **Participants**"):
                if participants := minutes.get("participants"):
                    for p in participants:
                        st.markdown(f"- {p}")
                else:
                    st.caption("No participants identified.")

            with st.expander("🗣️ **Discussion Points**"):
                if points := minutes.get("discussion_points"):
                    for t in points:
                        st.markdown(f"- {t}")
                else:
                    st.caption("No key topics identified.")
            
            with st.expander("✅ **Outcomes or Decisions**"):
                if decisions := minutes.get("outcomes_or_decisions"):
                    for d in decisions:
                        st.markdown(f"- {d}")
                else:
                    st.caption("No outcomes or decisions identified.")

            with st.expander("🚀 **Next Steps**"):
                if steps := minutes.get("next_steps"):
                    for s in steps:
                        st.markdown(f"- {s}")
                else:
                    st.caption("No next steps identified.")

        with tab2:
            st.header("Export Minutes")
            markdown_content = format_minutes_as_markdown(minutes)
            
            # Use st.code for a clean display with a built-in copy button
            st.code(markdown_content, language='markdown')
            
            st.download_button(
                "⬇️ Download as Markdown (.md)",
                markdown_content,
                "meeting_minutes.md",
                "text/markdown",
                use_container_width=True
            )

if __name__ == "__main__":

    main()
