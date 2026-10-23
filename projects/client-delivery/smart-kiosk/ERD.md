## Overview

This document identifies the core entities, their attributes, and their purpose within the Smart Kiosk Edge-First QSR Platform.

The model covers store and kiosk management, order processing, payments, menu configuration, offline operations, and downstream integrations.

**Notation**
- **PK** — Primary Key
- **FK** — Foreign Key
- **SRS** — Explicitly described or supported by the System Requirements Specification
- **Proposed** — Suggested for a complete relational data model; not explicitly defined in the SRS

## Implementation Baseline

This ERD is governed by the MVP and implementation plan. It describes the
local prototype data model, including deterministic mock integrations; it does
not by itself authorize live payment, POS, kitchen, cloud-sync, or encrypted
store-and-forward implementation.

All persisted monetary values use integer minor units and every order stores an
ISO 4217 `currency_code`. Catalog records referenced by transactions are
soft-deactivated rather than hard-deleted. SQLite migrations use real foreign
keys, and transaction-time snapshots remain authoritative for historical
payloads.

---

# 1. Store

Represents a physical restaurant location operating one or more kiosk terminals.

### Attributes

| Attribute    | Key | Description                     |
| ------------ | --- | ------------------------------- |
| `store_id`   | PK  | Unique identifier for the store |
| `store_name` |     | Store's display name            |
| `address`    |     | Physical store address          |
| `timezone`   |     | Store's local timezone          |
| `created_at` |     | Record creation timestamp       |

The platform operates within individual stores, each with its own Store Edge Node, kiosks, local menu replica, and integrations. A Store entity provides the organizational boundary for these resources and supports store-specific configuration.

The SRS establishes the store-level architecture but does not define a complete Store table schema. The attributes above are proposed.

---

# 2. Kiosk Terminal

Represents a physical kiosk used by customers to browse the menu, customize items, and place orders.

### Attributes

| Attribute | Key | Description |
|---|---|---|
| `terminal_id` | PK | Unique identifier for the kiosk |
| `store_id` | FK | Store where the kiosk is installed |
| `terminal_name` | | Human-readable terminal name |
| `status` | | Current operational status |
| `last_seen_at` | | Most recent reported activity |
| `created_at` | | Record creation timestamp |

The SRS identifies the Kiosk Client Terminal as the customer-facing ordering interface. For the MVP, a terminal shows an unavailable state if the Store Edge Node becomes unreachable; edge-isolated browsing or checkout is future scope.

A separate entity allows terminals to be identified, associated with a store, and monitored independently.

The `terminal_id` is explicitly present in the order payload. The remaining attributes are proposed for device management and diagnostics.

---

# 3. Order

Represents a customer transaction from order creation through payment and downstream processing.

### Attributes

| Attribute | Key | Description |
|---|---|---|
| `transaction_id` | PK | Unique order/transaction UUID |
| `terminal_id` | FK | Kiosk that created the order |
| `store_id` | FK | Store where the order was placed |
| `order_type` | | Order type |
| `order_status` | | Current order state |
| `created_at` | | Order creation timestamp |
| `currency_code` | | ISO 4217 currency for all financial values |
| `subtotal_minor` | | Order subtotal in integer minor units |
| `tax_amount_minor` | | Applied tax in integer minor units |
| `tip_amount_minor` | | Tip in integer minor units; `0` for the MVP |
| `total_amount_minor` | | Final transaction total in integer minor units |
| `virtual_register_id` | FK | POS register mapping |
| `updated_at` | | Most recent order update |

The order is the central business entity connecting customer selections, payment processing, and kitchen/POS dispatch.

The SRS defines a structured order payload containing a transaction UUID, terminal and store identifiers, timestamps, order type and status, financial values, payment metadata, and item details.

A dedicated Order entity provides the parent record for order items and payments while allowing the same transaction to be referenced by downstream integrations.

For the MVP, the order status is one of `DRAFT`, `AWAITING_PAYMENT`, `PAID`,
`FULFILLMENT_PENDING`, `COMPLETED`, `CANCELLED`, or `PAYMENT_FAILED`.
The UUID and core payload fields are SRS-supported. `updated_at`, integer minor
units, and the relational foreign-key structure are proposed implementation
decisions.

---

# 4. Order Item

Represents an individual menu item included in an order.

### Attributes

| Attribute            | Key | Description                     |
| -------------------- | --- | ------------------------------- |
| `order_item_id`      | PK  | Unique order-line identifier    |
| `transaction_id`     | FK  | Order containing the item       |
| `menu_item_id`       | FK  | Corresponding menu item         |
| `quantity`           |     | Number of units ordered         |
| `unit_price_minor`   |     | Price per unit at purchase time in integer minor units |
| `line_total_minor`   |     | Total for the order line in integer minor units |
| `item_name_snapshot` |     | Item name at time of purchase   |
| `item_sku_snapshot`  |     | Product SKU at time of purchase |

The SRS specifies that order payloads contain item arrays and that primary product SKUs are passed downstream for inventory deductions.

An Order Item entity represents each purchased product separately, supports quantities and line-level pricing, and connects the transaction to the menu catalog.

The item relationship and SKU requirement are supported by the SRS. The individual relational fields and snapshot attributes are proposed. Price and name snapshots preserve the details of the original purchase if the menu changes later.

---

# 5. Payment

Represents a payment attempt or payment transaction associated with an order.

### Attributes

| Attribute           | Key | Description                               |
| ------------------- | --- | ----------------------------------------- |
| `payment_id`        | PK  | Unique payment identifier                 |
| `transaction_id`    | FK  | Associated order                          |
| `payment_status`    |     | Payment processing status                 |
| `payment_method`    |     | Payment method or reader type             |
| `amount`            |     | Payment amount                            |
| `payment_token`     |     | Encrypted payment token/reference         |
| `gateway_reference` |     | Payment gateway transaction reference     |
| `is_offline`        |     | Whether the payment was processed offline |
| `created_at`        |     | Payment creation timestamp                |
| `authorized_at`     |     | Authorization timestamp                   |

The future platform requires direct payment-terminal integration, hardware-level encryption, encrypted payment tokens, payment metadata, and support for offline store-and-forward processing. The MVP models the permitted fields but uses only clearly labelled simulated results.

A separate Payment entity isolates payment state from order state and allows an order to be associated with its payment records.

The model must not store raw card numbers (PANs). Payment data should consist of permitted encrypted tokens and metadata, consistent with the SRS's security requirements.

The payment processing requirements are explicit; the exact table structure and several attributes are proposed.

### MVP Migration Refinement

The physical `payments` table adds `attempt_number`, `amount_minor`, and
`is_simulated`. `payment_token` and `gateway_reference` are nullable for a
simulated payment and must never contain fabricated provider values. Enforce a
unique `(transaction_id, attempt_number)` constraint. Allowed statuses are
`INITIATED`, `PENDING`, `APPROVED`, `DECLINED`, `CANCELLED`, `FAILED`,
`TIMED_OUT`, and `UNKNOWN`; an `UNKNOWN` result requires a safe status lookup
before retry.

---

# 6. Order Item Modifier

Represents a modifier selected for a specific order item.

### Attributes

| Attribute                | Key | Description                                |
| ------------------------ | --- | ------------------------------------------ |
| `order_item_modifier_id` | PK  | Unique selected-modifier record            |
| `order_item_id`          | FK  | Order item being customized                |
| `modifier_id`            | FK  | Selected menu modifier                     |
| `quantity`               |     | Quantity of the modifier, where applicable |
| `modifier_price`         |     | Price added by the modifier                |
| `modifier_name_snapshot` |     | Modifier name at purchase time             |
| `modifier_sku_snapshot`  |     | Modifier SKU at purchase time              |

The SRS supports customer item customization and requires granular modifier SKUs to accompany order payloads for ingredient-level ERP deductions.

This entity records the actual modifiers selected for a purchased item. It distinguishes the available modifier catalog from the customer's selections in a particular order.

The modifier relationship is supported by the SRS. The specific table and snapshot attributes are proposed.

The physical order-item-modifier record also stores
`modifier_group_id_snapshot` and `modifier_price_minor`, so dispatch payloads
remain historically correct after catalog changes.

---

# 7. Menu Category

Represents a category used to organize menu items.

### Attributes

| Attribute       | Key | Description                    |
| --------------- | --- | ------------------------------ |
| `category_id`   | PK  | Unique category identifier     |
| `category_name` |     | Category name                  |
| `description`   |     | Optional category description  |
| `display_order` |     | Position in the kiosk menu     |
| `is_active`     |     | Whether the category is active |

The SRS describes centrally managed menu structures and category mappings, with a local menu replica used by kiosks.

A Menu Category entity organizes menu items into browsable groups and supports consistent category presentation across terminals.

The category structure is SRS-supported. The exact fields are proposed.

---

# 8. Menu Item

Represents a product available for purchase through the kiosk.

### Attributes

| Attribute      | Key | Description                 |
| -------------- | --- | --------------------------- |
| `menu_item_id` | PK  | Unique menu item identifier |
| `category_id`  | FK  | Menu category               |
| `item_name`    |     | Display name                |
| `description`  |     | Item description            |
| `sku`          |     | Product Stock Keeping Unit  |
| `base_price`   |     | Standard item price         |
| `is_active`    |     | Whether the item is active  |
| `created_at`   |     | Record creation timestamp   |
| `updated_at`   |     | Most recent update          |

Menu items are central to the ordering process. The SRS specifies that the centrally managed menu includes items, pricing, and related customization data, and that the Store Edge Node maintains a local copy for offline operation.

A Menu Item entity provides the catalog record referenced by order lines and store-specific availability overrides.

The menu, pricing, and SKU concepts are supported by the SRS. The proposed fields provide a relational representation. The physical price field is
`base_price_minor`; records are deactivated rather than deleted when referenced
by an order.

---

# 9. Modifier Group

Represents a group of customization options, such as size, toppings, or add-ons.

### Attributes

| Attribute           | Key | Description                            |
| ------------------- | --- | -------------------------------------- |
| `modifier_group_id` | PK  | Unique modifier group identifier       |
| `group_name`        |     | Name of the customization group        |
| `selection_type`    |     | Single-select or multi-select behavior |
| `min_selections`    |     | Minimum number of selections           |
| `max_selections`    |     | Maximum number of selections           |
| `is_required`       |     | Whether selection is required          |

The SRS describes item modifier trees and customer-facing customization choices.

A Modifier Group organizes related modifiers and can represent selection rules that the kiosk must enforce during customization.

The existence of modifier groupings is supported by the SRS's menu and customization requirements. The specific selection-rule fields are proposed because the SRS does not define their exact schema. For the MVP, selection bounds belong to the menu-item/group relationship rather than the reusable group itself.

---

# 10. Modifier

Represents an individual customization option available for a menu item.

### Attributes

| Attribute           | Key | Description                        |
| ------------------- | --- | ---------------------------------- |
| `modifier_id`       | PK  | Unique modifier identifier         |
| `modifier_group_id` | FK  | Group containing the modifier      |
| `modifier_name`     |     | Modifier display name              |
| `modifier_sku`      |     | Modifier SKU                       |
| `price_adjustment`  |     | Additional cost or price reduction |
| `is_active`         |     | Whether the modifier is active     |

Modifiers allow customers to customize menu items. The SRS requires modifier trees, local menu execution, out-of-stock controls for modifiers, and modifier SKUs for downstream inventory deductions.

A Modifier entity stores the catalog definition of each option, while Order Item Modifier records which options were selected for a particular purchase.

The modifier and SKU concepts are supported by the SRS. The exact attributes are proposed. The physical price field is `price_adjustment_minor`.

---

# 11. Menu Schedule / Daypart

Represents a time-based menu schedule, such as breakfast or lunch.

### Attributes

| Attribute       | Key | Description                    |
| --------------- | --- | ------------------------------ |
| `schedule_id`   | PK  | Unique schedule identifier     |
| `store_id`      | FK  | Store using the schedule       |
| `schedule_name` |     | Schedule or daypart name       |
| `start_time`    |     | Local start time               |
| `end_time`      |     | Local end time                 |
| `days_of_week`  |     | Applicable days                |
| `is_active`     |     | Whether the schedule is active |

The SRS requires autonomous dayparting. The Store Edge Node evaluates schedule-based menus locally using its internal clock, without requiring cloud API calls.

A Menu Schedule entity represents when a particular menu or daypart should be active. It supports time-based menu transitions while preserving local operation during internet outages.

Schedule rules and local evaluation are explicitly described in the SRS. The proposed fields are one possible relational implementation.

---

# 12. Menu Item Schedule

A junction entity linking menu items to the schedules in which they are
available.

### Attributes

| Attribute      | Key    | Description |
| -------------- | ------ | ----------- |
| `schedule_id`  | PK, FK | Applicable store daypart |
| `menu_item_id` | PK, FK | Item available in that daypart |

This junction makes the daypart executable: a menu item is available only when
it is active, has an active applicable schedule, and has no active store
availability override. Evaluate schedules in the store's IANA timezone using
start-inclusive, end-exclusive intervals. Reject overlapping active schedules
unless an explicit priority is later added.

---

# 13. Menu Item Modifier Group

A junction entity linking menu items to the modifier groups available for them.

### Attributes

| Attribute           | Key    | Description                                 |
| ------------------- | ------ | ------------------------------------------- |
| `menu_item_id`      | PK, FK | Associated menu item                        |
| `modifier_group_id` | PK, FK | Associated modifier group                   |
| `display_order`     |        | Position of the group in customization      |
| `min_selections`    |        | Minimum selections required for this item |
| `max_selections`    |        | Maximum selections allowed for this item |

A menu item may expose one or more modifier groups, and a modifier group may be reused by multiple menu items.

The junction entity represents this many-to-many relationship without duplicating modifier group definitions for every item. A group is required when `min_selections > 0`; `max_selections = 1` represents single selection.

The SRS describes item modifier trees and customization choices, but does not explicitly prescribe this junction table. It is a proposed relational design.

---

# 14. Offline Payment Queue

Represents encrypted payment payloads waiting to be transmitted when connectivity is restored.

### Attributes

| Attribute          | Key | Description                               |
| ------------------ | --- | ----------------------------------------- |
| `queue_id`         | PK  | Unique queue record identifier            |
| `payment_id`       | FK  | Associated payment                        |
| `transaction_uuid` |     | Client-generated idempotency UUID         |
| `payload`          |     | Encrypted payment authorization payload   |
| `queued_at`        |     | Time the payload entered the queue        |
| `queue_status`     |     | Pending, processing, completed, or failed |
| `retry_count`      |     | Number of transmission attempts           |
| `last_attempt_at`  |     | Most recent transmission attempt          |

The SRS explicitly requires an encrypted SQLite queue on the Store Edge Node for offline payment authorization payloads. Once connectivity returns, the system asynchronously flushes the queue to the payment gateway.

The queue needs to preserve payloads until processing completes and use a client-generated UUID and timestamp to prevent duplicate charges.

The offline queue, encryption, and idempotency requirements are explicit. The table structure and retry-tracking fields are proposed.

**MVP scope note:** Create this schema only as a feature-gated placeholder and
do not enqueue any payload during the prototype. It may be activated only after
a selected provider and terminal support secure store-and-forward processing
and encrypted storage has been verified.

**Security note:** The payload must contain only permitted encrypted payment data. Raw PANs must never be stored by the kiosk software or local database.

---

# 15. Menu Version

Represents a version of the centrally managed menu replicated to a store.

### Attributes

| Attribute         | Key | Description                          |
| ----------------- | --- | ------------------------------------ |
| `menu_version_id` | PK  | Unique menu version record           |
| `store_id`        | FK  | Store holding the version            |
| `version_hash`    |     | Immutable menu version hash          |
| `created_at`      |     | Version creation timestamp           |
| `applied_at`      |     | Time the version was applied locally |
| `sync_status`     |     | Synchronization state                |

The SRS specifies cloud-master/store-replica menu architecture and delta synchronization. When connectivity returns, the Store Edge Node compares an immutable menu version hash and downloads only changed entities when necessary.

A Menu Version entity makes menu synchronization state explicit and provides a record of which version is associated with a store.

The version hash and synchronization behavior are supported by the SRS. The table and tracking fields are proposed.

---

# 16. Store Item Availability Override

Represents a store-level manual availability override for a menu item.

### Attributes

| Attribute      | Key | Description                      |
| -------------- | --- | -------------------------------- |
| `override_id`  | PK  | Unique override identifier       |
| `store_id`     | FK  | Store applying the override      |
| `menu_item_id` | FK  | Affected menu item               |
| `is_available` |     | Whether the item is available    |
| `reason`       |     | Optional reason for the override |
| `created_at`   |     | Time the override was created    |
| `expires_at`   |     | Optional expiration time         |
| `cleared_at`   |     | Time the override was cleared    |

The SRS requires store managers to mark items or modifiers out of stock through a local manager portal. These overrides must propagate rapidly to connected kiosks and take precedence over incoming cloud menu updates until cleared by staff or schedule-reset rules.

A separate override entity preserves the distinction between the centrally managed menu and temporary, store-specific availability.

The override behavior is explicit in the SRS. The table structure and timestamps are proposed.

**Modeling decision:** Use a separate `Store Modifier Availability Override`
entity with the same lifecycle and a `modifier_id` foreign key. Do not use a
polymorphic reference; this preserves SQLite foreign-key enforcement. Enforce
at most one active override per store/item and per store/modifier.

---

# 17. Store Modifier Availability Override

Represents a store-level manual availability override for a modifier.

### Attributes

| Attribute      | Key | Description |
| -------------- | --- | ----------- |
| `override_id`  | PK  | Unique override identifier |
| `store_id`     | FK  | Store applying the override |
| `modifier_id`  | FK  | Affected modifier |
| `is_available` |    | Whether the modifier is available |
| `reason`       |    | Optional reason for the override |
| `created_at`   |    | Time the override was created |
| `expires_at`   |    | Optional expiration time |
| `cleared_at`   |    | Time the override was cleared |

This entity mirrors the item-override lifecycle while retaining a real foreign
key to `Modifier`. At most one active override exists per `(store_id,
modifier_id)`.

---

# 18. Integration Dispatch

Represents an order or transaction payload sent to a downstream system.

### Attributes

| Attribute          | Key | Description                             |
| ------------------ | --- | --------------------------------------- |
| `dispatch_id`      | PK  | Unique dispatch identifier              |
| `transaction_id`   | FK  | Associated order                        |
| `destination_type` |     | KDS, printer, POS, or other destination |
| `destination_id`   |     | Specific destination or endpoint        |
| `payload`          |     | Structured outbound payload             |
| `dispatch_status`  |     | Pending, sent, failed, or acknowledged  |
| `idempotency_key`  |     | Stable idempotency key for this destination |
| `created_at`       |     | Dispatch creation timestamp             |
| `sent_at`          |     | Time the payload was sent               |
| `retry_count`      |     | Number of retry attempts                |
| `next_attempt_at`  |     | Scheduled retry time                    |
| `last_error`       |     | Sanitized latest error                  |
| `last_response_at` |     | Latest destination response time         |

The SRS describes a decoupled Integration Adapter Layer that routes orders to kitchen display systems, thermal printers, and the local POS. It also describes ERP inventory deductions through downstream middleware.

An Integration Dispatch entity separates order creation from delivery to external systems. It can track delivery status and retries independently for each destination.

The integration destinations and routing requirements are supported by the SRS. The dispatch table and tracking fields are proposed. Enforce a unique
`(transaction_id, destination_type, destination_id)` constraint. Allowed
statuses are `PENDING`, `IN_FLIGHT`, `ACKNOWLEDGED`, `FAILED_RETRYABLE`,
`FAILED_FINAL`, and `UNKNOWN`.

---

# 19. POS Register

Represents a POS register identifier used to classify kiosk sales within the existing POS system.

### Attributes

| Attribute             | Key | Description                        |
| --------------------- | --- | ---------------------------------- |
| `virtual_register_id` | PK  | Unique register mapping identifier |
| `store_id`            | FK  | Store associated with the register |
| `register_code`       |     | POS register code                  |
| `register_name`       |     | Human-readable register name       |
| `is_active`           |     | Whether the mapping is active      |

The SRS requires kiosk transactions to be posted to the existing POS using a designated Virtual Terminal ID, with `REGISTER_KIOSK_01` given as an example.

A POS Register entity stores this mapping separately from the order so that kiosk sales can be identified for channel-specific reporting while remaining part of the store's existing accounting workflow.

The virtual register mapping is explicitly described in the SRS. The relational entity and additional attributes are proposed.

---

# Entity Relationship Summary

| Entity | Relationship |
|---|---|
| Store | Has many Kiosk Terminals |
| Store | Has many Orders |
| Store | Has many Menu Schedules |
| Store | Has many Menu Versions |
| Store | Has many Availability Overrides |
| Store | Has many Modifier Availability Overrides |
| Store | Has many POS Register mappings |
| Kiosk Terminal | Creates many Orders |
| Order | Contains many Order Items |
| Order | Has associated Payment records |
| Order | Has many Integration Dispatch records |
| Order Item | References one Menu Item |
| Order Item | Has many Order Item Modifiers |
| Menu Category | Contains many Menu Items |
| Menu Item | Has many Order Items |
| Menu Item | Links to schedules through Menu Item Schedule |
| Menu Item | Links to Modifier Groups through Menu Item Modifier Group |
| Modifier Group | Contains many Modifiers |
| Modifier Group | Links to Menu Items through Menu Item Modifier Group |
| Modifier | Can appear in many Order Item Modifier records |
| Modifier | Can have store-specific availability overrides |
| Payment | Can have an Offline Payment Queue record |
| POS Register | Can be referenced by many Orders |
| Menu Item | Can have store-specific availability overrides |

---

# General Design Considerations

## 1. Separate Catalog Data from Transaction Data

Menu Category, Menu Item, Modifier Group, and Modifier represent the current catalog.

Order, Order Item, and Order Item Modifier represent what the customer actually purchased.

Keep transaction-time values such as item names, SKUs, and prices in order-line snapshots where needed. This prevents later menu edits from changing historical transaction details.

## 2. Preserve Order and Payment Identity

Use the SRS's transaction UUID as the stable transaction identifier. Keep payment processing state separate from order state, since payment authorization, order dispatch, and downstream acknowledgment are distinct operations.

## 3. Support Local Operation and Future Offline Payments

The Store Edge Node maintains the local menu replica, so the prototype can
operate through a WAN interruption while the kiosk remains connected to the
edge service. Menu versioning and the offline-payment queue preserve the
future model, but encrypted payment store-and-forward is feature-gated and is
not implemented or exercised by the MVP.

## 4. Keep Store Overrides Separate from the Master Menu

Manual out-of-stock changes are local operational overrides. They should not overwrite the centrally managed menu definition, and they must follow the SRS's conflict-resolution rules.

## 5. Track Downstream Delivery Independently

KDS, printer, POS, and other integration dispatches may have different delivery outcomes. Track each destination's dispatch status separately rather than treating a single order status as proof that every system received the order.

## 6. Pricing, Schedule, and Retry Invariants

The server revalidates a cart against active schedules and availability
overrides before checkout. Persisted transaction totals and snapshots are the
historical record. Order, payment, kitchen-dispatch, and POS-dispatch statuses
remain independent. A POS failure is retried independently and never by itself
reverses an approved payment.

## 7. Treat Proposed Attributes as Design Decisions

The SRS defines system behavior and several payload fields, but it does not provide a complete relational database schema for all 17 entities.

The proposed primary keys, foreign keys, normalization choices, status fields,
timestamps, and junction tables have been narrowed above for the MVP and
should be implemented as versioned SQLite migrations.
