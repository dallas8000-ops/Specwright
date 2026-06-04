import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = { children: ReactNode };
type State = { error: Error | null };

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Specwright UI error:", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div
          style={{
            padding: "2rem",
            maxWidth: "40rem",
            margin: "2rem auto",
            fontFamily: "system-ui, sans-serif",
            color: "#f0f4fc",
            background: "#1a2332",
            border: "1px solid #f87171",
            borderRadius: "12px",
          }}
        >
          <h1 style={{ color: "#f87171", marginBottom: "0.75rem" }}>
            Something went wrong
          </h1>
          <p style={{ marginBottom: "1rem", color: "#94a3b8" }}>
            The Specwright UI hit an error. Try refreshing the page.
          </p>
          <pre
            style={{
              fontSize: "0.8rem",
              overflow: "auto",
              padding: "1rem",
              background: "#0f1419",
              borderRadius: "8px",
            }}
          >
            {this.state.error.message}
          </pre>
          <button
            type="button"
            style={{
              marginTop: "1rem",
              padding: "0.5rem 1rem",
              background: "#0891b2",
              color: "white",
              border: "none",
              borderRadius: "8px",
              cursor: "pointer",
            }}
            onClick={() => window.location.reload()}
          >
            Reload
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
