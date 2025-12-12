# Multi-Agent File Editor

Multi-agent system for editing up to 50 files with AI. Local Docker deployment with FastAPI + LangGraph.

## Features

- **Upload up to 50 files** via web interface
- **Each file gets its own AI agent** for processing
- **Central coordinator agent** distributes your voice/text commands to appropriate file agents
- **Local deployment** - runs entirely on your computer via Docker
- **File persistence** - your files are stored in `./files/` directory

## Architecture

```
Frontend (Web UI)
    ↓
FastAPI Backend (port 8000)
    ↓
Central Agent (LangGraph)
    ├── Analyzes your commands
    └── Delegates to File Agents
        ├── Agent 1 → file_1.txt
        ├── Agent 2 → file_2.py
        └── Agent N → file_N.md
```

## Quick Start

### Prerequisites

- Docker Desktop (Windows 10/11) or Docker Engine (Linux)
- 4GB+ RAM recommended
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Aidariki/multi-agent-file-editor.git
cd multi-agent-file-editor
```

2. Start the system:
```bash
docker compose up
```

3. Open in browser:
```
http://localhost:8000
```

### Stopping

```bash
Ctrl+C
# или
docker compose down
```

## Project Structure

```
multi-agent-file-editor/
├── backend/
│   ├── app/
│   │   └── main.py          # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile          # Backend container
├── files/                  # Your uploaded files (mounted volume)
└── docker-compose.yml      # Docker orchestration
```

## Usage

1. **Upload Files**: Drag-and-drop up to 50 files into the web interface
2. **Give Commands**: Type or speak commands like:
   - "Add TODO comment to file_1.py"
   - "Fix typos in file_2.md"
   - "Translate file_3.txt to English"
3. **Review Changes**: Agents process files and save results to `./files/`

## Technology Stack

- **Backend**: FastAPI (Python 3.13)
- **AI Framework**: LangGraph for multi-agent orchestration
- **Containerization**: Docker + Docker Compose
- **LLM**: Compatible with Ollama (local) or external APIs

## Development

### Adding LLM Support

Edit `backend/app/main.py` to configure your preferred LLM:

```python
# Option 1: Local Ollama
from langchain_ollama import ChatOllama
llm = ChatOllama(model="llama3.2")

# Option 2: Google Gemini API
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-pro")
```

### Hot Reload for Development

Mount your code as volume in `docker-compose.yml`:

```yaml
volumes:
  - ./backend/app:/app/app
  - ./files:/app/files
```

## Troubleshooting

**Port 8000 already in use:**
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

**Out of memory:**
- Close other applications
- Increase Docker memory limit in Docker Desktop settings

## License

MIT License - see [LICENSE](LICENSE) file

## Contributing

Pull requests welcome! Please ensure:
1. Code follows PEP 8 (Python)
2. Add tests for new features
3. Update documentation

## Roadmap

- [ ] Web Speech API for voice commands
- [ ] Frontend UI with drag-and-drop
- [ ] Agent memory/context persistence
- [ ] Support for 100+ files
- [ ] Real-time WebSocket updates
- [ ] Multi-language support (Russian, English)

---

**Author**: Aidariki  
**Year**: 2025
