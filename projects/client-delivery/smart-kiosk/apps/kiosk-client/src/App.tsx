import { useEffect, useMemo, useState } from 'react';
import type { CartLine, OrderQuote, PaymentScenario } from '@smart-kiosk/shared';

const edgeUrl = import.meta.env.VITE_EDGE_URL ?? 'http://127.0.0.1:3001';

type Menu = {
  currencyCode: string;
  activeScheduleId: string;
  schedules: Array<{ schedule_id: string; schedule_name: string }>;
  categories: Array<{ category_id: string; category_name: string }>;
  items: Array<{
    menu_item_id: string;
    category_id: string;
    item_name: string;
    sku: string;
    base_price_minor: number;
  }>;
};

type Order = { transaction_id: string; order_status: string; total_amount_minor: number };

const formatMoney = (amount: number, currency = 'USD') =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount / 100);

export function App() {
  const [menu, setMenu] = useState<Menu>();
  const [cart, setCart] = useState<CartLine[]>([]);
  const [quote, setQuote] = useState<OrderQuote>();
  const [activeCategory, setActiveCategory] = useState<string>();
  const [message, setMessage] = useState('Loading local menu…');
  const [order, setOrder] = useState<Order>();
  const [highContrast, setHighContrast] = useState(false);
  const [lowerScreen, setLowerScreen] = useState(false);

  useEffect(() => {
    void loadMenu();
  }, []);

  useEffect(() => {
    if (cart.length === 0) {
      setQuote(undefined);
      return;
    }
    void fetch(`${edgeUrl}/v1/quotes`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ items: cart })
    })
      .then(async (response) => {
        if (!response.ok) throw new Error('Unable to update total');
        return (await response.json()) as OrderQuote;
      })
      .then(setQuote)
      .catch((error: unknown) => setMessage(error instanceof Error ? error.message : 'Unable to update total'));
  }, [cart]);

  const visibleItems = useMemo(
    () => menu?.items.filter((item) => !activeCategory || item.category_id === activeCategory) ?? [],
    [activeCategory, menu]
  );

  async function loadMenu(scheduleId?: string) {
    try {
      const response = await fetch(`${edgeUrl}/v1/menu${scheduleId ? `?scheduleId=${scheduleId}` : ''}`);
      if (!response.ok) throw new Error('Local edge service is unavailable');
      const data = (await response.json()) as Menu;
      setMenu(data);
      setActiveCategory(data.categories[0]?.category_id);
      setCart([]);
      setMessage(`Showing ${data.activeScheduleId.replace('schedule-', '')} menu`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Local edge service is unavailable');
    }
  }

  function addItem(menuItemId: string) {
    setCart((current) => {
      const existing = current.find((line) => line.menuItemId === menuItemId && line.modifiers.length === 0);
      if (!existing) return [...current, { menuItemId, quantity: 1, modifiers: [] }];
      return current.map((line) => (line === existing ? { ...line, quantity: line.quantity + 1 } : line));
    });
    setMessage('Added to cart');
  }

  async function checkout() {
    if (!quote || cart.length === 0) return;
    const response = await fetch(`${edgeUrl}/v1/orders`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ items: cart, idempotencyKey: crypto.randomUUID(), orderType: 'TAKE_OUT' })
    });
    if (!response.ok) return setMessage('Order could not be created. Review your cart and try again.');
    const created = (await response.json()) as Order;
    setOrder(created);
    setMessage('Order created. Choose a simulated payment outcome.');
  }

  async function pay(scenario: PaymentScenario) {
    if (!order) return;
    const response = await fetch(`${edgeUrl}/v1/orders/${order.transaction_id}/payment`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ scenario })
    });
    if (!response.ok) return setMessage('Payment could not be completed. Your cart remains available.');
    const updated = (await response.json()) as Order;
    setOrder(updated);
    if (updated.order_status === 'COMPLETED') {
      setMessage('Simulated payment approved. Mock kitchen and POS dispatches acknowledged.');
      setCart([]);
    } else {
      setMessage(`Simulated payment ${scenario.toLowerCase().replace('_', ' ')}. Your cart remains available.`);
      setOrder(undefined);
    }
  }

  const cardClass = highContrast ? 'border-white bg-black text-white' : 'border-slate-200 bg-white text-slate-900';
  const contentPosition = lowerScreen ? 'pt-24' : 'pt-8';

  return (
    <main className={`min-h-screen ${highContrast ? 'bg-black text-white' : 'bg-slate-50'} ${contentPosition}`}>
      <div className="mx-auto grid max-w-7xl gap-6 px-6 pb-10 lg:grid-cols-[1fr_22rem]">
        <section>
          <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm font-bold tracking-[0.2em] text-teal-700">SMART KIOSK · DEMO</p>
              <h1 className="text-4xl font-black">What can we make for you?</h1>
            </div>
            <div className="flex gap-2">
              <button className="min-h-12 rounded-lg border px-4 font-bold" onClick={() => setLowerScreen((value) => !value)}>
                Lower-screen mode
              </button>
              <button className="min-h-12 rounded-lg border px-4 font-bold" onClick={() => setHighContrast((value) => !value)}>
                High contrast
              </button>
            </div>
          </header>
          <p className="mb-5 rounded-lg bg-teal-50 p-3 text-sm font-semibold text-teal-950" role="status">{message}</p>
          <div className="mb-5 flex flex-wrap gap-2" aria-label="Meal schedule">
            {menu?.schedules.map((schedule) => (
              <button
                key={schedule.schedule_id}
                className={`min-h-12 rounded-lg px-5 font-bold ${menu.activeScheduleId === schedule.schedule_id ? 'bg-teal-700 text-white' : 'border'}`}
                onClick={() => void loadMenu(schedule.schedule_id)}
              >
                {schedule.schedule_name}
              </button>
            ))}
          </div>
          <div className="mb-5 flex flex-wrap gap-2" aria-label="Menu categories">
            {menu?.categories.map((category) => (
              <button
                key={category.category_id}
                className={`min-h-12 rounded-lg px-5 font-bold ${activeCategory === category.category_id ? 'bg-slate-900 text-white' : 'border'}`}
                onClick={() => setActiveCategory(category.category_id)}
              >
                {category.category_name}
              </button>
            ))}
          </div>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {visibleItems.map((item) => (
              <article key={item.menu_item_id} className={`rounded-2xl border p-5 shadow-sm ${cardClass}`}>
                <p className="text-xs font-bold tracking-widest text-teal-700">{item.sku}</p>
                <h2 className="mt-2 text-2xl font-extrabold">{item.item_name}</h2>
                <p className="mt-5 text-xl font-bold">{formatMoney(item.base_price_minor, menu?.currencyCode)}</p>
                <button className="mt-5 min-h-12 w-full rounded-lg bg-teal-700 px-4 font-bold text-white" onClick={() => addItem(item.menu_item_id)}>
                  Add to order
                </button>
              </article>
            ))}
          </div>
        </section>
        <aside className={`h-fit rounded-2xl border p-5 shadow-lg ${cardClass}`} aria-label="Order summary">
          <h2 className="text-2xl font-black">Your order</h2>
          <ul className="my-5 space-y-3">
            {cart.map((line) => {
              const item = menu?.items.find((candidate) => candidate.menu_item_id === line.menuItemId);
              return <li key={line.menuItemId} className="flex justify-between"><span>{line.quantity} × {item?.item_name ?? line.menuItemId}</span><span>{formatMoney((item?.base_price_minor ?? 0) * line.quantity, menu?.currencyCode)}</span></li>;
            })}
          </ul>
          <div className="border-t pt-4 text-xl font-black">Total: {formatMoney(quote?.totalAmountMinor ?? 0, menu?.currencyCode)}</div>
          {!order ? (
            <button disabled={!quote} className="mt-5 min-h-12 w-full rounded-lg bg-amber-500 px-4 font-extrabold text-slate-950 disabled:opacity-40" onClick={() => void checkout()}>
              Checkout
            </button>
          ) : (
            <div className="mt-5 space-y-2">
              <p className="font-bold">Simulated payment:</p>
              {(['APPROVED', 'DECLINED', 'CANCELLED', 'TIMED_OUT', 'FAILED'] as PaymentScenario[]).map((scenario) => (
                <button key={scenario} className="min-h-12 w-full rounded-lg border px-3 font-bold" onClick={() => void pay(scenario)}>{scenario.replace('_', ' ')}</button>
              ))}
            </div>
          )}
        </aside>
      </div>
    </main>
  );
}
