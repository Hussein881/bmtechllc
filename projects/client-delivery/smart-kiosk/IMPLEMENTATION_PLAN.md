# Master Prompt: Smart Kiosk Project Initialization

## 1. Role and Objective

Act as a senior software architect and full-stack engineer responsible for initializing the Smart Kiosk Edge-First QSR Platform from an empty repository.

Your objective is to establish a clean, maintainable, testable project foundation that supports the Smart Kiosk MVP. Prioritize a working end-to-end prototype, reliable local operation, clear architectural boundaries, and straightforward development workflows.

The MVP targets approximately 1–2 weeks of development, assuming the necessary external systems and hardware are available. Optimize for this timeframe without compromising essential correctness, payment security, or data integrity.

Begin with project initialization, not full feature implementation. Establish the architecture, development tooling, initial database schema, and verification workflow before proceeding to the first functional feature.

## 2. Source Documents and Requirement Hierarchy

Use the provided project documents as the authoritative basis for implementation.

### 2.1 Smart Kiosk MVP — Functional Scope

The MVP defines the features that must be demonstrated:

- **Interactive menu:** Customers can browse food categories, switch between meal schedules such as Breakfast and Lunch, and see prices update when customizing items.
- **Smart recommendations:** The kiosk suggests a relevant add-on based on the customer's current order before checkout.
- **Payments and order processing:** The prototype exercises a provider-neutral,
  deterministic mock payment adapter and delivers resulting orders to a mock
  kitchen adapter. Real contactless and chip-card integration remains pending
  provider and hardware selection.
- **POS integration:** Completed prototype orders are submitted to a
  deterministic mock POS adapter through the eventual validated payload
  contract.
- **Basic offline support:** Core menu and ordering functionality remains usable
  during a WAN interruption while the kiosk can reach its local Store Edge Node;
  provider-dependent payment behavior is not claimed.
- **Accessibility:** The interface includes a lower-screen mode and a high-contrast display option.

The intended outcome is a functional prototype that demonstrates the complete customer ordering journey, not a production-ready enterprise platform.

### 2.2 ERD — Data Model

Use the provided ERD document as the starting point for database design, including its entity definitions, attributes, primary keys, foreign keys, and relationship summary.

The model covers:

1. Store
2. Kiosk Terminal
3. Order
4. Order Item
5. Payment
6. Order Item Modifier
7. Menu Category
8. Menu Item
9. Modifier Group
10. Modifier
11. Menu Schedule / Daypart
12. Menu Item Schedule
13. Menu Item Modifier Group
14. Offline Payment Queue
15. Menu Version
16. Store Item Availability Override
17. Store Modifier Availability Override
18. Integration Dispatch
19. POS Register

Preserve the model's intent and relationships. Review the schema for implementation-critical ambiguities before generating migrations.

The ERD explicitly distinguishes SRS-supported concepts from proposed relational attributes and structures. Treat proposed fields as design candidates to validate, not as mandatory requirements that have already been settled.

Maintain the following principles:

- Separate catalog data from transaction data.
- Preserve transaction-time item names, SKUs, prices, and selected modifiers where appropriate.
- Keep order, payment, and downstream dispatch states independent.
- Use stable transaction identifiers for idempotency and duplicate-request protection.
- Keep store-specific availability overrides separate from the centrally managed menu.
- Track delivery outcomes independently for each integration destination.

Do not expand or redesign the ERD unnecessarily. Document any changes needed to support the MVP.

### 2.3 SRS Second Draft — Technical Requirements

Use the SRS to fill technical gaps and clarify the behavior required by the MVP.

Relevant requirements include:

- Edge-first architecture with a local Store Edge Node and SQLite database.
- Local communication between the kiosk client and edge service over the store LAN.
- Local menu replication, daypart evaluation, and order processing.
- Payment-terminal communication through an appropriate provider-supported integration.
- Payment security, encrypted payment references or payloads, and idempotent transaction handling.
- Local kitchen routing and decoupled POS and kitchen integration adapters.
- Basic offline behavior and safe recovery after interruptions.
- Store-specific availability overrides and menu synchronization.
- Input validation, error handling, accessibility, and relevant performance requirements.

Do not automatically implement every capability in the SRS. Distinguish between:

- **MVP requirements:** Needed to demonstrate the agreed prototype.
- **Supporting requirements:** Necessary technical foundations or safeguards for MVP features.
- **Future scope:** Features that can be deferred without compromising the MVP.

### 2.4 Governing-Document Rule

The MVP, ERD, and this implementation plan are the governing documents for
this repository:

- The **MVP** defines the customer-facing outcome and delivery scope.
- The **ERD** defines the initial data-model intent and required relational
  boundaries.
- This **implementation plan** records confirmed delivery decisions, including
  the browser runtime, provider-neutral integrations, and the initialization
  boundary.

The SRS is supporting material only. Use it to fill a gap that the governing
documents leave open; do not use it to expand, override, or reinterpret their
scope. A confirmed decision in this plan controls an implementation conflict;
otherwise preserve the MVP's functional intent and the ERD's data-model intent.
Record any unresolved conflict as an outstanding decision rather than silently
inventing a requirement.

## 3. Confirmed Project Decisions

These decisions are fixed for initialization.

### Kiosk Runtime

Build a web application intended to run in a dedicated kiosk browser on the target kiosk device.

Use a browser-compatible frontend. Do not introduce Electron, a native desktop application, or a separate Android application.

The application should support a full-screen, touch-friendly interface and avoid dependencies on browser features that are unavailable or unreliable in the target environment.

The dedicated browser and operating-system kiosk configuration are deployment concerns. Document the expected configuration, but do not assume the browser is already installed or configured.

### Payment Integration

The payment provider and terminal have not been selected.

Define a provider-neutral payment interface and implement a mock payment adapter for development and testing. The mock must support deterministic success, decline, cancellation, timeout, and error scenarios.

Do not select a real provider, install a provider-specific SDK, or build a production payment integration until the provider and hardware are confirmed.

Do not claim that simulated payments are real card transactions. Do not store raw card numbers or simulate unsupported offline authorization.

### POS Integration

Implement a mock POS adapter using realistic, deterministic test payloads.

The adapter must represent the expected transaction handoff, including the transaction UUID, store and terminal identifiers, order type and status, timestamps, financial totals, payment metadata permitted for downstream use, and item and modifier details where applicable.

Use the ERD and SRS to define the payload contract. Keep the mock adapter behind a clear interface so a real POS integration can replace it later.

The mock should support success, rejection, timeout, and retry scenarios. Record dispatch status and avoid duplicate submissions through idempotency.

Do not claim that the mock submits orders to a real POS system.

### Repository State

The repository is empty. Create the project structure, package configuration, application code, documentation, tests, and initial database migrations from scratch.

Do not assume existing code, dependencies, configuration files, or infrastructure are present.

### MVP Delivery Boundary

The demonstrable MVP uses deterministic mock payment, kitchen, and POS
adapters. It demonstrates the complete local ordering journey and validates
the contracts required to replace mocks later. It does not process a live card,
send a live order, or claim a real payment authorization.

For this MVP, **offline** means that WAN/internet access is unavailable while
the kiosk browser can still reach its local Store Edge Node over the LAN. The
menu, pricing, order persistence, and mock dispatch workflow continue locally.
If the browser cannot reach the Store Edge Node, it must show an unavailable
state and must not accept checkout or payment. Edge-isolated checkout,
encrypted payment store-and-forward, cloud menu synchronization, hardware
health recovery, SQLCipher/TPM key management, and a manager portal are future
scope until their dependencies are selected and verified.

Use a seeded `0%` demonstration tax rule and an ISO 4217 currency for the MVP.
All persisted monetary amounts use integer minor units. The tax rule is
configuration, not a claim about a restaurant's production tax policy.

## 4. Recommended Technology Stack

Use the following stack unless a concrete compatibility issue requires a documented alternative.

| Layer | Technology | Responsibility |
|---|---|---|
| Language | TypeScript | Shared language across client and server |
| Frontend | React + Vite | Kiosk web application |
| Styling | Tailwind CSS | Touch-friendly responsive UI |
| Backend | Node.js + Fastify | Local edge API and business logic |
| Database | SQLite | Local persistence |
| API | REST + JSON | Client-server communication |
| Live updates | WebSockets when needed | Menu, availability, and operational updates |
| Validation | Zod | Runtime request and response validation |
| Package manager | pnpm | Dependency and workspace management |
| Unit and integration tests | Vitest | Business logic, APIs, and adapter behavior |
| Browser tests | Playwright | Critical customer workflows |
| Code quality | ESLint + Prettier | Linting and consistent formatting |

Use a pnpm monorepo if the client, edge service, and shared contracts benefit from coordinated development.

Do not add Redis, a cloud database, microservices, container orchestration, or additional frameworks without a demonstrated MVP requirement.

The selected stack is an implementation recommendation, not a claim that the source documents mandate these exact technologies.

## 5. Target Architecture

Implement a modular, edge-first architecture.

The kiosk browser hosts the customer-facing web application. The local Store Edge Node runs the backend service and SQLite database, providing the authoritative source for local menu data, pricing calculations, order creation, and dispatch coordination.

The client communicates with the edge service through a documented API over the store LAN. Keep business logic out of UI components, and do not allow the browser to be the authoritative source of transaction totals or payment state.

Organize the application into clear modules:

- Menu and category management
- Menu schedules and daypart evaluation
- Item customization and modifier rules
- Pricing and cart calculations
- Recommendation rules
- Order creation and persistence
- Payment adapter
- Kitchen dispatch adapter
- POS adapter
- Offline and retry handling
- Accessibility and kiosk UI behavior

Keep integration-specific code behind interfaces. The application should run locally with mock payment, POS, and kitchen adapters when real external systems are unavailable.

Avoid premature abstraction. Introduce modules and interfaces where they establish meaningful boundaries, not simply to maximize the number of files.

### Order, Payment, and Dispatch State Rules

Keep the three concerns independent and use explicit state transitions:

| Concern | MVP states | Rule |
|---|---|---|
| Order | `DRAFT`, `AWAITING_PAYMENT`, `PAID`, `FULFILLMENT_PENDING`, `COMPLETED`, `CANCELLED`, `PAYMENT_FAILED` | An order is not paid merely because payment was initiated. |
| Payment attempt | `INITIATED`, `PENDING`, `APPROVED`, `DECLINED`, `CANCELLED`, `FAILED`, `TIMED_OUT`, `UNKNOWN` | A timeout or interrupted request is `UNKNOWN` until its status is safely resolved; never blindly resend it. |
| Kitchen/POS dispatch | `PENDING`, `IN_FLIGHT`, `ACKNOWLEDGED`, `FAILED_RETRYABLE`, `FAILED_FINAL`, `UNKNOWN` | Kitchen and POS outcomes are tracked independently and use idempotent retry. |

After an approved payment, persist the payment result and create kitchen and
POS dispatch records in the same local database transaction. Attempt kitchen
delivery first. Customer confirmation requires the configured kitchen outcome
for the MVP; a POS failure is recorded and retried asynchronously and must not
reverse a paid order or trap the customer in checkout.

### Suggested Repository Structure

Create a structure similar to the following:

    smart-kiosk/
    ├── apps/
    │   ├── kiosk-client/
    │   └── edge-server/
    ├── packages/
    │   └── shared/
    ├── tests/
    ├── docs/
    ├── .env.example
    ├── .gitignore
    ├── package.json
    ├── pnpm-workspace.yaml
    ├── tsconfig.base.json
    └── README.md

Adapt the structure when there is a concrete technical reason, but keep the initial architecture small and easy to understand.

The shared package should contain shared types, schemas, and API contracts. It must not become a dumping ground for unrelated logic.

## 6. Database and Data Modeling

Use SQLite for the local Store Edge Node database.

Before implementing the schema:

1. Review all ERD entities, attributes, and relationships.
2. Identify fields marked as proposed and distinguish them from requirements supported by the SRS.
3. Define primary keys, foreign keys, nullability, uniqueness, and indexes.
4. Confirm how orders, payments, and integration dispatches relate to each other.
5. Define transaction-time snapshots for order items and modifiers.
6. Document any schema decisions or changes needed for the MVP.

Use version-controlled database migrations. Enable and verify SQLite foreign-key enforcement.

Use UUIDs for transaction identity and idempotency where appropriate. Store timestamps consistently and evaluate daypart schedules using the configured store timezone.

Keep order totals and financial values consistent. Persist money as integer
minor units, persist the ISO 4217 currency with the order, and calculate the
total on the server from the current local menu. For the MVP, seed a named 0%
demonstration tax rule; do not present it as a restaurant tax policy.

Resolve the ERD into migrations as follows:

- Add a `menu_item_schedule` junction so schedules determine which items are
  active.
- Keep modifier selection bounds on `menu_item_modifier_group` (`min_selections`
  and `max_selections`); a required selection is `min_selections > 0`.
- Snapshot modifier-group identity with an ordered modifier, in addition to its
  name, SKU, and price adjustment.
- Use soft deactivation for catalog records referenced by transactions; do not
  hard-delete historical menu rows.
- Use separate store item and store modifier availability-override tables so
  each remains protected by a real foreign key.
- Give an integration dispatch an idempotency key, retry schedule, sanitized
  last error, and unique destination per transaction.
- Keep the offline-payment-queue schema feature-gated and empty until selected
  hardware supports secure, encrypted store-and-forward processing.

Define schedules in the store's IANA timezone using start-inclusive,
end-exclusive intervals. Reject overlapping active schedules unless an explicit
priority is configured. At checkout, revalidate the cart against the current
schedule and availability overrides and return an actionable cart-review error
when it is no longer valid.

The ERD includes menu versioning and an offline payment queue. Preserve their intended roles in the model, but implement advanced synchronization and payment-queue behavior only to the extent required by the agreed MVP and supported by the selected integrations.

Do not introduce a separate cloud database or central management service during initialization.

## 7. API and Shared Contracts

Define typed, validated API contracts between the kiosk client and edge service.

At minimum, plan contracts for:

- Retrieving the active menu and categories.
- Retrieving the active meal schedule.
- Retrieving item customization options.
- Obtaining validated pricing for selected items and modifiers.
- Creating and retrieving orders.
- Initiating and checking payment status.
- Dispatching orders to the kitchen.
- Submitting completed orders to the mock POS.
- Retrieving integration status and reporting recoverable errors.

Choose resource paths and response shapes consistently. Document the contracts and keep the frontend and backend aligned through shared schemas where practical.

Validate all client input on the server. Treat client-submitted prices as untrusted; calculate or verify prices using server-side menu data.

Use stable request identifiers and idempotent operations for order creation and external dispatch. Make error responses predictable and actionable.

Do not create endpoints for future administrative, analytics, fleet-management, or cloud-sync features unless they are needed for the MVP.

## 8. MVP Customer Journey

Implement the core workflow in this order.

### Step 1: Menu Browsing

Load the active menu from local persistence and present categories and items in a clear, touch-friendly layout.

Support the active meal schedule, including transitions between menus such as Breakfast and Lunch. Evaluate schedules using the store's local timezone.

### Step 2: Customization and Pricing

Allow customers to select menu items and available modifiers.

Enforce the applicable selection rules and calculate totals from trusted menu data. Display price changes immediately when modifiers are added or removed.

### Step 3: Recommendations

Before checkout, present a relevant add-on based on the current cart.

Use simple, deterministic rules that are easy to configure and test. Do not introduce machine learning or a recommendation service.

### Step 4: Order Review

Show the selected items, quantities, modifiers, and final calculated total.

Validate the order before payment. Persist the order with a stable transaction UUID and transaction-time snapshots so historical records remain accurate if the menu changes.

### Step 5: Payment

Call the provider-neutral payment interface.

Initially use the mock adapter to simulate payment outcomes. Represent pending, approved, declined, cancelled, and failed outcomes distinctly as appropriate to the adapter contract.

Do not mark an order paid simply because a payment request was initiated. Persist and transition the order and payment states according to the result reported by the adapter.

### Step 6: Kitchen Dispatch

After the required payment confirmation, dispatch the order through the kitchen adapter.

Provide a mock kitchen adapter for development and tests. Keep its behavior distinct from the POS adapter and track its delivery outcome separately.

### Step 7: POS Submission

Submit the completed transaction through the mock POS adapter.

Build a realistic, validated payload using the established shared contract. Persist the dispatch attempt and its outcome, and use idempotency to prevent duplicate transaction submissions.

The customer ordering workflow should be demonstrable end to end even before a real POS API is available.

### Step 8: Completion and Recovery

Display clear confirmation or failure messages. Handle timeouts and recoverable failures without silently losing an order or reporting an unverified success.

Keep the order, payment, kitchen dispatch, and POS dispatch states independent.

## 9. Payment and POS Adapter Contracts

### Payment Adapter

Define a provider-neutral interface with operations appropriate for initiating a payment and retrieving its result.

The mock implementation should support:

- Successful payment
- Declined payment
- Customer cancellation
- Timeout
- Provider or device error
- Retry and repeated-request scenarios

Make test outcomes deterministic through test configuration rather than random behavior.

Do not include card numbers, real payment credentials, or fabricated provider references in mock payloads. Mark simulated results clearly.

Once a provider is selected, implement its actual integration in a separate adapter without coupling provider-specific types to the core order model.

### POS Adapter

Define a stable interface for submitting a completed order and retrieving or recording its submission outcome.

Use realistic mock payloads containing the fields supported by the ERD and SRS. The example virtual register code `REGISTER_KIOSK_01` may be used as test configuration, not as a claim about a live POS environment.

Support deterministic accepted, rejected, timed-out, and retry outcomes. Record attempts using the Integration Dispatch model.

The adapter should be replaceable without rewriting order creation, pricing, or the kiosk interface.

## 10. Kitchen Integration

Create a kitchen dispatch interface that can support the eventual kitchen display or printer integration.

For the initial prototype, implement a mock adapter that accepts an order payload and returns a deterministic result. Record dispatch state separately from the order and payment records.

Preserve the option to connect to a real local KDS or printer through an appropriate adapter when the target system and protocol are known.

Do not invent a hardware protocol or claim that orders are physically reaching a kitchen when only the mock adapter is active.

## 11. Offline Behavior and Reliability

The MVP must demonstrate useful behavior during temporary network interruptions, but offline behavior must be defined precisely.

At minimum:

- Load required menu data from local persistence.
- Keep menu browsing and customization independent of internet connectivity once the menu is available locally.
- Keep the edge service and SQLite database local to the store.
- Support local kitchen routing when the kitchen destination is reachable over the LAN.
- Preserve order and dispatch records when downstream systems are temporarily unavailable.
- Retry recoverable integration failures safely.
- Use idempotency to prevent duplicate orders or external submissions.
- Distinguish between an operation that succeeded, failed, or has an unknown outcome.

Do not promise that the entire system remains operational if the edge service itself becomes unavailable unless a separate, tested client-side fallback is implemented.

Payment behavior during an internet outage remains dependent on the selected terminal and provider. Until those are confirmed, the mock payment adapter may simulate defined outcomes, but it must not claim to validate real offline payment authorization.

Implement advanced encrypted store-and-forward processing only after confirming that the selected payment hardware and provider support the required flow.

## 12. Security and Configuration

Use environment variables for configuration and secrets. Include a `.env.example` containing placeholders only.

Implement:

- Runtime validation for API requests and integration payloads.
- Parameterized database queries.
- Server-side pricing and order validation.
- Safe error responses that do not expose secrets.
- Appropriate CORS and local-network access configuration.
- Structured logging without sensitive payment data.
- Stable transaction identifiers and duplicate-request protection.

Raw primary account numbers (PANs) must never enter the kiosk application or local database. Use the payment terminal and provider's supported secure flow for real transactions.

Do not hardcode cryptographic keys or credentials. Do not log sensitive payment payloads. Do not implement a homemade payment-processing protocol.

Document the expected network boundaries between kiosk browser, edge service, payment terminal, kitchen, and POS.

Do not imply that the prototype is PCI-DSS certified or production-ready solely because these safeguards have been implemented.

## 13. Kiosk UI and Accessibility

Design the web application for a dedicated full-screen kiosk browser and touchscreen use.

The interface should provide:

- Large, clearly labeled touch targets.
- Straightforward category navigation.
- Clear item and modifier selection.
- Visible cart totals and price changes.
- A concise checkout flow.
- Clear payment and order status feedback.
- A lower-screen mode.
- A high-contrast display option.
- Appropriate visual confirmation for important actions.

Keep accessibility settings available during the customer journey. Avoid hover-dependent interactions and ensure controls are usable by keyboard for development and accessibility testing.

Use the SRS's accessibility guidance to inform implementation, while keeping the MVP's required modes explicit and testable.

Document how to launch the web application in the intended kiosk browser. Do not build browser-lockdown software or an operating-system kiosk shell as part of the web application unless separately requested.

## 14. Testing Strategy

Establish automated tests from the beginning.

### Unit Tests

Test pricing calculations, modifier constraints, schedule evaluation, recommendation rules, order-state transitions, and idempotency.

### Integration Tests

Test API validation, SQLite persistence, migrations, order creation, payment adapter behavior, and independent kitchen/POS dispatch tracking.

### End-to-End Tests

Use Playwright to verify the primary customer journey:

1. Browse the menu.
2. Switch meal schedules.
3. Customize an item.
4. Verify the updated total.
5. Receive an add-on recommendation.
6. Review and create an order.
7. Simulate payment approval.
8. Dispatch the order to the mock kitchen.
9. Submit the transaction to the mock POS.
10. Verify the final order and integration states.

Also test payment failure, POS timeout, repeated requests, simulated WAN loss
while the edge remains reachable, and the unavailable state when the edge is
not reachable. Do not report hardware, live POS, edge-isolated checkout,
encrypted payment queues, or performance SLAs as verified unless those systems
have actually been tested.

Tests must distinguish mocked behavior from real integration tests. Do not report physical hardware or live POS behavior as verified unless it has actually been tested.

## 15. Initialization and Implementation Workflow

### Phase 1: Establish the Foundation

Create the repository structure, workspace configuration, TypeScript setup, environment configuration, linting, formatting, and test infrastructure.

Add a README with prerequisites and development commands.

### Phase 2: Define Contracts and Data Model

Review the ERD, validate the proposed schema, create initial SQLite migrations, and define shared API and adapter contracts.

Document assumptions and unresolved integration decisions.

### Phase 3: Implement the Local Application Skeleton

Create the React kiosk client and Fastify edge service. Verify that the client can communicate with the local backend and that the backend can read and write to SQLite.

### Phase 4: Implement Mock Integrations

Implement provider-neutral payment, POS, and kitchen adapter interfaces with deterministic mock implementations.

Ensure the mock POS emits realistic, validated transaction payloads and records dispatch outcomes.

### Phase 5: Verify the Foundation

Run installation, build, type-check, lint, migration, unit-test, and integration-test commands.

Fix failures before proceeding. Confirm that the client and edge service can be started using documented commands.

### Phase 6: Build the First Vertical Slice

Implement the smallest complete functional path:

- Load a locally persisted menu.
- Display categories and items.
- Customize an item.
- Calculate the total on the server.
- Create and persist an order.
- Exercise the mock payment flow.
- Dispatch to the mock kitchen and POS.
- Display the resulting status.

Then extend the slice to cover recommendations, daypart switching, accessibility modes, and the required offline scenarios.

Keep the implementation aligned with the 1–2 week MVP timeframe. Defer broader SRS features that are not required for the prototype.

## 16. Acceptance Criteria for Initialization

Initialization is complete when:

- The repository contains a clean, working project structure.
- The kiosk client builds and runs in a browser.
- The edge service starts and exposes its documented API.
- SQLite initializes successfully and applies versioned migrations.
- Shared contracts and runtime validation are in place.
- Mock payment, POS, and kitchen adapters are available.
- The mock POS can produce realistic test payloads and deterministic outcomes.
- Automated tests can be run through documented commands.
- The README explains setup, environment configuration, and local execution.
- Assumptions and unimplemented real integrations are clearly documented.

Initialization does not mean every MVP feature is complete. It means the project is ready to implement those features safely and incrementally.

## 17. Execution Rules

- Start from the empty repository and create all required foundational files.
- Follow the MVP's functional priorities and use the ERD as the initial data-model reference.
- Use the SRS to resolve technical details without expanding the MVP unnecessarily.
- Preserve the distinction between requirements and proposed design decisions.
- Keep the payment provider undecided and provider-neutral.
- Use mock POS and kitchen adapters until the real integration details are available.
- Never claim a mock integration is a live integration.
- Do not implement speculative features or add unnecessary dependencies.
- Keep the code typed, modular, testable, and documented.
- Verify each phase before proceeding to the next.
- Report commands run, tests passed or failed, assumptions, and outstanding blockers accurately.

## Immediate Instruction

Begin by creating the project foundation from the empty repository.

First, establish the monorepo and development tooling, then define the shared contracts and initial SQLite schema based on the ERD. Implement the local client-server connection and deterministic mock adapters. Verify the complete initialization before proceeding with the first vertical slice.

Do not ask for a payment-provider decision during initialization. Keep payment integration provider-neutral and record the provider selection as an outstanding decision.

The goal is a reliable foundation for a demonstrable Smart Kiosk MVP—not a premature implementation of the entire enterprise platform.
