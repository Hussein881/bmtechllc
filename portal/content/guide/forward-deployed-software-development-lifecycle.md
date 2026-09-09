---
title: Forward Deployed Software Development Lifecycle
description: Continuous, embedded enterprise software execution model mapping FDE roles, deliverables, and risks across six phases.
owner: fa
updated: '2026-09-02'
tags:
  - onboarding
  - playbook
status: published
visibility: internal
reviewCycleMonths: 6
order: 50
related: []
---

## Enterprise Execution Framework & FDE Competency Mapping

The **Forward Deployed Software Development Lifecycle (FD-SDLC)** adapts the traditional enterprise software lifecycle for environments where software must be built, adapted, and integrated directly inside a client's infrastructure. 

Unlike standard engineering workflows that operate in isolated, multi-tenant environments, the FD-SDLC uses **Forward Deployed Engineers (FDEs)** to compress discovery, architecture, deployment, and feedback loops into a continuous execution cycle within the customer's ecosystem.

---

## Phase 1: Technical Discovery & Operational Feasibility

The initiation phase establishes the project baseline, evaluates strategic alignment, and validates live technical feasibility directly within the client's environment.

### Key Objectives
* Define core problem statements, business drivers, and target performance metrics.
* Conduct live technical feasibility spikes (network access, authentication, air-gapped constraints).
* Evaluate project viability across technical, operational, financial, and regulatory compliance dimensions.
* Establish project governance, steering committee alignment, and milestone gates.

### FDE Role & Responsibilities
* **Environment Audit:** Inspect client network topographies, firewall rules, and legacy authentication systems (OAuth, SAML, mTLS).
* **Technical Proof-of-Concept:** Execute real-time spikes inside the client's landing zone rather than relying on theoretical risk decks.
* **The Core Loop Guard:** Validate that the client’s core challenge requires platform engineering rather than bespoke agency consulting.

### Key Deliverables
* **Project Charter & Scope Boundary:** Authorizes project scope, executive sponsorship, and explicit boundaries between core product features and custom adapters.
* **Live Feasibility & Infrastructure Audit Report:** Outlines verified VPC access rules, compliance boundaries (SOC2, HIPAA, GDPR), and technical risks.
* **Integrated Deployment Roadmap:** Defines release milestones, environment deployment targets, and operational SLAs.

### Phase Failure Modes & Risks
* **Unviable ROI & Scope Inflation:** Building without verifying client data accessibility leads to massive resource waste.
* **The "Consulting Trap":** Failing to enforce scope boundaries turns the engineering team into a custom software agency building one-off tools.
* **Compliance & Security Blockers:** Skipping early security checks in isolated client networks results in forced project halts late in the lifecycle.

---

## Phase 2: Requirements Elicitation & Scope Architecture

Raw business objectives are translated into structured technical requirements, separating core product platform features from client-specific integration adapters.

### Key Objectives
* Conduct technical workshops, user interview sessions, and system dependency mappings.
* Catalog user personas, operational workflows, and data pipeline constraints.
* Formulate functional specifications and non-functional targets (latency, availability, throughput, security).

### FDE Role & Responsibilities
* **Technical Translation:** Bridge executive business goals and client engineering constraints into concrete technical metrics.
* **Scope Architecture:** Categorize requirements into two buckets:
  1. *Core Platform Features:* Generalized capabilities fed back into the main product repository.
  2. *Field Extensions:* Client-specific pipeline adapters, middleware, and schema mappings.
* **Traceability Enforcer:** Map business requirements directly to system specification items and testable assertions.

### Key Deliverables
* **System Requirements Specification (SRS):** Standardized document capturing functional rules, data requirements, external interfaces, and quality attributes.
* **Core vs. Adapter Backlog:** Prioritized feature backlog mapped via frameworks like MoSCoW (Must-have, Should-have, Could-have, Won't-have).
* **Interface Traceability Matrix:** Links client workflows directly to API contracts and validation tests.

### Phase Failure Modes & Risks
* **Building the Wrong Integration:** Proceeding based on unverified client assumptions leads to low end-user adoption.
* **Uncontrolled Scope Creep:** Undefined integration boundaries cause continuous shift in deliverables, destroying project timelines.
* **Ignored Non-Functional Quality Targets:** Neglecting security, latency, or throughput requirements up front forces expensive late-stage architectural re-writes.

---

## Phase 3: Architecture & System Design

Translates system specifications into a concrete technical blueprint, data pipeline model, and interface integration strategy.

### Key Objectives
* Select architectural patterns (e.g., Event-Driven, Microservices, Modular Monolith) compatible with the client’s deployment target.
* Design technical contracts, storage tier models, and internal/external API communications.
* Establish visual guidelines, wireframes, and interface workflows for key end-user journeys.

### FDE Role & Responsibilities
* **Integration Layer Design:** Build API adapters, data pipeline connectors (SQL, Spark, Snowflake), and search pipelines (e.g., PostgreSQL with `pgvector`, Qdrant) bridging client systems to the platform.
* **Multi-Cloud & Hybrid Adaptation:** Ensure containerized services deploy seamlessly across AWS, GCP, Azure, or on-premises Kubernetes (OpenShift, VMware).
* **Security Architecture:** Implement end-to-end data privacy protocols, PII masking, tokenization, and zero-trust authentication wrappers.

### Key Deliverables
* **Architecture Design Document (ADD):** System topology, container manifests, security boundaries, and technical stack choices.
* **Data & API Contract Specifications:** Database schemas, entity relationships, and interface definitions (OpenAPI/REST, gRPC, schema registries).
* **UX/UI Prototypes & Workflows:** Wireframes and interface flows for client-facing components.

### Phase Failure Modes & Risks
* **Architectural Bottlenecks & Tech Debt:** Skipping deep architectural review yields brittle systems that fail under production load.
* **Data Schema Instability:** Unstandardized API contracts and shifting database schemas mid-development trigger costly refactoring.
* **Incompatible Infrastructure:** Building without accounting for client-side firewall or container orchestration constraints blocks deployment in Phase 5.

---

## Phase 4: Test Planning & Data Evaluation Strategy

Establishes objective quality criteria, test environments, and validation frameworks in parallel with system design before execution begins.

### Key Objectives
* Formulate a multi-layered testing strategy covering unit, integration, end-to-end, and non-functional validation.
* Configure test environments, test data management protocols, and automated validation tooling.
* Define acceptance criteria and "Definition of Done" metrics for all software deliverables.

### FDE Role & Responsibilities
* **Real-World Data Validation:** Build test suites that validate code against messy, real-world client data inputs rather than clean synthetic mocks.
* **AI & Data Pipeline Benchmarking:** Implement evaluation frameworks (e.g., LLM-as-judge, deterministic assertions, latency profiling) to track data drift and output quality.
* **Non-Functional Verification Setup:** Configure automated security scans, load tests, and failover validation suites inside client-adjacent staging environments.

### Key Deliverables
* **Master Test & Evaluation Plan:** Outlines test levels, coverage targets, data drift benchmarks, and execution schedules.
* **Test Case & Assertion Suite:** Formulated scenarios covering core workflows, edge cases, data sanitization, and stress limits.
* **Acceptance Criteria Framework:** Quantitative performance and quality thresholds required for production sign-off.

### Phase Failure Modes & Risks
* **Unclear Definition of Done:** Features marked complete without objective metrics contain critical logic bugs or unhandled edge cases.
* **Mock-Only Testing Blindness:** Relying solely on synthetic test data masks regressions caused by messy production data formats.
* **Post-Deployment Security Vulnerabilities:** Neglecting non-functional test planning leaves performance bottlenecks and security flaws undetected until live deployment.

---

## Phase 5: Agile Execution & Embedded Engineering

Implements the designed software incrementally using iterative sprints, automated CI/CD pipelines, and direct code commits within the client target environment.

### Key Objectives
* Execute development in 2-week sprint cycles using prioritized user stories and regular Agile ceremonies.
* Enforce code quality through automated Continuous Integration (CI) pipelines running linting, unit tests, and build checks.
* Conduct continuous code reviews, architectural adherence checks, and system integration.

### FDE Role & Responsibilities
* **Production Code Delivery:** Write modular, production-grade code (Python, Go, TypeScript) deployed into the client’s VPC or air-gapped landing zone.
* **Client CI/CD Integration:** Build automated deployment pipelines via GitHub Actions, GitLab CI, or Jenkins that comply with client approval protocols.
* **Rapid Triaging:** Debug integration blockers, API mismatches, and deployment failures directly alongside client engineering teams.

### Key Deliverables
* **Production-Grade Codebase:** Tested source code for core modules and field integration adapters.
* **Automated CI/CD Pipelines:** Container build, test, and automated deployment configurations.
* **Sprint Artifacts:** Sprint backlogs, velocity metrics, burn-down reports, and live software increment demonstrations.

### Phase Failure Modes & Risks
* **Big-Bang Integration Conflicts:** Avoiding iterative integration and automated CI leads to massive merge conflicts near release dates.
* **Opaque Progress Metrics:** Lack of structured sprint artifacts reduces visibility into team velocity and milestone delivery.
* **Rigid Delivery Cycles:** Rigid execution prevents adaptation when client environments or underlying data sources shift mid-project.

---

## Phase 6: Release, Operations & Upstream Feedback

Delivers validated software increments into live production, establishes operational telemetry, and upstreams reusable innovations back to the core platform.

### Key Objectives
* Execute zero-downtime production deployment strategies (e.g., Blue/Green or Canary rollouts).
* Establish real-time monitoring, centralized logging, alerting, and operational telemetry.
* Complete operational handoffs, user enablement, and day-2 support procedures.

### FDE Role & Responsibilities
* **Zero-Downtime Deployment:** Execute production release strategies and verify live system behavior under load.
* **Observability Setup:** Configure monitoring dashboards, error logging, and alert triggers for system health and model drift.
* **Upstream Contribution:** Abstract reusable adapters, custom pipeline tools, and performance fixes built during deployment, merging them back into the core platform repository.
* **Day-2 Handoff:** Draft operational runbooks and train client technical staff for ongoing system maintenance.

### Key Deliverables
* **Production Release Package:** Deployed, fully integrated software running in the client's production environment.
* **Observability & Telemetry Setup:** Configured dashboards tracking system uptime, API latency, error rates, and data pipeline health.
* **Operational Playbooks & Upstream Code PRs:** Incident response guides, maintenance procedures, and core platform pull requests containing generalized improvements.

### Phase Failure Modes & Risks
* **High-Risk Manual Releases:** Manual deployment procedures trigger outages, broken configurations, and prolonged downtime.
* **Operational Blindness:** Lacking telemetry and logging leaves production issues undetected until reported by end users.
* **Codebase Fragmentation:** Failing to upstream reusable code results in permanent branch drift, forcing the team to maintain divergent custom builds for every client.

---

## Comprehensive Matrix: SDLC Phases vs. FDE Execution

| SDLC Phase | Core Objective | Primary FDE Skill Applied | Key FDE Output vs. Traditional Output | Primary Phase Risk |
| :--- | :--- | :--- | :--- | :--- |
| **1. Discovery & Feasibility** | Baseline purpose, alignment, and constraint validation. | Client Discovery & Field Leadership | Live environment technical proof-of-concept **vs.** Theoretical feasibility deck | Consulting Trap (becoming a custom dev shop) |
| **2. Requirements & Scope** | Functional/non-functional specification and scoping. | Technical Product & Scope Management | Scope boundary map (Core product vs. Custom adapter) **vs.** Generic SRS document | Constant scope creep and shifting boundaries |
| **3. Architecture & Design** | System blueprints, API contracts, and interface models. | Systems Integration & Security | Production data pipelines, auth wrappers, and K8s manifests **vs.** Theoretical ADD diagrams | Architectural bottlenecks and tight coupling |
| **4. Test & Evaluation** | Objective quality standards and environment setup. | Data Engineering & AI Fluency | Data drift benchmarks and live integration test suites **vs.** Manual test scripts | Mock-only testing masking real-world failures |
| **5. Agile Execution** | Incremental software development and pipeline setup. | Full-Stack Software Engineering | Deployed containerized services in client VPC **vs.** Unintegrated feature builds | Big-bang integration conflicts and build failures |
| **6. Release & Upstream** | Production deployment, telemetry, and operational handoff. | Enterprise Infrastructure & Upstream Engineering | Operational runbooks + Upstreamed core platform code **vs.** Standard sign-off documents | Codebase fragmentation and unmaintained custom forks |
