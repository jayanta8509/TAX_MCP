# Tax Filing Assistant (1040NR) with MCP

A context-aware AI assistant designed to help non-resident clients file their 1040NR tax returns. This system leverages the **Model Context Protocol (MCP)** to securely access client data and **Redis** for maintaining conversation memory.

## 🚀 Features

- **Intelligent Tax Assistance**: specialized prompt for 1040NR filing workflows.
- **MCP Integration**: Uses `langchain-mcp-adapters` to connect LLMs with a MySQL database via MCP tools.
- **Context Awareness**: Remembers previous interactions, tax forms discussed, and specific client details using Redis.
- **Privacy Focused**: Built-in rules to prevent leaking internal Client IDs or Reference types.
- **Dual Client Support**: Handles both "Company" and "Individual" client types with dynamic schema mapping.

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI
- **AI/LLM**: LangChain, OpenAI GPT-4o-mini
- **Database**: MySQL (via MCP tools)
- **Memory**: Redis (12-hour TTL)
- **Protocol**: Model Context Protocol (MCP)

## 📋 Prerequisites

- Python 3.10+
- Redis Server (local or cloud)
- MySQL Database
- OpenAI API Key

## ⚙️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd TAX_MCP
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv env
   # Windows
   .\env\Scripts\activate
   # Linux/Mac
   source env/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 🔧 Configuration

Create a `.env` file in the root directory with the following variables:

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Database (MySQL)
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=your_db_name
DB_PORT=3306

# Redis
HOST=localhost
PORT=6379
PASSWORD=your_redis_password
```

## 🏃‍♂️ Usage

1. **Start the FastAPI Server**
   ```bash
   python app.py
   ```
   The server will start on `http://0.0.0.0:8002`.

2. **API Endpoint**
   - **URL**: `/chat/agent`
   - **Method**: `POST`
   - **Body**:
     ```json
     {
       "user_id": "user123",
       "client_id": 3,
       "reference": "company",
       "query": "What is my current account status?",
       "use_agent": true
     }
     ```

## 📂 Project Structure

- `app.py`: FastAPI application entry point and API route handlers.
- `client.py`: Core agent logic, MCP client setup, and Redis memory management.
- `mcp_functions.py`: Defines the MCP tools and database queries.
- `connection.py`: Database connection helper.
- `requirements.txt`: Python dependencies.

## 🛡️ Privacy & Security

- **Internal IDs**: The system is configured to never expose `client_id` or `reference` type in responses.
- **Memory TTL**: Conversation history in Redis expires automatically after 12 hours.
