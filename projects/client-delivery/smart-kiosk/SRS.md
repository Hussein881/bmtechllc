# Smart Kiosk Edge-First QSR Platform

**System Requirements Specification (SRS)**

## 1. Introduction

### 1.1 Purpose

This System Requirements Specification (SRS) records technical guidance,
future-platform requirements, and gap-filling detail for the Smart Kiosk
Edge-First Quick-Service Restaurant (QSR) Platform. It supports the MVP, ERD,
and implementation plan; it is not the governing scope or delivery contract
for this repository.

### 1.2 Document Conventions

- Priority Levels: Requirements are prioritized as [Must Have] (Phase 1 MVP Scope), [Should Have] (Phase 2), or [Could Have] (Phase 3).

- Requirement Identifiers: Each verifiable requirement follows the format `[Category]-[Subdomain]-[Number]`.

- Mandatory Language: The words shall (mandatory requirement), should (recommended requirement), and may (optional requirement) convey strict engineering compliance standards.

- Source precedence: The MVP defines functional scope, the ERD defines the
  initial data-model intent, and the implementation plan records confirmed
  delivery decisions. This SRS fills gaps only and must not expand or override
  those governing documents. Requirements marked **Future integration** are
  deliberately outside the current prototype.

### 1.3 Intended Audience and Reading Suggestions

- Software Engineering Teams: To guide component architecture, local database schemas, local LAN protocols, and UI state machine implementation.

- QA & Test Engineers: To construct automated end-to-end test suites, offline network disconnect simulations, and security validation checks.

- QSR Operations & IT Executives: To verify scope alignment, fault isolation guarantees, and downstream system integration strategy.

### 1.4 Project Scope

The Smart Kiosk system is a high-speed, autonomous touchscreen ordering engine built specifically for high-volume fast-food environments. The platform mitigates peak-hour ordering queues and eliminates downtime caused by internet outages by moving core processing from the cloud down to local store hardware over a Local Area Network (LAN).

The scope encompasses:

- The front-of-house customer ordering interface (Kiosk Client Terminal).

- The in-store orchestration server (Store Edge Node) and local SQLite replica.

- Integrated payment terminal communications (Point-to-Point Encryption with Store-and-Forward capability).

- Decoupled integration adapters for Kitchen Display Systems (KDS), thermal printers, legacy Point of Sale (POS) registers, and Enterprise Resource Planning (ERP) inventory databases.

### 1.4.1 Current MVP Applicability

The current MVP is a browser kiosk and local Store Edge Node with seeded local
data and deterministic mock payment, kitchen, and POS adapters. It demonstrates
the complete customer journey without claiming live card processing or live
downstream delivery. Provider-specific terminal SDKs, live POS/KDS/printer
adapters, cloud synchronization, manager tooling, encrypted payment
store-and-forward, TPM-backed encryption, and hardware recovery remain future
integration work until their dependencies are selected and verified.

### 1.5 Definitions, Acronyms, and Abbreviations

- QSR: Quick-Service Restaurant.

- POS: Point of Sale System (the store's core system of record for accounting).

- KDS: Kitchen Display System (digital screens located in food preparation lines).

- ERP: Enterprise Resource Planning System (central supply chain and inventory engine).

- LAN: Local Area Network (the private high-speed local store network).

- P2PE: Point-to-Point Encryption (PCI-certified hardware-level payment encryption).

- Store Edge Node: A dedicated local compute unit installed in the store to orchestrate local data, queues, and dispatches.

- TPM: Trusted Platform Module (cryptographic hardware module for key storage).

- UUID: Universally Unique Identifier (36-character canonical string used for transaction idempotency).

- 86'd: Operational QSR term indicating an item or ingredient is out of stock.

### 1.6 References

- IEEE Std 830-1998 / ISO/IEC/IEEE 29148:2018 Standards for System Requirements Specifications.

- Payment Card Industry Data Security Standard (PCI-DSS) v4.0.

- ADA Standards for Accessible Design / WCAG 2.1 Level AA Accessibility Guidelines.

- Smart Kiosk Edge-First QSR Platform System Architecture Blueprint.

## 2. Overall Description

### 2.1 Product Perspective & Architectural Pattern

The Smart Kiosk platform operates as an additive, edge-first order intake channel. Unlike traditional cloud-dependent kiosk platforms that freeze or lag when central servers or internet connections slow down, this platform executes all critical user paths locally over the store's private Local Area Network (LAN).

The physical Kiosk Client Terminal runs a decoupled user interface that queries an in-store Store Edge Node. The Store Edge Node houses a read-optimized local database (SQLite) containing active menus, pricing rules, customization choices, and upsell logic. Order outputs are routed locally to kitchen printers and display screens within sub-second times, while transactions are formatted and injected into the existing store POS for accounting.

### 2.2 Operating Modes

- Online Operating Mode (**Future live integration**): Under normal network
  conditions, a selected payment reader may authenticate transactions in real
  time through its approved provider flow. Live kitchen/POS delivery and cloud
  analytics are future integrations. The MVP uses deterministic local mocks.

- WAN-Interrupted MVP Mode: When WAN/internet connectivity is lost but the
  kiosk can still reach its Store Edge Node over LAN, menu browsing,
  customization, server-side pricing, order persistence, and mock dispatch
  continue locally. The mock payment adapter may simulate a documented outcome;
  it does not authorize offline card payments.

- Degraded Edge-Isolated Mode (**Future integration**): If the Store Edge Node
  becomes unreachable over LAN, the MVP shows an unavailable state and does not
  accept checkout or payment. Read-only cached browsing and payment-token
  acceptance require separately designed and tested client fallback and a
  selected payment provider.

### 2.3 User Classes and Characteristics

- End Customer: Prioritizes screen responsiveness, clear visual customizations, fast checkout, accessibility accommodations, and intuitive payment interactions.

- Store Manager: Requires simple, non-technical tools to manually mark items out-of-stock ("86ing") during rushes without rebooting systems or calling central IT.

- System Administrator: Oversees corporate menu updates, remote device health diagnostics, security policy enforcement, and multi-store fleet configurations.

### 2.4 Design and Implementation Constraints

- PCI-DSS Compliance: Raw primary account numbers (PANs) shall never touch the kiosk operating system, local disk, or RAM memory; hardware readers must handle encryption at the pin-pad head.

- Fault Isolation: Delays, outages, or API timeouts originating from central cloud servers, loyalty networks, or legacy POS backends shall never cause the customer-facing checkout screen to lock or stall.

- Runtime: The current MVP uses a browser-compatible React web application.
  Electron and native Android applications are outside this repository's scope.
  Future runtime choices must not couple core order or integration contracts to
  a single hardware vendor.

### 2.5 Assumptions and Dependencies

- The store maintains a functional Local Area Network (LAN) with managed Ethernet switches or enterprise-grade local Wi-Fi.

- Any future payment terminal supports the provider's approved secure flow; its
  P2PE and offline store-and-forward capabilities are unconfirmed dependencies,
  not current MVP assumptions.

- The Store Edge Node and network switches remain powered via an Uninterruptible Power Supply (UPS) during store operations.

## 3. System Features & Functional Requirements

### 3.1 Deterministic Customer Workflow State Machine

The customer-facing application shall strictly enforce a deterministic state machine to ensure predictable session transitions, prevent state corruption, and eliminate ordering confusion.

#### State Definitions and Transition Rules

| State ID | State Name | Operational Mechanics | Exit Trigger / Transition Rules |
|---:|---|---|---|
| 0 | Attract / Idle | Renders high-definition looping marketing media. No active customer session data exists in memory. | Screen touch event → transition to State 1. |
| 1 | Category / Menu | Queries the local Edge Node SQLite database to render category grids, schedule-based dayparts (e.g., Breakfast vs. Lunch), and active items. | Category/item selected → transition to State 2. |
| 2 | Item Customization | Captures modifier additions and removals (e.g., “no onions”), required group selections, and updates running financial totals in real time. | Add to cart → return to State 1; tap “Checkout” → transition to State 3. |
| 3 | Upsell Evaluation | Evaluates cart contents against the local rule-based upsell engine and displays a single targeted add-on modal. | Accept or decline offer → transition to State 4. |
| 4 | Payment Processing | Locks cart modifications, invokes the provider-neutral payment interface, and waits for its result. The MVP uses a clearly labelled deterministic mock adapter. | Payment approved → transition to State 5; decline, cancellation, or known failure → revert to State 2; unknown outcome → show recoverable resolution status without blind retry. |
| 5 | Kitchen Dispatch | Formats a structured payload with transaction UUID and modifier SKUs; sends it through the kitchen adapter. The MVP uses a deterministic mock adapter. | Required kitchen outcome acknowledged → transition to State 6; recoverable failure is persisted and reported. |
| 6 | Order Confirmation | Renders a large-text order reference number and starts a 10-second auto-reset timer. Receipt printing and SMS/email capture are future peripheral integrations. | Timer expires (10 seconds) or user taps “Done” → scrub session and return to State 0. |

#### State Machine Detailed Requirements

- **FR-STATE-001** — Cart Preservation on Payment Failure: If payment fails in State 4 (declined card, timeout, tap read error), the system shall revert the user directly to State 2 with an explicit, non-intrusive notification banner. The customer's customized cart contents shall remain completely intact.

- **FR-STATE-002** — Automatic Session Reset: If no touch interaction occurs for 30 consecutive seconds during States 1, 2, or 3, the application shall render an overlay countdown prompt ("Are you still there? 10 seconds remaining"). If no touch occurs before the countdown hits zero, the session shall terminate, all personal customer data shall be scrubbed from RAM, and the application shall reset to State 0.

- **FR-STATE-003** — Touch Event Debouncing: UI touch inputs shall enforce a 150ms debounce threshold to prevent unintentional double-tap submissions on item additions or payment triggers.

- **FR-STATE-004** — Independent Dispatches: After an approved payment, the
  edge service shall persist kitchen and POS dispatch records atomically with
  the payment result. Kitchen and POS outcomes are independent. A POS timeout
  is retried asynchronously and shall not reverse a paid order or keep the
  customer in checkout.

### 3.2 Menu Architecture & Offline Synchronization Strategy

The system shall utilize a Cloud-Master / Store-Replica Data Architecture to balance central administration with edge execution.

For the MVP, the Store Edge Node is seeded with a local menu and evaluates
dayparts locally. Cloud authoring, manager portal access, WebSocket propagation,
delta synchronization, and split-brain reconciliation are future integrations.
The MVP nevertheless preserves store-specific item and modifier override data
for later use.

#### Menu Synchronization Requirements

- **FR-MENU-001** — Cloud Master Data Sourcing: Global menu structures, category mappings, item modifier trees, pricing tiers, tax profiles, and dynamic schedule rules shall be authored centrally in the Cloud Management Console.

- **FR-MENU-002** — Local Execution Copy: The Store Edge Node shall maintain an embedded SQLite database containing a pre-rendered copy of the active store menu. All kiosk queries shall execute locally against this Store Edge Node over LAN, ensuring sub-second UI responses.

- **FR-MENU-003** — Autonomous Dayparting: Transitioning between schedule-based menus (e.g., Breakfast to Lunch at 10:30 AM) shall evaluate locally against the Store Edge Node internal system clock without issuing cloud API calls.

- **FR-MENU-004** — Local Manager Overrides (86ing): The Store Edge Node shall host a localized, password-protected Web Manager Portal accessible via local store Wi-Fi/LAN. Store managers shall have the ability to toggle items or modifiers as "Out of Stock".

- **FR-MENU-005** — Sub-Second State Propagation: When an item is marked out of stock on the Manager Portal, the Store Edge Node shall broadcast a WebSocket message across the local LAN, updating all connected kiosk screens in ≤ 500ms without requiring application reboots.

- **FR-MENU-006** — Delta Reconnection Synchronization: Upon internet restoration following an outage, the Store Edge Node shall query the Cloud Master using an immutable menu version hash. If the hashes differ, the Edge Node shall stream only the specific modified database entities (delta payload) rather than re-downloading the entire catalog.

- **FR-MENU-007** — Split-Brain Conflict Resolution: Active manual out-of-stock locks applied by the store manager during an outage shall take precedence over incoming cloud menu sync payloads until explicitly cleared by store staff or cleared via schedule reset rules.

### 3.3 Payment Infrastructure & Store-and-Forward Engine

The kiosk application shall process payments directly via connected hardware card readers, avoiding checkout dependencies on legacy POS registers.

For the MVP, this section defines the future adapter contract only. The
provider and terminal are unselected, so the implementation uses a
provider-neutral mock adapter with deterministic approved, declined, cancelled,
timeout, and error scenarios. FR-PAY-001 through FR-PAY-005 are **Future
integration** requirements and cannot be represented as verified behavior until
the selected provider and hardware support them.

#### Payment Processing Requirements

- **FR-PAY-001** — Direct Payment Terminal SDK Integration: The kiosk application shall communicate directly with integrated card reader hardware using local vendor SDKs (e.g., Stripe Terminal, Square, Verifone, or Ingenico) to trigger authorization requests.

- **FR-PAY-002** — P2PE Tokenization: The payment reader shall perform hardware-level encryption at the swipe/insert/tap head. The kiosk software layer shall only handle encrypted transaction tokens and payment metadata.

- **FR-PAY-003** — Offline Store-and-Forward Engine: If internet connectivity drops, supported payment readers shall automatically switch to offline store-and-forward mode. Encrypted payment authorization payloads shall be buffered in an encrypted SQLite database queue on the Store Edge Node.

- **FR-PAY-004** — Offline Risk Controls: The Store Edge Node shall enforce configurable risk thresholds during offline payment mode:

  - Maximum single offline transaction value cap (default: $50.00).
  - Maximum cumulative offline transactions per individual card (default: 3 transactions).
  - Maximum total offline transaction queue velocity per store.

- **FR-PAY-005** — Idempotent Queue Flushing: When internet connectivity is re-established, the Store Edge Node shall flush buffered payment tokens to the payment gateway asynchronously. Every payload shall carry a client-generated UUID and timestamp to ensure zero duplicate charges.

### 3.4 Downstream System Integrations (POS, KDS, ERP)

The system shall act as an additive intake channel through a decoupled Integration Adapter Layer.

For the MVP, adapters are deterministic mocks behind stable interfaces. Their
payloads, idempotency, persistence, and retry behavior are tested locally; no
claim is made that a physical kitchen, POS, printer, or ERP receives an order.

#### Integration Requirements

- **FR-INT-001** — Sub-Second Local KDS Dispatch: Upon successful payment authorization (State 5), the Store Edge Node shall format and transmit a structured order payload over local TCP/IP sockets directly to Kitchen Display Systems (KDS) and kitchen thermal printers in ≤ 1.0 second.

- **FR-INT-002** — Passive POS Order Injection: Following payment completion, the Store Edge Node shall post the finalized transaction payload to the local POS via local REST APIs or webhooks.

- **FR-INT-003** — Virtual Register Mapping: The POS adapter shall register kiosk sales under a designated Virtual Terminal ID (e.g., REGISTER_KIOSK_01 ), preserving channel-specific sales reporting while keeping end-of-day register audits unified.

- **FR-INT-004** — Ingredient-Level ERP Deductions: Order payloads shall carry primary product Stock Keeping Units (SKUs) and granular modifier SKUs, allowing downstream ERP middleware to perform precise inventory decrements.

- **FR-INT-005** — Local Concurrency Load Shedding: The Store Edge Node shall support up to 8 active parallel kiosk connections per store, maintaining order queue response times ≤ 200ms under simultaneous active checkouts.

## 4. External Interface Requirements

### 4.1 User Interfaces & Accessibility Standards

- Touch Screen Hit Area: Interactive buttons and touch targets shall maintain a minimum touch boundary of 48 × 48 pixels with a minimum 8px visual spacing margin.

- Visual Hierarchy: Running cart totals, item customization modifiers, and tax additions must remain clearly visible across States 1 through 4.

- **FR-ACC-001** — Physical Reach Bounds (ADA Section 508): The application shall provide an "Accessibility Mode" toggle that lowers all primary touch targets and category menus to the lower 15 to 48 inches zone of the physical screen.

- **FR-ACC-002** — WCAG 2.1 Level AA Compliance: Visual text elements shall maintain a minimum color contrast ratio of 4.5:1 against background containers. High-contrast toggle modes shall be natively supported.

- **FR-ACC-003** — Audio & Visual Cues: Every user action (item addition, cart change, payment prompt) shall be accompanied by dynamic on-screen visual confirmation modals and clear, low-frequency audio tones for sight-impaired users.

### 4.2 Hardware Interfaces

#### Kiosk Terminal Component Specifications

Commercial Touch Screen Display: 21.5-inch to 32-inch PCAP (Projected Capacitive) multi-touch display with anti-glare, commercial-grade tempered glass.

Integrated Payment Terminal: PCI-P2PE certified payment sled supporting Contactless NFC (Apple Pay, Google Pay, contactless cards), EMV Smart Chip, and Magnetic Stripe.

Thermal Receipt Printer: Heavy-duty 80mm thermal receipt printer with automated paper cutter, paper-low optical sensor, and paper-jam detection.

Optical Scanner: Integrated 2D omnidirectional barcode scanner for loyalty mobile app QR codes and promotional vouchers.

### 4.3 Software & Communication Interfaces

#### Protocol and Interface Specifications

| Communication Path | Transport Protocol | Serialization Format | Purpose and Description |
|---|---|---|---|
| Kiosk → Store Edge Node | REST over local HTTP + JSON | JSON | MVP API for local menus, validated pricing, orders, payment status, and integration status. WebSockets are added only when a verified MVP need exists. |
| Kiosk → Payment Reader | Provider-neutral edge adapter | Typed internal contract | MVP mock adapter; direct USB/LAN/Serial vendor SDK integration is future work. |
| Edge Node → Kitchen KDS | Kitchen adapter | Validated payload | MVP mock adapter; TCP sockets, WebSockets, or printer protocols are selected later. |
| Edge Node → Local POS | POS adapter | Validated payload | MVP mock adapter with idempotent retry; live REST/WebSocket integration is future work. |
| Edge Node → Cloud Backend | Future integration | JSON | Menu sync, analytics, and queue flushing are not MVP capabilities. |

## 5. Non-Functional Requirements (NFRs)

### 5.1 Performance & Latency Benchmarks

The following platform targets guide future validation. The MVP verifies local
functional behavior only and does not claim production performance or
availability SLAs.

- **NFR-PERF-01** — UI Touch Latency: System touch-to-screen visual feedback response time shall be ≤ 100ms.

- **NFR-PERF-02** — Local Screen Render: Transitioning between menu categories or rendering customization modal options shall take ≤ 200ms.

- **NFR-PERF-03** — Kitchen Dispatch Speed: Time elapsed between card approval (State 4)

and kitchen prep display rendering (State 5) shall be ≤ 1.0 second over the local LAN.

### 5.2 Security & Data Privacy

The MVP enforces no-PAN handling, server-side validation, parameterized
database access, safe error responses, restricted local-network configuration,
and structured logging without payment-sensitive data. OS kiosk lockdown,
SQLCipher/TPM key management, and hardware controls remain deployment or future
integration work.

- **NFR-SEC-01** — OS Shell Locking (Kiosk Mode): Terminals shall run dedicated operating

system enclosure software (Android Kiosk Mode, Windows Assigned Access, or custom Linux shell lock) preventing access to underlying file systems, desktop environments, or external browser windows.

- **NFR-SEC-02** — Hardware TPM Key Management: Local SQLite databases (SQLCipher AES-256) on the Store Edge Node shall store encryption keys inside a hardware Trusted Platform Module (TPM 2.0) or Secure Enclave, eliminating hardcoded software keys.

- **NFR-SEC-03** — Memory Scrubbing: Transient customer session data (loyalty identifiers, phone numbers, custom cart choices) must be immediately cleared from active application memory upon entering State 0 or triggering an inactivity timeout.

### 5.3 Reliability, Availability, & Fault Isolation

- **NFR-REL-01** — Continuous Sales Availability: The customer ordering and checkout loop shall operate with 99.99% availability within store operational hours, completely unaffected by central cloud server outages or external internet disruptions.

- **NFR-REL-02** — Fault Isolation Boundaries: Failure or latency spikes in external non-critical services (e.g., third-party loyalty engines, central analytics pipelines, or ERP inventory systems) shall be gracefully bypassed by the kiosk without stalling the checkout workflow.

### 5.4 Peripheral Health & Automated Error Recovery

#### Peripheral Failure and Degradation Matrix

| Component | Failure Mode | System Detection Method | Automated Recovery Protocol |
|---|---|---|---|
| Thermal Printer | Paper out / paper jam | Hardware optical sensor trigger or status code via USB/Serial SDK | Suppress physical receipt printing in State 6; default to SMS/email receipt or large on-screen order number. |
| Payment Terminal | Disconnected / unresponsive | Keep-alive heartbeat ping fails for more than 3 seconds | Display a non-intrusive warning on the terminal; auto-reboot the reader SDK service; place the kiosk out of service if recovery fails within 30 seconds. |
| Barcode Scanner | Hardware freeze / read timeout | Optical sensor ping timeout | Disable the barcode scan prompt in the UI; provide a numeric keypad for manual loyalty phone-number entry. |
| Kitchen KDS | LAN socket disconnect | TCP socket connection drop or missing ACK payload for more than 1 second | Buffer the order ticket in the local Store Edge Node queue; trigger a backup kitchen thermal printer over a secondary IP. |

## 6. Data Schemas and API Payload Specifications

### 6.1 Order Dispatch Payload Specifications (Kiosk → Store Edge Node → POS)

The payload transmitted over local network calls upon payment completion shall conform to the following field specifications.

| Attribute Name | Data Type | Requirement Level | Description and Validation Rules |
|---|---|---|---|
| `transaction_id` | String (UUID v4) | Mandatory | 36-character canonical identifier ensuring strict transaction idempotency. |
| `terminal_id` | String | Mandatory | Unique hardware identifier associated with the originating kiosk. |
| `store_id` | String | Mandatory | Location identifier associated with the active store branch. |
| `timestamp` | String (ISO 8601) | Mandatory | High-resolution UTC timestamp representing completion time. |
| `order_type` | Enum | Mandatory | Service destination mode: `DINE_IN` or `TAKE_OUT`. |
| `order_status` | Enum | Mandatory | MVP dispatch state is `PAID`; `PENDING_OFFLINE` is reserved for a future provider-supported store-and-forward flow. |
| `virtual_register_id` | String | Mandatory | Target POS register mapping (e.g., `REGISTER_KIOSK_01`). |
| `financials` | Nested object | Mandatory | Includes `currency` (ISO 4217), `subtotal_minor`, `tax_amount_minor`, `tip_amount_minor`, and `total_amount_minor` as integer minor units. |
| `payment_metadata` | Nested object | Mandatory | A discriminated object. A provider result includes the permitted processor, entry mode, authorization code, token/reference, and offline flag. A mock result includes `is_simulated: true` and its scenario, with provider references absent. |
| `items` | Array of objects | Mandatory | Ordered items. Each item contains `line_item_id`, `item_sku`, `item_name`, `quantity`, `base_unit_price_minor`, and a nested `modifiers` array (`modifier_group_id`, `modifier_sku`, `modifier_name`, `price_delta_minor`). |

The transaction UUID is the idempotency key for an order. Each downstream
destination receives a stable dispatch idempotency key. A result whose delivery
or payment outcome is unknown must be resolved by status lookup before retry.

## 7. Phased Scope & Delivery Roadmap

To maximize delivery momentum and mitigate operational risk, platform features are divided across three planned development phases.

### Phase 1: Minimum Viable Product (Current Prototype Scope)

- **Interactive UI Engine:** Category menu browsing, dynamic schedule switching (e.g., Breakfast vs. Lunch), and real-time total calculations for custom modifiers.

- **Rule-Based Upsell Engine:** Single modal prompt prior to checkout presenting a targeted add-on suggestion based on cart contents.

- **Mock Payments & Local Dispatch:** Provider-neutral mock payment outcomes,
  deterministic kitchen dispatch, persisted idempotent retry records, and a
  clearly labelled simulated customer journey.

- **Decoupled Mock POS Injection:** Validated post-payment payloads sent to a
  deterministic mock POS adapter using a seeded virtual-register mapping.

- **Basic Accessibility Controls:** ADA lower-screen toggle and high-contrast display modes.

- **WAN-Interrupted Local Operation:** Menu, pricing, ordering, and mocks
  continue when internet access is unavailable but the kiosk remains connected
  to its Store Edge Node. Edge-isolated checkout is not part of this phase.

### Phase 2: Analytics and Loyalty Integration

**Store Manager Dashboard:** Real-time analytics tracking rush-hour order throughput, upsell acceptance rates, and order funnel abandonment points.

- **Loyalty & Barcode Scanning:** Integrated 2D optical reader support for customer barcode scanning, enabling loyalty point accrual and promotional coupon redemption.

- **Real-Time Inventory Sync:** Automated menu item toggles tied directly to store inventory stock levels.

- **Live Integration Enablement:** Selected payment-terminal SDK, live KDS/
  printer and POS adapters, authenticated manager portal, and verified
  availability propagation.

### Phase 3: Multi-Store Fleet Automation and Scaling

**Remote Fleet Management and MDM:** Automated central software deployment, screen locking, remote diagnostics, and hardware status monitoring across multiple locations.

- **Algorithmic Personalization:** Dynamic machine-learning recommendation prompts based on historic store trends, time of day, and weather inputs.
