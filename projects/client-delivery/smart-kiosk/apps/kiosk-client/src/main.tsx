import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';
import { App } from './App';
import { ErrorFallback } from './ErrorFallback';

const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error('Smart Kiosk could not find its root element.');
}

createRoot(rootElement).render(
  <StrictMode>
    <ErrorFallback>
      <App />
    </ErrorFallback>
  </StrictMode>
);
