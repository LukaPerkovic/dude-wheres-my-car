# Dude, Where's My Car?

The inspiration for the project name comes from the 2000 comedy film feature Ashton Kutcher and Seann William Scott.
The underlying context and data used within the system are generated to reflect the fictional, futuristig world of Cyberpunk.

The repository contains a multi-agent system designed to handle conversational queries, parking reservations, and human-in-the-loop approval workflows using Retrieval-Augumented-Generation (RAG).

## Architecture

The system utlizes a graph-based state machine to coordinate interactions between various AI agents, retrieval mechanisms, and external tools.

Core architectural components include:
* **State Management**: Built on directed graph architecture to maintain conversation history and agent states.
* **Model Context Protocol (MPC)**: A dedidcated server provides agents with safe, standardized access to underlying tools and database operations.
* **Retrieval-Augmented Generation (RAG)**: Indexes static markdown documents and dynamic data to answer user queries accuretly.
* **Relational Database**: Currently uses SQLite for local spaces, users, and reservation states i.e. checkpointing.
* **CI/CID**: Unit tests and code lint ran on PRs in GitHub actions.

## Agent and Server Logic

The application routing is determined by user intent, passing state through dedicated nodes.
    <p align="center">
    <img src="artifacts/agent_graph.png" width="800" alt="Agent Graph">
    </p>

* **Chatbot Agent**: Acts as the primary entry point. It analyzes user input to determine if the query requires general information, a specific reservation action, or admin intervention.
    <p align="center">
    <img src="artifacts/static_chatbot_rag.png" width="800" alt="Chatbot Interaction">
    </p>
* **Guardrails**: Any prompt injection, off-topic attempts or PII request will activate the guardrails and user request will be refused.
    <p align="center">
    <img src="artifacts/PII_request_denied.png" width="800" alt="PII/Injection refusal">
    </p>
* **RAG Engine**: If the query is informational (e.g. location, booking process), the chatbot routes the request to the RAG query engine to fetch context from the indexed documentation. If user requuires actual and factual info, router directs it to dynamic RAG.
    <p align="center">
    <img src="artifacts/dynamic_chatbot_rag.png" width="800" alt="RAG Interaction">
    </p>
* **Reservation Agent**: Invoked when the user intent involves booking a spaces. It gathers necesssary parameters (vehicle details, dates) and utilizes MCP tools to check availability and create a reservation.
    <p align="center">
    <img src="artifacts/reservation_request.png" width="800" alt="Reservation request">
    </p>
* **Approval/Human-in-the-loop (HITL) Agent**: Handles reservations that require manual oversight. It pauses the agentic workflow to await external administrative approval or denual before proceeding.
    <p align="center">
    <img src="artifacts/admin_request_portal.png" width="800" alt="Admin Approval Portal">
    </p>
* **MCP Server:** Operates independently to expose determininstic functons (e.g. database queries, data mutations) as callable tools for the LLM agents, ensuring a strict boundary between reasoning and execution. Speficially speaking, the MCP server is in charge for writing reservation data to a file. Note: It's an append style and write only.


## System Evaluation

To maintain the quality of agentic workflows., the system includes performance evaluations and accuracy benchmarks.

<details>
<summary>View Load Testing Results (Locust)</summary>

The system was tested for concurrent agent interactions. Note: The LLM models were Haiku grade.
![Locust Statistic](artifacts/locust_statistics.png)
![Locust Chart](artifacts/locust_chart.png)

</details>

<details>
<summary>View RAG Evaluation Results</summary>

Metrics showing retrieval accuracy and faithfulness.
![RAG Evaluation](artifacts/rag_eval.png)

</details>

## Setup and Deployment Guidelines

**Prerequisites**
* Python 3.13+
* Docker and Docker Compose
* `uv` package manager


**Local Installation**
1. Clone the repository and navigate to the project root.
2. Install dependencies using `uv`:
    ```bash
    uv sync
    ```
3. Set up the environment variables. Create a `.env` file in the root directory and provide your required API keys (Anthropic API key, database paths, admin username and password)

**Running the System**

Use Docker Compose:
```bash
docker compose up --build
```

This will spin up the database, populate data automatically using data seeding script `script/init.py`, start MCP server and application server. Waiting time ~10 minutes. If it's the first time, due to library installs, ~20-30 minutes. It will enable the services on port 8080, so navigate with your browser. To use the API, make POST reques to `/chat` endpoint providing a JSON structure with `message` and `thread_id` keys, or curl method. Alternatvely, to test via Swagger UI navigate to `/docs` endpoint, to see the admin portal navigate to `/admin` endpoint and provide the username and password.


## Project Structure

* `src/agents/`: Contains the logic for the chatbot, reservation and HITL agents.
* `src/graph/`: Defines the nodes, edges, and overall state graph workflow.
* `src/mcp_server`: Contains the Model Context Protocol server and client implementations.
* `src/rag/`: Logic for document indexing, retrieval, query engine and guardrails.
* `data/`: Static markdown documentation, dynamic seed SQL scripts, and the SQLite database.
* `evaluation`: Scripts for load testing and RAG evaluation.

## Future Work

Several architectural decisions were made to prioritze local development convenience and **cost control**. Future iteration of this project should consider the following improvements.

* **Database Migration:**  The project currently uses SQLLite for setup convenience.  Since we do checkpointing *and* SQL dynamic data retrieval, we had to address the concurrency issues with additional configs. For a production environment, this should be migrated to an open-source PostgreSQL database. Similarly, ChromaDB is alike SQLite, and good choice for first iterations, however migrations to Postgres' `pgvector` can be considered.
* **Dataset Expansion**: The Current golden dataset for testing is kept small to minimize LLM usage costs. Scaling this dataset is required for better evaluation pipeline. Also, we are of opinion that lower RAG score is impacted by this reason as well. Also the LLM judge was of lower quality (Haiku) to save money. Ideally it should be better quality (e.g. sonnet grade)
* **More robust RAG evaluation**: Another reason for lower scores might be that for our RAG eval use both static and dynamic data, while our implementation is gravitating toward vector evaluation. Additionally, a fragile piece of this eval is also a router. If router doesn't do it's work properly, the golden dataset row will arrive in front of wrong evaluator (SQL to vector and vice versa).
* **LLM Evaluation**: RAGAS and automated LLM evaluations are limited due to token API costs and should be implemented in enterprise settings.
* **Advanced RAG Features**: Users input query rewritting is currently omiited from the RAG pipeline to (yet again) save on costs. Implementing a query expansion or rewriting step would improve retrieval accuracy. 
* **Additional CI/CD**: A RAG evaluation trigger was attempted on merge requests pertaining to the code related wit RAG (`src/rag` and `src/config`) but was deemed to expensive. In serious environments it should included.
8 **PII Anonymization**: As of now, only PII protection is guardrails module. This module blocks any attempts that include PII, but in case we needed to return some reponses to users that *could* include PII, we can leverage Presidio. Unfortunately, choosing a fictional universe, locked us out of built-in anoymization techniques, and was concluded that any effort to rollback the data seeding or custom implementing filter was too much for this stage of the project.
* **Cloud Deployment (AWS, GCP, Azure)**: The setup is hefty. Deploying this to cloud would go above the free tiers, and incur costs. This as well can be reserved when enterprise sponsorship is acquired.
