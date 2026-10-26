import { Component, type ErrorInfo, type ReactNode } from 'react';

type Props = { children: ReactNode };
type State = { error?: Error };

export class ErrorFallback extends Component<Props, State> {
  state: State = {};

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('Smart Kiosk frontend failed to render', error, info);
  }

  render(): ReactNode {
    if (!this.state.error) return this.props.children;
    return (
      <main className="grid min-h-screen place-items-center bg-slate-950 p-6 text-white">
        <section className="max-w-xl rounded-xl border border-amber-400 bg-slate-900 p-6 shadow-xl">
          <p className="font-bold tracking-widest text-amber-300">SMART KIOSK STARTUP ERROR</p>
          <h1 className="mt-3 text-2xl font-black">The kiosk UI could not render.</h1>
          <p className="mt-3 text-slate-200">Refresh after confirming the edge service and Vite development server are running.</p>
          <pre className="mt-4 overflow-auto rounded bg-black p-3 text-sm text-amber-100">{this.state.error.message}</pre>
        </section>
      </main>
    );
  }
}
