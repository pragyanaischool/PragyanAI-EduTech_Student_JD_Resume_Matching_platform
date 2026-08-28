"""
Realistic enterprise-grade sample datasets: 10 Job Descriptions and 10 Candidate CVs.
"""

SAMPLE_JDS = [
    {
        "id": "jd_01",
        "title": "Lead Generative AI Engineer",
        "department": "Autonomous Agent Systems",
        "location_type": "Hybrid (Bengaluru / Remote)",
        "content": """Job Title: Lead Generative AI Engineer
Department: Autonomous Agent Systems
Experience Required: 5-8 Years | Compensation: $130,000 - $160,000 | Location: Bengaluru / Hybrid

Responsibilities:
- Architect and deploy production multi-agent systems using LangChain, LangGraph, and AutoGen.
- Optimize high-throughput LLM inferencing pipelines using Groq Cloud, vLLM, and TensorRT-LLM for sub-100ms latency.
- Design low-latency semantic retrieval architectures integrating ChromaDB, FAISS, and Qdrant with hybrid cross-encoder reranking.
- Lead a squad of 4 ML engineers, establish evaluation benchmarks using RAGAS, and enforce NeMo guardrails.

Requirements:
- 5+ years of production Python engineering (FastAPI, AsyncIO, Pydantic, SQLAlchemy).
- 3+ years architecting Vector Search and dense embeddings (SentenceTransformers, BGE, FAISS).
- Proven track record deploying Llama-3, Mistral, or DeepSeek models in private VPCs.
- Strong knowledge of PostgreSQL/SQLite and Vector DBMS."""
    },
    {
        "id": "jd_02",
        "title": "Senior Full-Stack Cloud Architect",
        "department": "Platform Engineering",
        "location_type": "Remote",
        "content": """Job Title: Senior Full-Stack Cloud Architect
Department: Platform Engineering
Experience Required: 6+ Years | Compensation: $125,000 - $150,000 | Location: Remote

Responsibilities:
- Design microservices architectures using FastAPI, Next.js, and Dockerized Kubernetes clusters.
- Manage SQL database performance, migrations, schema design, and automated backups (PostgreSQL/SQLAlchemy).
- Implement robust RBAC multi-tenant authentication systems using JWT, OAuth2, and bcrypt.
- Maintain 99.95% system uptime across AWS cloud infrastructure using Terraform.

Requirements:
- 6+ years building full-stack applications with Python (FastAPI/Django) and React/Next.js.
- Deep expertise in relational database indexing, query planning, and connection pooling.
- Proven CI/CD pipeline automation experience with GitHub Actions and Docker."""
    },
    {
        "id": "jd_03",
        "title": "Staff MLOps & Platform Engineer",
        "department": "Data & ML Platform",
        "location_type": "Onsite (Bengaluru)",
        "content": """Job Title: Staff MLOps & Platform Engineer
Department: Data & ML Platform
Experience Required: 6-10 Years | Compensation: $140,000 - $175,000 | Location: Bengaluru

Responsibilities:
- Build and operate enterprise ML deployment infrastructure using Kubeflow, MLflow, and Triton Inference Server.
- Implement automated model training, validation, and continuous deployment pipelines (CI/CD/CT).
- Scale vector search clusters (Milvus/Qdrant) and monitor real-time inference latency and model drift.
- Optimize GPU resource utilization across multi-node Kubernetes clusters on AWS/GCP.

Requirements:
- 6+ years in DevOps/MLOps with deep Kubernetes, Helm, and Terraform expertise.
- Hands-on experience with Triton Inference Server, vLLM, and Ray Serve.
- Strong proficiency in Python, Go, and Linux kernel performance tuning."""
    },
    {
        "id": "jd_04",
        "title": "Senior Computer Vision Engineer",
        "department": "Edge AI & Vision Systems",
        "location_type": "Hybrid (Hyderabad / Remote)",
        "content": """Job Title: Senior Computer Vision Engineer
Department: Edge AI & Vision Systems
Experience Required: 4-7 Years | Compensation: $115,000 - $145,000 | Location: Hybrid

Responsibilities:
- Design real-time object detection, segmentation, and defect verification models using PyTorch and OpenCV.
- Quantize and deploy vision models to edge devices (NVIDIA Jetson, TensorRT, ONNX Runtime).
- Construct automated synthetic data generation pipelines for training edge models.
- Collaborate with embedded systems teams for camera sensor driver integration.

Requirements:
- 4+ years developing deep learning models with PyTorch/TensorFlow for computer vision.
- Strong expertise with YOLO architectures, Mask R-CNN, and ViTs.
- Production experience with C++, Python, OpenCV, and TensorRT."""
    },
    {
        "id": "jd_05",
        "title": "Principal Data Engineer",
        "department": "Enterprise Analytics & Lakehouse",
        "location_type": "Remote",
        "content": """Job Title: Principal Data Engineer
Department: Enterprise Analytics & Lakehouse
Experience Required: 8+ Years | Compensation: $150,000 - $185,000 | Location: Remote

Responsibilities:
- Architect distributed real-time streaming and batch lakehouses using Apache Spark, Kafka, and Delta Lake.
- Formulate data contracts, lineage tracking, and automated data quality checks with Great Expectations.
- Optimize petabyte-scale data pipelines in Snowflake and AWS Athena.
- Mentor a team of 6 data engineers and establish enterprise data modeling standards.

Requirements:
- 8+ years building high-throughput data platforms with Spark, PySpark, and SQL.
- Deep expertise in dbt, Apache Airflow, Kafka, and Snowflake/BigQuery.
- Advanced knowledge of dimensional modeling, data governance, and partitioning strategies."""
    },
    {
        "id": "jd_06",
        "title": "Backend Python / FastAPI Specialist",
        "department": "Core Platform Engineering",
        "location_type": "Remote",
        "content": """Job Title: Backend Python / FastAPI Specialist
Department: Core Platform Engineering
Experience Required: 3-5 Years | Compensation: $90,000 - $120,000 | Location: Remote

Responsibilities:
- Develop high-concurrency RESTful and WebSocket microservices using FastAPI and AsyncIO.
- Implement transactional business workflows with SQLAlchemy ORM, Alembic, and PostgreSQL.
- Construct distributed task queues and caching layers with Redis and Celery.
- Write thorough unit and integration test suites achieving >85% test coverage.

Requirements:
- 3+ years specialized in Python 3.10+, FastAPI, and Pydantic.
- Strong SQL proficiency including query optimization, index tuning, and ACID transactions.
- Experience with Docker, Redis, Celery, and Pytest."""
    },
    {
        "id": "jd_07",
        "title": "Cloud Security & DevSecOps Engineer",
        "department": "Information Security",
        "location_type": "Hybrid (Bengaluru)",
        "content": """Job Title: Cloud Security & DevSecOps Engineer
Department: Information Security
Experience Required: 5-8 Years | Compensation: $120,000 - $155,000 | Location: Bengaluru

Responsibilities:
- Integrate automated SAST, DAST, and container security scanning into GitHub Actions CI/CD pipelines.
- Implement Zero-Trust cloud network security, IAM least-privilege policies, and AWS KMS key rotation.
- Perform automated vulnerability management and penetration testing across cloud infrastructure.
- Lead SOC2 Type II, ISO 27001, and GDPR compliance audits.

Requirements:
- 5+ years in Cloud Security (AWS/Azure) and DevSecOps tooling (Trivy, Snyk, SonarQube, OPA).
- Certifications like AWS Certified Security Specialty or CISSP preferred.
- Strong scripting skills in Python and Bash."""
    },
    {
        "id": "jd_08",
        "title": "Lead Product Manager - AI & Data",
        "department": "Product Management",
        "location_type": "Hybrid (Bengaluru / Mumbai)",
        "content": """Job Title: Lead Product Manager - AI & Data
Department: Product Management
Experience Required: 6-9 Years | Compensation: $135,000 - $165,000 | Location: Hybrid

Responsibilities:
- Define product strategy, roadmap, and PRDs for enterprise Generative AI and analytics SaaS tools.
- Partner with ML engineers to balance model accuracy, latency trade-offs, and compute costs.
- Conduct user research, define north-star metrics, and run A/B experimentation frameworks.
- Drive GTM alignment with sales, solutions engineering, and customer success teams.

Requirements:
- 6+ years in technical product management with at least 2+ years on AI/ML/Data products.
- Deep comprehension of LLM capabilities, RAG pipelines, and conversational interfaces.
- Proven track record scaling B2B SaaS products from 0 to 1."""
    },
    {
        "id": "jd_09",
        "title": "Embedded Linux & Firmware Engineer",
        "department": "Hardware Systems",
        "location_type": "Onsite (Bengaluru)",
        "content": """Job Title: Embedded Linux & Firmware Engineer
Department: Hardware Systems
Experience Required: 4-8 Years | Compensation: $110,000 - $140,000 | Location: Bengaluru

Responsibilities:
- Develop Linux device drivers (I2C, SPI, UART, PCIe) and Board Support Packages (BSP) using Yocto.
- Write low-level bare-metal and FreeRTOS firmware for ARM Cortex-M microcontrollers.
- Debug hardware-software interfaces using logic analyzers, oscilloscopes, and JTAG.
- Optimize boot-up time and power consumption for battery-operated edge hardware.

Requirements:
- 4+ years in C/C++ embedded systems, Linux kernel driver development, and U-Boot.
- Proficiency with Yocto Project / Buildroot and ARM architecture.
- Hands-on experience reading schematics and debugging hardware buses."""
    },
    {
        "id": "jd_10",
        "title": "Junior Machine Learning Engineer",
        "department": "AI Research & Development",
        "location_type": "Hybrid (Hyderabad / Remote)",
        "content": """Job Title: Junior Machine Learning Engineer
Department: AI Research & Development
Experience Required: 1-3 Years | Compensation: $65,000 - $85,000 | Location: Hybrid

Responsibilities:
- Assist in preprocessing, cleaning, and tokenizing large multi-modal datasets.
- Implement baseline machine learning models using Scikit-Learn, XGBoost, and PyTorch.
- Build interactive internal demonstration dashboards using Streamlit and Gradio.
- Maintain data pipelines and assist in documenting experiment runs with Weights & Biases.

Requirements:
- 1-3 years of Python experience (Pandas, NumPy, Scikit-Learn, PyTorch).
- Solid theoretical understanding of supervised, unsupervised learning, and transformer basics.
- Bachelor's degree in Computer Science, Data Science, or related engineering discipline."""
    }
]

SAMPLE_RESUMES = [
    {
        "id": "cv_01",
        "filename": "Aarav_Sharma_Generative_AI_Lead.pdf",
        "candidate_name": "Aarav Sharma",
        "email": "aarav.sharma@domain.com",
        "phone": "+91-9876543210",
        "target_role": "Lead Generative AI Engineer",
        "raw_content": """Aarav Sharma | Bengaluru, India | aarav.sharma@domain.com | +91-9876543210 | github.com/aarav-ai | linkedin.com/in/aaravsharma-ml

EXECUTIVE SUMMARY:
Principal AI Engineer with 6.5 years of experience architecting production LLM systems, Agentic workflows, and semantic search platforms. Expert in cyclic state machines with LangGraph, hybrid vector search (ChromaDB, FAISS), and Groq inference acceleration (sub-80ms latencies).

TECHNICAL SKILLS:
- Languages & Frameworks: Python (AsyncIO, Pydantic), TypeScript, FastAPI, PyTorch
- AI & Multi-Agent: LangChain, LangGraph, AutoGen, Groq SDK, vLLM, RAGAS, NeMo Guardrails, Llama-3
- Vector Stores & Databases: ChromaDB, FAISS, Qdrant, PostgreSQL, SQLAlchemy, Redis
- DevOps & Cloud: Docker, Kubernetes, AWS (EC2, S3, ECS), CI/CD (GitHub Actions)

PROFESSIONAL EXPERIENCE:
Senior Staff AI Specialist — Cognition Labs, Bengaluru (2022 - Present)
- Engineered an autonomous recruiting agent using LangGraph and Groq, reducing initial screening turnaround times by 78%.
- Scaled local vector retrieval using FAISS and ChromaDB over 500,000+ unstructured technical profiles with sub-50ms query latencies.
- Designed custom RAG evaluation pipelines with RAGAS, maintaining 94% context precision and 91% faithfulness scores.
- Mentored a squad of 5 AI engineers, instituted strict Pydantic validation layers, and managed CI/CD deployments.

Machine Learning Engineer — HyperScale Data Systems, Hyderabad (2019 - 2022)
- Built semantic resume parsing microservices in FastAPI extracting structured JSON schemas from PDFs and DOCXs.
- Spearheaded SQL database optimization, reducing query execution times across 2 million application records by 40%.
- Deployed BERT and SentenceTransformer embeddings pipelines across distributed AWS EC2 clusters.

EDUCATION:
- B.Tech in Computer Science & Engineering, IIT Madras (2015 - 2019) | CGPA: 8.9/10""",
        "swot": {
            "strengths": ["Deep LangGraph and Groq production background", "Local vector search scaling mastery (FAISS/ChromaDB)", "Strong CS fundamentals (IIT Madras)"],
            "weaknesses": ["Primary focus on Python backends; limited React/Next.js frontend experience"],
            "opportunities": ["Can lead multi-agent systems and RAG benchmarking architectures"],
            "threats": ["Holds competing enterprise offers"]
        }
    },
    {
        "id": "cv_02",
        "filename": "Priya_Nair_Cloud_Architect.pdf",
        "candidate_name": "Priya Nair",
        "email": "priya.nair@domain.com",
        "phone": "+91-9876543211",
        "target_role": "Senior Full-Stack Cloud Architect",
        "raw_content": """Priya Nair | Pune, India | priya.nair@domain.com | +91-9876543211 | github.com/priyanair-cloud

EXECUTIVE SUMMARY:
Senior Full-Stack Cloud Architect with 7 years of experience building resilient microservices, high-traffic web applications, and multi-tenant cloud platforms. Specialized in FastAPI, React/Next.js, PostgreSQL optimization, and AWS Kubernetes infrastructure.

TECHNICAL SKILLS:
- Backend: Python (FastAPI, Django), Node.js, SQLAlchemy, Alembic, Celery, Redis
- Frontend: React.js, Next.js, TypeScript, Tailwind CSS
- Cloud & Infrastructure: AWS (EKS, RDS, S3, CloudFront), Terraform, Docker, Kubernetes, Helm
- Databases: PostgreSQL, MongoDB, Redis, SQLite

PROFESSIONAL EXPERIENCE:
Lead Platform Architect — CloudMatrix Technologies, Pune (2021 - Present)
- Architected enterprise multi-tenant SaaS backend using FastAPI and Next.js, serving 300,000+ monthly active users.
- Reduced PostgreSQL query latency by 55% using read-replicas, connection pooling with PgBouncer, and composite indexing.
- Implemented full RBAC with JWT token rotation and OAuth2 multi-provider social sign-in.
- Automated multi-region AWS infrastructure deployment using Terraform and GitHub Actions.

Senior Software Engineer — Zenith Tech Solutions, Bengaluru (2018 - 2021)
- Developed REST microservices in FastAPI handling 5,000+ requests per second.
- Migrated monolithic Django backend into containerized Docker services orchestrated on AWS EKS.

EDUCATION:
- B.E. in Information Technology, Pune Institute of Computer Technology (2014 - 2018) | First Class with Distinction""",
        "swot": {
            "strengths": ["7+ years building enterprise full-stack systems", "Expertise in PostgreSQL optimization and AWS EKS", "Strong architectural discipline"],
            "weaknesses": ["Limited hands-on fine-tuning of large language models"],
            "opportunities": ["Ideal leader for scalable SaaS cloud and platform engineering"],
            "threats": ["Expects remote-only arrangement"]
        }
    },
    {
        "id": "cv_03",
        "filename": "Vikram_Mehta_MLOps_Engineer.pdf",
        "candidate_name": "Vikram Mehta",
        "email": "vikram.mehta@domain.com",
        "phone": "+91-9876543212",
        "target_role": "Staff MLOps & Platform Engineer",
        "raw_content": """Vikram Mehta | Bengaluru, India | vikram.mehta@domain.com | +91-9876543212 | github.com/vmehta-mlops

EXECUTIVE SUMMARY:
Staff MLOps and Infrastructure Engineer with 8 years of experience deploying and scaling machine learning inference platforms. Expert in Kubernetes, Triton Inference Server, vLLM, and distributed Ray clusters.

TECHNICAL SKILLS:
- MLOps & Orchestration: Kubeflow, MLflow, Triton Inference Server, vLLM, Ray Serve, Airflow
- Containerization & Cloud: Docker, Kubernetes, Helm, Terraform, AWS, GCP
- Languages: Python, Go, Bash, C++
- Monitoring & Vector DBs: Prometheus, Grafana, Milvus, Qdrant, Weights & Biases

PROFESSIONAL EXPERIENCE:
Staff MLOps Architect — NeuralScale Systems, Bengaluru (2021 - Present)
- Built Triton and vLLM GPU serving cluster on Kubernetes, reducing p99 model inference latency from 320ms to 45ms.
- Scaled distributed Qdrant vector database to 10M+ embeddings with sub-25ms retrieval.
- Automated continuous model training (CT) pipelines using Kubeflow and GitHub Actions.

DevOps & Infrastructure Engineer — DataCore Global, Hyderabad (2017 - 2021)
- Managed 50+ Kubernetes nodes on AWS, cutting cloud compute costs by 35% using AWS Spot Instances.
- Implemented Prometheus and Grafana telemetry dashboards tracking real-time GPU memory, temperature, and throughput.

EDUCATION:
- M.Tech in Software Systems, BITS Pilani (2019 - 2021)
- B.Tech in Computer Science, NIT Warangal (2013 - 2017)""",
        "swot": {
            "strengths": ["Deep GPU serving optimization (Triton/vLLM)", "8 years Kubernetes and cloud infrastructure mastery"],
            "weaknesses": ["Less focus on application frontend development"],
            "opportunities": ["Can establish company-wide GPU clusters and inference orchestration"],
            "threats": ["High compensation expectations"]
        }
    },
    {
        "id": "cv_04",
        "filename": "Ananya_Deshmukh_Computer_Vision.pdf",
        "candidate_name": "Ananya Deshmukh",
        "email": "ananya.d@domain.com",
        "phone": "+91-9876543213",
        "target_role": "Senior Computer Vision Engineer",
        "raw_content": """Ananya Deshmukh | Hyderabad, India | ananya.d@domain.com | +91-9876543213 | github.com/ananya-vision

EXECUTIVE SUMMARY:
Computer Vision Engineer with 5.5 years of experience building real-time object detection, PCB surface defect inspection, and video analytics algorithms. Skilled in PyTorch, TensorRT, OpenCV, and embedded NVIDIA Jetson deployment.

TECHNICAL SKILLS:
- Computer Vision: OpenCV, YOLOv8/v10, Mask R-CNN, Vision Transformers (ViT), Segment Anything (SAM)
- Deep Learning: PyTorch, TorchScript, ONNX Runtime, TensorRT, CUDA
- Languages & Tools: Python, C++, Linux, Docker, Git

PROFESSIONAL EXPERIENCE:
Senior Computer Vision Engineer — Apex Vision AI, Hyderabad (2021 - Present)
- Developed an automated PCB component misalignment and solder bridge defect detection system achieving 99.2% accuracy.
- Optimized YOLOv8 models using TensorRT INT8 quantization, achieving 65 FPS on NVIDIA Jetson Orin Nano.
- Built automated image annotation and synthetic data augmentation workflows with Blender and OpenCV.

Computer Vision Developer — RoboSense Technologies, Bengaluru (2019 - 2021)
- Implemented multi-camera tracking and pose estimation for factory floor worker safety compliance.
- Deployed real-time edge vision algorithms on Raspberry Pi and NVIDIA Jetson TX2.

EDUCATION:
- M.S. in Electrical & Computer Engineering, IIIT Hyderabad (2017 - 2019)
- B.E. in Electronics & Communication, Osmania University (2013 - 2017)""",
        "swot": {
            "strengths": ["Proven track record in industrial PCB defect verification", "TensorRT quantization and embedded edge deployment"],
            "weaknesses": ["Limited exposure to NLP and conversational LLM pipelines"],
            "opportunities": ["Directly aligns with computer vision inspection and edge AI initiatives"],
            "threats": ["Prefers hybrid or onsite setup in Hyderabad"]
        }
    },
    {
        "id": "cv_05",
        "filename": "Suresh_Ranganathan_Principal_Data_Eng.pdf",
        "candidate_name": "Suresh Ranganathan",
        "email": "suresh.r@domain.com",
        "phone": "+91-9876543214",
        "target_role": "Principal Data Engineer",
        "raw_content": """Suresh Ranganathan | Chennai, India | suresh.r@domain.com | +91-9876543214 | github.com/sureshr-data

EXECUTIVE SUMMARY:
Principal Data Engineer with 9 years of experience architecting petabyte-scale data platforms, distributed streaming systems, and lakehouses. Expert in Apache Spark, Kafka, Delta Lake, Snowflake, and dbt.

TECHNICAL SKILLS:
- Big Data & Lakehouse: Apache Spark, PySpark, Delta Lake, Snowflake, Databricks, Apache Iceberg
- Streaming & Orchestration: Apache Kafka, Apache Flink, Airflow, dbt
- Databases & Cloud: PostgreSQL, AWS (S3, EMR, Redshift, Glue), BigQuery
- Languages: Python, Scala, SQL, Bash

PROFESSIONAL EXPERIENCE:
Principal Data Architect — Global FinAnalytics, Chennai (2020 - Present)
- Designed real-time transaction processing lakehouse handling 40,000 events/second using Kafka, Spark Structured Streaming, and Delta Lake.
- Spearheaded Snowflake migration, reducing corporate query execution costs by $180,000 annually.
- Led data governance, lineage tracking, and automated validation tests using dbt and Great Expectations.

Lead Data Engineer — Quantix Insights, Bengaluru (2016 - 2020)
- Built enterprise data warehouses aggregating financial metrics across 15 disparate CRM and ERP systems.
- Optimized PySpark batch jobs reducing nightly ETL window from 6 hours to 85 minutes.

EDUCATION:
- B.Tech in Information Technology, Anna University, Chennai (2012 - 2016) | Gold Medalist""",
        "swot": {
            "strengths": ["9 years enterprise big data and lakehouse leadership", "Deep Spark, Kafka, and Snowflake cost optimization expertise"],
            "weaknesses": ["Minimal experience with PyTorch/TensorFlow modeling"],
            "opportunities": ["Can establish world-class enterprise data platform governance"],
            "threats": ["Notice period is 60 days"]
        }
    },
    {
        "id": "cv_06",
        "filename": "Kavita_Patel_FastAPI_Backend.pdf",
        "candidate_name": "Kavita Patel",
        "email": "kavita.patel@domain.com",
        "phone": "+91-9876543215",
        "target_role": "Backend Python / FastAPI Specialist",
        "raw_content": """Kavita Patel | Ahmedabad, India | kavita.patel@domain.com | +91-9876543215 | github.com/kavita-dev

EXECUTIVE SUMMARY:
Backend Python Engineer with 4 years of experience specializing in FastAPI, AsyncIO, SQLAlchemy ORM, and high-performance microservices. Passionate about clean code, test-driven development, and database optimization.

TECHNICAL SKILLS:
- Languages: Python 3.11+, SQL, JavaScript
- Frameworks & Libraries: FastAPI, Pydantic, SQLAlchemy, Alembic, Celery, Pytest
- Databases & Caching: PostgreSQL, Redis, SQLite, MongoDB
- DevOps & Tools: Docker, Git, GitHub Actions, Linux, Postman

PROFESSIONAL EXPERIENCE:
Backend Software Engineer — FinFlow Solutions, Ahmedabad (2022 - Present)
- Developed high-throughput REST APIs using FastAPI and AsyncIO serving 8M daily requests.
- Integrated Celery worker queues with Redis broker for asynchronous PDF generation and email dispatches.
- Wrote automated test suites using Pytest with 92% code coverage and integrated CI/CD checks.

Junior Python Developer — ByteCraft Systems, Vadodara (2020 - 2022)
- Built internal CRUD microservices using FastAPI, SQLAlchemy, and PostgreSQL.
- Implemented OAuth2 JWT authentication and password hashing with bcrypt.

EDUCATION:
- B.E. in Computer Engineering, Gujarat Technological University (2016 - 2020) | CGPA: 8.7/10""",
        "swot": {
            "strengths": ["Specialized in high-concurrency FastAPI & AsyncIO", "High testing discipline (92% Pytest coverage)"],
            "weaknesses": ["Moderate experience in vector search and complex agent frameworks"],
            "opportunities": ["Quickly productive in core backend and API development"],
            "threats": ["Requires mentorship for complex multi-agent LLM systems"]
        }
    },
    {
        "id": "cv_07",
        "filename": "Rohan_Verma_Junior_ML_Dev.pdf",
        "candidate_name": "Rohan Verma",
        "email": "rohan.v@domain.com",
        "phone": "+91-9123456780",
        "target_role": "Junior Machine Learning Engineer",
        "raw_content": """Rohan Verma | Hyderabad, India | rohan.v@domain.com | +91-9123456780 | github.com/rohan-v

EXECUTIVE SUMMARY:
Junior Machine Learning Engineer with 2 years of experience building basic prompt chains, web scraping scripts, and standard Scikit-Learn pipelines.

TECHNICAL SKILLS:
- Core: Python, Pandas, NumPy, Scikit-Learn, Streamlit, Basic OpenAI APIs, SQL
- Tools: Git, VS Code, Linux, Jupyter Notebooks

PROFESSIONAL EXPERIENCE:
Junior Python Developer — InfoTech Solutions, Hyderabad (2023 - Present)
- Built interactive Streamlit dashboards for reporting sales analytics and data distribution trends.
- Integrated standard OpenAI wrapper endpoints for document summarization tasks.
- Cleaned tabular datasets, handled missing values, and managed SQLite relational tables.

Machine Learning Intern — DataSpark Labs, Hyderabad (2022 - 2023)
- Built classification and regression models using Scikit-Learn and XGBoost on tabular datasets.

EDUCATION:
- B.E. in Information Technology, Osmania University (2019 - 2023) | First Class""",
        "swot": {
            "strengths": ["Strong foundational Python, Pandas, and SQL basics", "Eager learner with Streamlit prototyping skills"],
            "weaknesses": ["Lacks multi-agent systems (LangGraph), Groq inference, and vector DBMS experience"],
            "opportunities": ["Great candidate for Junior ML or Associate Developer role"],
            "threats": ["Does not meet senior or lead requirements"]
        }
    },
    {
        "id": "cv_08",
        "filename": "Divya_Krishnan_Product_Manager_AI.pdf",
        "candidate_name": "Divya Krishnan",
        "email": "divya.k@domain.com",
        "phone": "+91-9876543216",
        "target_role": "Lead Product Manager - AI & Data",
        "raw_content": """Divya Krishnan | Bengaluru, India | divya.k@domain.com | +91-9876543216 | linkedin.com/in/divyakrishnan-pm

EXECUTIVE SUMMARY:
Technical Product Manager with 7 years of experience launching AI/ML products, enterprise SaaS solutions, and data analytics tools. Adept at translating complex LLM capabilities into high-ROI customer workflows.

TECHNICAL & PRODUCT SKILLS:
- Product Management: PRD authoring, North-Star metrics, User Story mapping, Agile/Scrum, GTM Strategy
- AI/Data Concepts: RAG workflows, LLM benchmarking, Prompt Engineering, Vector Search, Data Lineage
- Analytics & Tools: Mixpanel, Amplitude, JIRA, Figma, SQL, Postman

PROFESSIONAL EXPERIENCE:
Lead AI Product Manager — DataSense AI, Bengaluru (2021 - Present)
- Led product roadmap for enterprise RAG assistant, achieving $2.4M ARR within 14 months of launch.
- Partnered with ML teams to establish cost-latency-accuracy Pareto trade-offs for Llama-3 vs. proprietary models.
- Increased user retention by 38% through contextual feedback loops and automated error recovery.

Product Manager — HyperGrowth SaaS, Mumbai (2018 - 2021)
- Managed customer onboarding workflows and analytics reporting dashboard for 500+ enterprise clients.
- Conducted 100+ user interviews to identify key recruitment platform automation pain points.

EDUCATION:
- MBA in Product & Marketing, IIM Bangalore (2016 - 2018)
- B.Tech in Computer Science, NIT Surathkal (2012 - 2016)""",
        "swot": {
            "strengths": ["Proven $2.4M ARR track record for enterprise AI SaaS", "Exceptional blend of engineering and IIM MBA product leadership"],
            "weaknesses": ["Does not write production backend code directly"],
            "opportunities": ["Can lead product vision and GTM for the entire platform"],
            "threats": ["Requires high product autonomy"]
        }
    },
    {
        "id": "cv_09",
        "filename": "Karthik_Balakrishnan_Embedded_Linux.pdf",
        "candidate_name": "Karthik Balakrishnan",
        "email": "karthik.b@domain.com",
        "phone": "+91-9876543217",
        "target_role": "Embedded Linux & Firmware Engineer",
        "raw_content": """Karthik Balakrishnan | Bengaluru, India | karthik.b@domain.com | +91-9876543217 | github.com/karthik-embedded

EXECUTIVE SUMMARY:
Embedded Linux and Firmware Engineer with 6 years of experience in Board Support Package (BSP) development, Linux kernel device drivers, Yocto builds, and ARM microcontroller firmware.

TECHNICAL SKILLS:
- Embedded Systems: Linux Kernel Drivers (I2C, SPI, UART, PCIe), BSP Development, Yocto, U-Boot
- Microcontrollers: ARM Cortex-M4/M7, STM32, ESP32, FreeRTOS
- Languages & Protocols: C, C++, Python, Assembly, CAN bus, Modbus, BLE
- Hardware Tools: Oscilloscopes, Logic Analyzers, JTAG / SWD Debuggers

PROFESSIONAL EXPERIENCE:
Senior Embedded Systems Engineer — EdgeWave Hardware, Bengaluru (2021 - Present)
- Authored custom Linux device drivers and optimized Yocto Linux distributions for ARM-based smart gateway.
- Reduced cold boot time by 60% (from 18s to 7.2s) through U-Boot and systemd initialization tuning.
- Designed FreeRTOS firmware for sensor telemetry collection across RS485 and CAN interfaces.

Firmware Engineer — MicroEmbed Labs, Chennai (2018 - 2021)
- Developed low-power STM32 firmware with sleep-state power management for IoT battery devices.
- Created automated hardware-in-the-loop (HIL) test rigs using Python and PyVISA.

EDUCATION:
- B.E. in Electronics & Instrumentation, College of Engineering Guindy (CEG), Anna University (2014 - 2018)""",
        "swot": {
            "strengths": ["6 years hands-on Linux kernel driver and Yocto mastery", "Deep hardware debugging and boot time optimization skills"],
            "weaknesses": ["Non-web software stack (no web development experience)"],
            "opportunities": ["Ideal for IoT, edge AI hardware, and PCB sensor integration"],
            "threats": ["Onsite lab presence required"]
        }
    },
    {
        "id": "cv_10",
        "filename": "Neha_Chopra_DevSecOps_Security.pdf",
        "candidate_name": "Neha Chopra",
        "email": "neha.chopra@domain.com",
        "phone": "+91-9876543218",
        "target_role": "Cloud Security & DevSecOps Engineer",
        "raw_content": """Neha Chopra | Delhi NCR, India | neha.chopra@domain.com | +91-9876543218 | linkedin.com/in/nehachopra-sec

EXECUTIVE SUMMARY:
Cloud Security & DevSecOps Engineer with 6.5 years of experience securing AWS/Kubernetes architectures, integrating CI/CD shift-left security, and driving SOC2 / ISO 27001 compliance.

TECHNICAL SKILLS:
- Cloud & Container Security: AWS Security, Kubernetes RBAC, Trivy, Snyk, SonarQube, OPA Gatekeeper
- Security Domains: IAM Least Privilege, KMS Key Management, SAST/DAST, Vulnerability Management
- DevOps & Scripting: GitHub Actions, Terraform, Python, Bash, Docker, Helm
- Compliance: SOC2 Type II, ISO 27001, GDPR

PROFESSIONAL EXPERIENCE:
Lead DevSecOps Engineer — SecureCloud Systems, Gurugram (2021 - Present)
- Integrated automated SAST, DAST, and container vulnerability gating into GitHub Actions pipelines, blocking 400+ critical flaws before production.
- Enforced Kubernetes Pod Security Standards and Open Policy Agent (OPA) admission controls across 12 EKS clusters.
- Successfully led SOC2 Type II and ISO 27001 technical audit controls with zero major non-conformities.

Cloud Security Analyst — CyberShield India, Noida (2018 - 2021)
- Implemented AWS GuardDuty, AWS Security Hub, and centralized CloudTrail log monitoring.
- Conducted regular internal network penetration testing and developer security training sessions.

EDUCATION:
- B.Tech in Information Technology, Delhi Technological University (DTU) (2014 - 2018)
- Certifications: AWS Certified Security - Specialty, Certified Kubernetes Security Specialist (CKS)""",
        "swot": {
            "strengths": ["AWS Certified Security Specialist & CKS certified", "Strong DevSecOps shift-left automation & SOC2 compliance background"],
            "weaknesses": ["Focus is purely security/compliance rather than feature development"],
            "opportunities": ["Can establish enterprise security guardrails and audit readiness"],
            "threats": ["Prefers Delhi NCR or Remote"]
        }
    }
]
