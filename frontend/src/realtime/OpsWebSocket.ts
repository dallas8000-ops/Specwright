import type { DomainEventEnvelope } from "./types";

type EventHandler = (event: DomainEventEnvelope) => void;
type StatusHandler = (status: "connecting" | "connected" | "disconnected" | "error") => void;

export class OpsWebSocket {
  private ws: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  private handlers = new Set<EventHandler>();
  private statusHandlers = new Set<StatusHandler>();
  private shouldReconnect = true;

  constructor(
    private getToken: () => string | null,
    private baseUrl = `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}`
  ) {}

  connect() {
    const token = this.getToken();
    if (!token) return;

    this.shouldReconnect = true;
    this.setStatus("connecting");
    const url = `${this.baseUrl}/ws/ops/?token=${encodeURIComponent(token)}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.setStatus("connected");
      this.pingTimer = setInterval(() => {
        this.ws?.send(JSON.stringify({ type: "ping", ts: Date.now() }));
      }, 25000);
    };

    this.ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data);
        if (data.type === "connection.established") return;
        if (data.type === "pong") return;
        if (data.type === "domain.event" || data.event_type) {
          this.handlers.forEach((h) => h(data as DomainEventEnvelope));
        }
      } catch {
        /* ignore malformed */
      }
    };

    this.ws.onclose = () => {
      this.setStatus("disconnected");
      this.clearPing();
      if (this.shouldReconnect) {
        this.reconnectTimer = setTimeout(() => this.connect(), 3000);
      }
    };

    this.ws.onerror = () => this.setStatus("error");
  }

  disconnect() {
    this.shouldReconnect = false;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.clearPing();
    this.ws?.close();
    this.ws = null;
    this.setStatus("disconnected");
  }

  onEvent(handler: EventHandler) {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  onStatus(handler: StatusHandler) {
    this.statusHandlers.add(handler);
    return () => this.statusHandlers.delete(handler);
  }

  private setStatus(status: Parameters<StatusHandler>[0]) {
    this.statusHandlers.forEach((h) => h(status));
  }

  private clearPing() {
    if (this.pingTimer) clearInterval(this.pingTimer);
    this.pingTimer = null;
  }
}
