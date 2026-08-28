"""
Realistic enterprise-grade sample datasets for local testing, demo walk-throughs, and database seeding.
"""

SAMPLE_JDS = [
    {
        "id": "jd_ai_01",
        "title": "Lead Generative AI Systems Engineer",
        "department": "Autonomous Agent Systems",
        "location_type": "Hybrid (Bengaluru / Remote)",
        "content": """
Job Title: Lead Generative AI Systems Engineer
Department: Autonomous Agent Systems
Experience Required: 5-8 Years | Compensation: $130,000 - $160,000 | Location: Bengaluru / Hybrid

Core Responsibilities:
- Architect, build, and deploy production multi-agent systems using LangChain, LangGraph, and AutoGen.
- Optimize high-throughput LLM inferencing pipelines using Groq Cloud, vLLM, and TensorRT-LLM for sub-100ms response latencies.
- Design low-latency semantic retrieval architectures integrating ChromaDB, FAISS, and Qdrant with hybrid cross-encoder reranking.
- Build end-to-end RAG workflows featuring recursive document chunking, metadata enrichment, and contextual compression.
- Lead a team of 4 ML engineers, establish evaluation benchmarks using RAGAS, and implement guardrails with NeMo.

Must-Have Technical Requirements:
- 5+ years of production Python engineering (FastAPI, AsyncIO, PyDantic, SQLAlchemy).
- 3+ years architecting Vector Search and embeddings systems (SentenceTransformers, BGE, FAISS).
- Proven track record deploying Llama-3, Mistral, or DeepSeek models in private enterprise VPCs.
- Strong knowledge of SQL relational databases (PostgreSQL/SQLite) and NoSQL stores.

Nice-to-Have:
- Direct contributions to open-source agent frameworks (LangGraph, CrewAI).
- Experience with WebRTC audio/video integration for conversational voice agents.
"""
    },
    {
        "id": "jd_cloud_02",
        "title": "Senior Full-Stack Cloud Architect",
        "department": "Platform Engineering",
        "location_type": "Remote",
        "content": """
Job Title: Senior Full-Stack Cloud Architect
Department: Distributed Infrastructure
Experience Required: 6+ Years | Compensation: $120,000 - $145,000 | Location: Remote

Core Responsibilities:
- Design microservices architectures using FastAPI, Next.js, and Dockerized Kubernetes clusters.
- Manage SQL database performance, migrations, schema design, and automated backups (PostgreSQL/SQLAlchemy).
- Implement robust RBAC multi-tenant authentication systems using JWT, OAuth2, and bcrypt.
- Maintain 99.95% system uptime across AWS cloud infrastructure using Terraform.

Must-Have Requirements:
- 6+ years building full-stack applications with Python (FastAPI/Django) and React/Next.js.
- Deep expertise in relational database indexing, query planning, and connection pooling.
- Proven CI/CD pipeline automation experience with GitHub Actions and Docker.
"""
    }
]

SAMPLE_RESUMES = [
    {
        "id": "cand_01",
        "filename": "Aarav_Sharma_Generative_AI_Lead.pdf",
        "candidate_name": "Aarav Sharma",
        "email": "aarav.sharma@domain.com",
        "phone": "+91-9876543210",
        "raw_content": """
Aarav Sharma | Bengaluru, India | aarav.sharma@domain.com | +91-9876543210
GitHub: [github.com/aarav-ai](https://github.com/aarav-ai) | LinkedIn: [linkedin.com/in/aaravsharma-ml](https://linkedin.com/in/aaravsharma-ml)

EXECUTIVE SUMMARY:
Principal AI Engineer with 6.5 years of experience architecting LLM systems, Agentic workflows, and semantic search platforms. Pioneer in implementing cyclic state machines with LangGraph and optimizing Groq inference endpoints for sub-100ms response latencies.

TECHNICAL SKILLS:
- Languages & Core: Python (AsyncIO, PyDantic), TypeScript, SQL, Bash.
- LLM & Agents: LangChain, LangGraph, Groq SDK, vLLM, Ollama, Llama-3, RAGAS, NeMo Guardrails.
- Vector Databases & Retrieval: ChromaDB, FAISS, Qdrant, BM25 Hybrid Search, Cross-Encoders.
- Backend & DevOps: FastAPI, PostgreSQL, SQLite, SQLAlchemy, Docker, Kubernetes, AWS.

PROFESSIONAL EXPERIENCE:
Senior Staff AI Specialist — Cognition Labs, Bengaluru (2022 - Present)
- Engineered an autonomous recruiting agent using LangGraph and Groq, reducing initial screening turnaround times by 78%.
- Scaled local vector retrieval using FAISS and ChromaDB over 500,000+ unstructured technical profiles with sub-50ms query latencies.
- Designed custom RAG evaluation pipelines with RAGAS, maintaining 94% context precision and 91% faithfulness scores.
- Mentored a squad of 5 AI engineers, instituted strict PyDantic validation layers, and managed CI/CD deployments.

Machine Learning Engineer — HyperScale Data Systems, Hyderabad (2019 - 2022)
- Built semantic resume parsing microservices in FastAPI extracting structured JSON schemas from PDFs and DOCXs.
- Spearheaded SQL database optimization, reducing query execution times across 2 million application records by 40%.
- Deployed BERT and SentenceTransformer embeddings pipelines across distributed AWS EC2 clusters.

EDUCATION:
- B.Tech in Computer Science & Engineering, IIT Madras (2015 - 2019) | CGPA: 8.9/10
""",
        "swot": {
            "strengths": [
                "Exceptional LangGraph and Groq practical experience matching active JD requirements.",
                "Deep background in local vector search (ChromaDB/FAISS) and hybrid retrieval architectures.",
                "Demonstrated engineering leadership (mentored 5 engineers) and robust CS fundamentals (IIT Madras)."
            ],
            "weaknesses": [
                "Primary focus on Python/AI backends; minimal frontend React experience.",
                "Notice period is currently 45 days (manageable via buyout)."
            ],
            "opportunities": [
                "Can immediately take ownership of the Core Agentic Workflow Engine.",
                "Capable of establishing internal RAGAS evaluation and benchmarking frameworks."
            ],
            "threats": [
                "Holds competing offers from AI startups; requires an agile decision cycle."
            ]
        }
    },
    {
        "id": "cand_02",
        "filename": "Rohan_Verma_Junior_ML_Dev.pdf",
        "candidate_name": "Rohan Verma",
        "email": "rohan.v@domain.com",
        "phone": "+91-9123456780",
        "raw_content": """
Rohan Verma | Hyderabad, India | rohan.v@domain.com
GitHub: [github.com/rohan-v](https://github.com/rohan-v)

SUMMARY:
Junior Machine Learning Engineer with 2 years of experience building basic prompt chains, web scraping scripts, and standard Scikit-Learn pipelines.

TECHNICAL SKILLS:
Python, Pandas, NumPy, Scikit-Learn, Streamlit, Basic OpenAI APIs, SQL.

EXPERIENCE:
Junior Python Developer — InfoTech Solutions, Hyderabad (2023 - Present)
- Built basic Streamlit dashboards for reporting sales analytics.
- Integrated standard OpenAI wrapper endpoints for simple summarization tasks.
- Cleaned tabular data and managed SQLite relational tables.

EDUCATION:
- B.E. in Information Technology, Osmania University (2019 - 2023)
""",
        "swot": {
            "strengths": ["Strong foundational Python and basic SQL competency."],
            "weaknesses": ["Lacks experience in multi-agent systems (LangGraph), Groq inference, and production vector indices."],
            "opportunities": ["Strong candidate for a Junior or Associate Developer role with mentoring."],
            "threats": ["Does not meet the minimum 5-year requirement for the Lead Engineer role."]
        }
    }
]
