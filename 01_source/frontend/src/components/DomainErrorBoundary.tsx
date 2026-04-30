import React, { type ErrorInfo, type ReactNode } from "react";
import type { OpsDomain } from "../features/ops/types";

interface DomainErrorBoundaryProps {
  children: ReactNode;
  domain?: OpsDomain | "orders";
  onError?: (error: Error, errorInfo: ErrorInfo, domain: string) => void;
}

interface DomainErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export default class DomainErrorBoundary extends React.Component<
  DomainErrorBoundaryProps,
  DomainErrorBoundaryState
> {
  constructor(props: DomainErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): DomainErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    if (typeof this.props.onError === "function") {
      this.props.onError(error, errorInfo, this.props.domain || "global");
      return;
    }

    console.error("[DomainErrorBoundary]", {
      domain: this.props.domain || "global",
      error,
      errorInfo,
    });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <div className="public-card" style={{ margin: "24px auto", maxWidth: "720px" }}>
        <h2 style={{ marginTop: 0 }}>Algo deu errado nesta area</h2>
        <p style={{ marginBottom: 16 }}>
          Dominio: <strong>{this.props.domain || "global"}</strong>. Tente novamente.
        </p>
        <button type="button" className="public-btn primary" onClick={this.handleRetry}>
          Tentar novamente
        </button>
      </div>
    );
  }
}
