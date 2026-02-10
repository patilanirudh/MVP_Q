# AI Task Assistant - MVP

Proof-of-concept automation system demonstrating intelligent task routing with SOP-based enrichment.

## Architecture

```
[Streamlit UI/Telegram bot] → [Task Processor] → [Todoist API]
                      ↓
                 [RAG Engine]
                      ↓
                 [ChromaDB + Groq]
```

## Components

- **Intake Layer**: Streamlit interface (swappable with Telegram/Email/Webhooks)
- **Intelligence Layer**: Groq LLM + ChromaDB vector search
- **Action Layer**: Todoist API integration
- **Knowledge Base**: SOP documents indexed in vector database

## Features Demonstrated

1. **Intake Parsing**: Natural language → Structured task data
2. **Vector Search**: RAG-based SOP retrieval
3. **Guided AI Response**: Context-aware task enrichment
4. **Basic Routing**: Automated Todoist task creation
5. **Logging**: Full activity trail
6. **Error Handling**: Graceful failure management

## Setup Instructions

### Prerequisites

- Python 3.9+
- Groq API key
- Todoist API key
- Telegram bot API

### Installation

```bash
# Clone repository
git clone <repository-url>
cd mvp

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys
```

### Running the Application

```bash
streamlit run app.py
python telegram_bot.py
```

## Tech Stack Rationale

| Component   | Choice                | Reason                                                    |
| ----------- | --------------------- | --------------------------------------------------------- |
| LLM         | Groq (Llama 3.1 70B)  | Free, fast inference, excellent for structured extraction |
| Vector DB   | ChromaDB              | Lightweight, no external dependencies, perfect for MVP    |
| Embeddings  | sentence-transformers | Local, no API costs, good quality                         |
| Task System | Todoist API           | Client requirement                                        |
| Interface   | Streamlit             | Rapid prototyping, clear demonstration                    |

### Production Ready

```
[Telegram]  ─┐
[Email]     ─┤
[WhatsApp]  ─┼→ [Core Processing] → [Todoist]
[Todoist WH]─┘   (unchanged)
```

Core processing logic is channel-agnostic. Adding new intake channels requires only new input handlers.

## File Structure

```
mvp/
├── app.py                   # Streamlit interface
├── telegram_bot.py          # chat interface
├── core/
│   ├── config.py            # Configuration management
│   ├── task_processor.py    # Task parsing and enrichment
│   ├── rag_engine.py        # Vector search and SOP retrieval
│   └── todoist_client.py    # Todoist integration
├── data/
│   └── sop_expenses.txt     # SOP knowledge base
├── logs/
│   └── app.log              # Application logs
└── requirements.txt
```
