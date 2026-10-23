# Smart Kiosk MVP

## MVP Definition

The MVP will deliver a functional self-service kiosk prototype that allows
customers to browse the menu, customize orders, complete a clearly labelled
simulated payment, and send orders to mock kitchen and POS adapters. It
establishes the local edge architecture and validated contracts required for
later hardware integrations; it does not claim to process live cards or submit
to live restaurant systems.

-   **Interactive Menu:** Customers can browse food categories, switch
    between meal menus (e.g., Breakfast and Lunch), and see prices
    update as they customize their orders.
-   **Smart Recommendations:** Before checkout, the kiosk suggests a
    relevant add-on based on the customer's order.
-   **Payments & Order Processing:** The prototype exercises a provider-neutral
    payment flow with deterministic approved, declined, cancelled, timeout, and
    error outcomes. Orders are sent to a mock kitchen adapter, with useful local
    operation during a simulated WAN interruption while the kiosk remains
    connected to its Store Edge Node.
-   **POS Integration:** Completed prototype orders are automatically sent to a
    deterministic mock POS adapter using the validated, idempotent payload
    contract intended for the eventual POS integration.
-   **Accessibility:** The interface includes a lower-screen mode for
    easier access and a high-contrast display option.

## MVP Boundary and Deferred Work

The prototype's local edge service is authoritative for menu availability,
pricing, order creation, payment state, and integration dispatch state. The
browser is never authoritative for totals or payment outcomes.

For this MVP, **offline** means loss of WAN/internet access while the kiosk can
still reach its Store Edge Node over the store LAN. If that edge service is
unreachable, the kiosk shows an unavailable state and does not accept checkout
or payment. The MVP does not implement or claim edge-isolated checkout,
offline card authorization, encrypted payment store-and-forward, cloud menu
synchronization, a manager portal, or live peripheral recovery.

Real payment terminal, POS, KDS/printer, and cloud integrations begin only
after their provider, hardware, protocol, credentials, and security capability
have been confirmed. Raw card data never enters the kiosk application or local
database.

## Expected Timeline for MVP

The MVP is expected to take 1--2 weeks, with the goal of delivering a
working prototype that demonstrates the kiosk's core features.

Days 1 - 2: Menu & Interface - Build the seeded local menu, meal schedules,
server-authoritative pricing, customization, and accessibility features. Days
3 - 4: Ordering Experience - Add order management, product recommendations,
state transitions, and mock kitchen dispatch. Days 5 - 7: Payments &
Integration - Implement provider-neutral payment, kitchen, and POS interfaces
with deterministic mocks; test the complete local customer journey.

If a second week is available, the focus will be on improving offline
functionality, fixing issues, and preparing the prototype for
demonstration.

This timeline assumes development hardware capable of running the browser and
local edge service. Live integration work additionally requires the applicable
hardware, credentials, network details, and vendor support. The goal is to
establish a working foundation that can be expanded in later development
stages.
