import warnings
warnings.filterwarnings('ignore', message='.*torch.classes.*')

import streamlit as st
import logging
from datetime import datetime
from core.config import Config
from core.task_processor import TaskProcessor
from core.todoist_client import TodoistClient
from core.rag_engine import RAGEngine

logging.basicConfig(
    filename=Config.LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

st.set_page_config(
    page_title="AI Task Assistant - MVP",
    layout="wide"
)

def init_session_state():
    if 'rag_loaded' not in st.session_state:
        st.session_state.rag_loaded = False
    if 'processor' not in st.session_state:
        st.session_state.processor = None
    if 'todoist_client' not in st.session_state:
        st.session_state.todoist_client = None
        
def load_sop():
    try:
        rag = RAGEngine()
        chunks = rag.load_sop('data/sop_expenses.txt')

        # Inject dependency properly
        st.session_state.processor = TaskProcessor(rag_engine=rag)
        st.session_state.todoist_client = TodoistClient()

        st.session_state.rag_loaded = True
        return True, chunks

    except Exception as e:
        return False, str(e)

def main():
    init_session_state()
    
    st.title("AI Task Assistant - MVP Demo")
    st.markdown("---")
    
    # Configuration validation
    try:
        Config.validate()
    except ValueError as e:
        st.error(f"Configuration Error: {str(e)}")
        st.info("Please set up your .env file with required API keys")
        return
    
    # Initialize components
    if not st.session_state.rag_loaded:
        with st.spinner("Loading SOP knowledge base..."):
            success, result = load_sop()
            if success:
                st.success(f"SOP loaded successfully: {result} chunks indexed")
            else:
                st.error(f"Failed to load SOP: {result}")
                return
    
    if st.session_state.processor is None:
        st.session_state.processor = TaskProcessor()
        st.session_state.todoist_client = TodoistClient()
    
    # Main interface
    tab1, tab2 = st.tabs(["Create Task", "Ask SOP Question"])
    
    with tab1:
        st.header("Create Task from Request")
        
        user_request = st.text_area(
            "Enter task request:",
            placeholder="e.g., Buy MacBook for new developer, urgent",
            height=100
        )
        
        if st.button("Process Request", type="primary"):
            if not user_request.strip():
                st.warning("Please enter a task request")
            else:
                process_task_request(user_request)
    
    with tab2:
        st.header("Ask SOP Question")
        
        question = st.text_area(
            "Enter your question:",
            placeholder="e.g., Which card should I use for laptop purchases?",
            height=100
        )
        
        if st.button("Ask Question", type="primary"):
            if not question.strip():
                st.warning("Please enter a question")
            else:
                answer_question(question)

def process_task_request(request: str):
    """Process task creation request with SOP enrichment"""

    with st.expander("Processing Logs", expanded=True):

        # Step 1: Parse request
        st.write(f"{datetime.now().strftime('%H:%M:%S')} - Parsing request...")
        parsed = st.session_state.processor.parse_request(request)
        st.json(parsed)

        # Step 2: Search SOP
        st.write(f"{datetime.now().strftime('%H:%M:%S')} - Searching SOP knowledge base...")
        st.write(f"Query: {parsed['category']} - {parsed['title']}")

        sop_chunks = st.session_state.processor.rag_engine.query(
            f"{parsed['category']} {parsed['title']}",
            n_results=3
        )

        # Use container instead of expander
        st.subheader("Retrieved SOP Chunks")
        sop_container = st.container()

        if sop_chunks:
            with sop_container:
                for i, chunk in enumerate(sop_chunks):
                    st.text(f"Chunk {i+1}: {chunk[:200]}...")
        else:
            st.warning("No relevant SOP found")

        # Step 3: Generate enriched description
        st.write(f"{datetime.now().strftime('%H:%M:%S')} - Generating task description...")
        enriched_desc = st.session_state.processor.enrich_with_sop(parsed)

        # Another container
        st.subheader("Generated SOP-Enriched Description")
        st.write(enriched_desc)

        # Step 4: Create Todoist task
        st.write(f"{datetime.now().strftime('%H:%M:%S')} - Creating Todoist task...")

        try:
            task = st.session_state.todoist_client.create_task(parsed, enriched_desc)
            st.write(
                f"{datetime.now().strftime('%H:%M:%S')} - Task created successfully: ID {task['id']}"
            )
        except Exception as e:
            st.error(f"Failed to create task: {str(e)}")
            logging.error("Todoist creation failed", exc_info=True)
            return

    # Final summary (outside expander)
    st.success("Task Created Successfully in Todoist")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Task Summary")
        st.write(f"**Title:** {task['content']}")
        st.write(f"**Priority:** P{task['priority']}")
        st.write(f"**Todoist ID:** {task['id']}")
        st.markdown(f"[Open in Todoist]({task['url']})")

    with col2:
        st.subheader("SOP-Enriched Description")
        st.write(enriched_desc)

def answer_question(question: str):
    """Answer SOP question using RAG"""
    with st.spinner("Searching SOP knowledge base..."):
        answer = st.session_state.processor.answer_question(question)
    
    st.subheader("Answer")
    st.write(answer)

if __name__ == "__main__":
    main()