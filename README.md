# Multi-Agent System with Ollama & Telegram

# 1 Organization 
A production-ready multi-agent system that leverages Ollama's local LLMs with a hierarchical routing architecture and Telegram integration.

## Models 

### ===== TIER 1: ESSENTIAL =====
ollama pull gemma3:1b
ollama pull gemma3:4b
ollama pull qwen2.5-coder:3b
ollama pull qwen2.5-coder:7b
ollama pull phi4:14b

### ===== TIER 2: EXTENDED =====
ollama pull llama3.2-vision:11b
ollama pull minicpm-v:8b
ollama pull aya:8b
ollama pull nous-hermes2:10.7b
ollama pull mistral-nemo:12b
ollama pull qwen2.5:14b

### ===== TIER 3: MAXIMUM QUALITY =====
ollama pull gemma3:12b
ollama pull qwen2.5:32b
ollama pull deepseek-coder-v2:16b
ollama pull command-r:35b

## Agent Architecture with New Stack
```markdown 
INPUT → gemma3:1b (Route) → Specialist:
                            ├── Vision/Finance: gemma3:4b
                            ├── Code (fast): qwen2.5-coder:3b  
                            ├── Code (complex): qwen2.5-coder:7b
                            ├── Vision (heavy): qwen3-vl
                            └── Agent/Tool: qwen3


🏗️ Architecture

┌─────────────────────────────────────────────────────────┐
│                    INPUT LAYER                          │
│         (Email, Chat, Document, Voice)                  │
└─────────────────────────┬───────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│  ROUTER (gemma3:1b) - Instant classification            │
│  "What type of task? → Route to specialist"             │
│  Priority: urgent/normal | Category: code/vision/text   │
└─────────────────────────┬───────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   VISION     │  │    CODE      │  │   ANALYSIS   │
│   PIPELINE   │  │   PIPELINE   │  │   PIPELINE   │
│              │  │              │  │              │
│ gemma3:4b    │  │ qwen2.5-coder│  │   phi4:14b   │
│ (general)    │  │   :3b (fast) │  │ (deep think) │
│              │  │              │  │              │
│ llama3.2-vis │  │ qwen2.5-coder│  │ qwen2.5:14b  │
│ :11b (complex│  │   :7b (arch) │  │ (logic/math) │
│              │  │              │  │              │
│ minicpm-v:8b │  │ deepseek-code│  │ gemma3:12b   │
│ (OCR/docs)   │  │ r-v2:16b     │  │ (upgrade)    │
│              │  │ (complex)    │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        └─────────────────┴─────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│  SYNTHESIZER (gemma3:4b or aya:8b)                      │
│  "Format output, generate response, update memory"      │
└─────────────────────────────────────────────────────────┘
```
## 1.2 Data Flow Pipeline

1. User Input → Telegram Message
2. Intent Classification → gemma3:1b (50-100ms)
3. Task Routing → Specialized Model
4. Processing → Domain-Specific Execution
5. Synthesis → Response Formatting
6. Output → Telegram Reply

INPUT → gemma3:1b (Router) → Specialist Models → Synthesizer → Telegram


- **Router**: gemma3:1b (50-100ms intent classification)
- **Code**: qwen2.5-coder (3b/7b/16b) for fast/complex code generation
- **Vision**: gemma3:4b, llama3.2-vision:11b, minicpm-v:8b
- **Analysis**: phi4:14b, qwen2.5:14b for deep reasoning
- **Synthesis**: aya:8b for multilingual response formatting

## ✨ Features

- 🤖 **Multi-Model Orchestration**: Automatic routing to specialized models
- 💬 **Telegram Integration**: Full-featured bot with inline keyboards
- 📧 **Email Automation**: Fetch, prioritize, and reply to emails
- 💻 **Code Generation**: Multi-language with execution testing
- 🖼️ **Vision Processing**: Image analysis and OCR
- 🔍 **Web Search**: Search and summarize information
- ⏰ **Reminders**: Scheduled notifications
- 🧠 **Memory Management**: Redis-based conversation memory
- 🚀 **Production Ready**: Docker, Poetry, comprehensive logging

## 📋 Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/)
- [Ollama](https://ollama.ai/)
- 16GB+ RAM (32GB+ recommended for maximum tier)
- NVIDIA GPU (optional, but recommended)

## 🚀 Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/yourusername/multi-agent-system.git
cd multi-agent-system

# Install dependencies
poetry install

# Initialize project structure
poetry run agent-system init
```
### 2. Configure Environment
Edit .env file with your credentials:

```bash
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Optional but recommended
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=your_app_password
```

### 3. Deploy Models
```bash
# Deploy essential models (minimum)
poetry run agent-system deploy-models essential

# Or deploy all models
poetry run agent-system deploy-models maximum
```

### 4. Run the Bot
```bash
# Polling mode (simpler)
poetry run agent-system run --polling

# Or webhook mode
poetry run agent-system run
```

🐳 Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f
```
### 📁 Project Structure
```bash
multi-agent-system/
├── src/agent_system/     # Main package
│   ├── core/            # Core orchestration
│   ├── agents/          # Specialist agents
│   ├── telegram/        # Telegram bot
│   ├── memory/          # Memory management
│   └── automation/      # Automation modules
├── tests/               # Test suite
├── scripts/            # Utility scripts
└── data/              # Data directory
```
### 🎯 Usage Examples
#### Code Generation
```text
User: "Write a Python function to download files from URL"
Bot: Generates complete, tested Python code with error handling
```
### Email Management
```text
User: "Check my emails"
Bot: Fetches emails, prioritizes, suggests replies
```
### Vision Processing
```text
User: [Uploads image] "Extract text from this receipt"
Bot: OCR processing with minicpm-v:8b
```
### Deep Analysis
```text
User: "Analyze this dataset and find patterns"
Bot: Statistical analysis with phi4:14b
```
## ⚙️ Configuration
### Model Tiers
| Tier      | Models     | VRAM  | Use Case                     |
|-----------|------------|-------|------------------------------|
| Essential | 5 models   | 16GB  | Core functionality           |
| Extended  | +6 models  | 24GB  | Vision + Multilingual        |
| Maximum   | +4 models  | 32GB  | High-quality output          |

### Performance Optimization
- Router uses gemma3:1b (<100ms latency)
- Models load on-demand to save memory
- Response caching with Redis
- Async processing for concurrent users

## 🔧 Development
```bash
# Run tests
poetry run pytest

# Format code
poetry run black .
poetry run isort .

# Type checking
poetry run mypy src

# Run linter
poetry run ruff check .
```
## 📊 Monitoring
- Prometheus metrics at `/metrics`
- Structured logging with Loguru
- Performance tracing
- Model usage statistics

## 🤝 Contributing
Contributions are welcome! Please read our contributing guidelines.

## 📄 License
MIT License - see LICENSE file

## 🙏 Acknowledgments
- Ollama for local LLM deployment
- Python Telegram Bot library
- All the open-source models used

## ⚠️ Disclaimer
This system runs LLMs locally. Ensure you have sufficient hardware resources. 
Email features require valid IMAP/SMTP credentials.


## 🚀 Installation & Setup Commands

```bash
# Complete setup from scratch
git clone <repository>
cd multi-agent-system

# Install Poetry if not installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Initialize project
poetry run agent-system init

# Edit .env file
nano .env  # or vim, code, etc.

# Deploy models
poetry run agent-system deploy-models essential

# Run the bot
poetry run agent-system run --polling
```


## 📁Final Project Structure with All Files

```text
multi-agent-system/
│
├── 📄 pyproject.toml                 # Poetry configuration
├── 📄 poetry.lock                   # Locked dependencies
├── 📄 README.md                     # Project documentation
├── 📄 .env.example                  # Template for environment variables
├── 📄 .env                          # Your actual environment variables (create this!)
├── 📄 .gitignore                    # Git ignore rules
├── 📄 docker-compose.yml            # Docker Compose configuration
├── 📄 Dockerfile                    # Docker build instructions
│
├── 📁 scripts/                      # UTILITY SCRIPTS - Deployment & Tools
│   ├── 📄 deploy_models.sh          # MAIN: Model deployment script (bash)
│   ├── 📄 deploy_models.py         # Python version of model deployment
│   ├── 📄 init_ollama.py           # Initialize Ollama connection
│   ├── 📄 test_ollama.py           # Test Ollama connectivity
│   ├── 📄 check_models.py          # Check which models are installed
│   ├── 📄 benchmark_models.py      # Performance testing
│   └── 📄 setup.sh                 # One-command setup script
│
├── 📁 src/                          # SOURCE CODE - Main application
│   └── 📁 agent_system/            # Main package
│       ├── 📄 __init__.py
│       ├── 📄 main.py              # ENTRY POINT: CLI application
│       ├── 📄 config.py            # Configuration management
│       │
│       ├── 📁 core/                # CORE ORCHESTRATION
│       │   ├── 📄 __init__.py
│       │   ├── 📄 orchestrator.py  # MAIN: Coordinates all agents
│       │   ├── 📄 router_agent.py  # Router using gemma3:1b
│       │   └── 📄 specialist_base.py # Base class for all agents
│       │
│       ├── 📁 agents/              # SPECIALIST AGENTS
│       │   ├── 📄 __init__.py
│       │   ├── 📄 code_specialist.py  # Code generation with qwen-coder
│       │   ├── 📄 email_agent.py      # Email automation with phi4
│       │   ├── 📄 vision_agent.py     # Vision with llama3.2-vision
│       │   ├── 📄 analysis_agent.py   # Deep analysis with phi4
│       │   ├── 📄 search_agent.py     # Web search with qwen2.5
│       │   └── 📄 synthesis_agent.py  # Response formatting with aya
│       │
│       ├── 📁 telegram/            # TELEGRAM INTEGRATION
│       │   ├── 📄 __init__.py
│       │   ├── 📄 bot.py           # MAIN: Telegram bot setup
│       │   ├── 📄 handlers.py      # Command and message handlers
│       │   ├── 📄 keyboards.py     # Inline keyboard layouts
│       │   └── 📄 callbacks.py     # Callback query handlers
│       │
│       ├── 📁 memory/              # MEMORY MANAGEMENT
│       │   ├── 📄 __init__.py
│       │   ├── 📄 manager.py       # MAIN: Memory orchestration
│       │   ├── 📄 redis_client.py  # Redis connection
│       │   ├── 📄 vector_store.py  # Vector embeddings storage
│       │   └── 📄 session.py       # User session management
│       │
│       ├── 📁 automation/          # AUTOMATION MODULES
│       │   ├── 📄 __init__.py
│       │   ├── 📄 email_client.py  # Email fetching/sending
│       │   ├── 📄 code_executor.py # Code execution sandbox
│       │   ├── 📄 scheduler.py     # Task scheduler for reminders
│       │   └── 📄 notification.py  # Notification system
│       │
│       ├── 📁 utils/               # UTILITIES
│       │   ├── 📄 __init__.py
│       │   ├── 📄 logger.py        # Logging configuration
│       │   ├── 📄 validators.py    # Input validation
│       │   ├── 📄 helpers.py       # Helper functions
│       │   └── 📄 metrics.py       # Performance metrics
│       │
│       └── 📁 models/              # MODEL REGISTRY
│           ├── 📄 __init__.py
│           ├── 📄 schemas.py       # Pydantic schemas
│           └── 📄 model_registry.py # Model capabilities registry
│
├── 📁 tests/                       # TESTS
│   ├── 📄 __init__.py
│   ├── 📄 conftest.py             # Pytest configuration
│   ├── 📁 unit/                   # Unit tests
│   │   ├── test_router.py
│   │   ├── test_code_agent.py
│   │   └── test_email_agent.py
│   ├── 📁 integration/            # Integration tests
│   │   ├── test_orchestrator.py
│   │   └── test_ollama.py
│   └── 📁 fixtures/               # Test fixtures
│       └── sample_data.py
│
├── 📁 data/                        # DATA DIRECTORY
│   ├── 📁 memory/                 # Persistent memory storage
│   ├── 📁 logs/                   # Application logs
│   ├── 📁 temp/                   # Temporary files
│   └── 📁 models/                 # Local model cache
│
└── 📁 docs/                       # DOCUMENTATION
    ├── 📄 architecture.md         # System architecture
    ├── 📄 api.md                  # API documentation
    ├── 📄 deployment.md           # Deployment guide
    └── 📄 models.md              # Model specifications
```
