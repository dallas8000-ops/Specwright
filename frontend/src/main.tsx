import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./styles/global.css";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 10_000, retry: 1 } },
});

const rootEl = document.getElementById("root");

function showBootError(message: string) {
  if (!rootEl) return;
  rootEl.innerHTML = `<div style="padding:2rem;font-family:system-ui,sans-serif;color:#f1f5f9;background:#1a2332;max-width:32rem;margin:2rem auto;border:1px solid #f87171;border-radius:12px"><h2 style="color:#f87171">Specwright failed to start</h2><p style="color:#94a3b8;margin:0.75rem 0">${message}</p><p style="font-size:0.85rem">Stop other Vite servers, run <code>npm run dev</code> in <code>frontend/</code>, and open the URL it prints.</p></div>`;
}

if (!rootEl) {
  showBootError("Missing #root element.");
} else {
  try {
    ReactDOM.createRoot(rootEl).render(
      <React.StrictMode>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </QueryClientProvider>
      </React.StrictMode>
    );
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Unknown error";
    showBootError(msg);
  }
}
