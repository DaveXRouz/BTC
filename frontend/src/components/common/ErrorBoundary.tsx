import { Component, type ReactNode, type ErrorInfo } from "react";
import { withTranslation, type WithTranslation } from "react-i18next";

interface ErrorBoundaryOwnProps {
  children: ReactNode;
  fallback?: ReactNode;
}

type ErrorBoundaryProps = ErrorBoundaryOwnProps & WithTranslation;

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundaryClass extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { t } = this.props;

      return (
        <div className="flex items-center justify-center min-h-[300px] p-6">
          <div className="max-w-md w-full bg-[var(--nps-bg-card)] border border-nps-error rounded-lg p-6 text-center">
            <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-nps-error/10 flex items-center justify-center">
              <span className="text-nps-error text-xl font-bold">!</span>
            </div>
            <h2 className="text-lg font-semibold text-nps-text mb-2">
              {t("common.error_boundary_title")}
            </h2>
            <p className="text-sm text-nps-text-dim mb-4">
              {t("common.error_boundary_message")}
            </p>
            {import.meta.env.DEV && this.state.error && (
              <details className="mb-4 text-start">
                <summary className="text-xs text-nps-text-dim cursor-pointer">
                  {t("common.error_details")}
                </summary>
                <pre className="mt-2 p-2 bg-[var(--nps-bg-input)] rounded text-xs text-nps-error overflow-auto max-h-32">
                  {this.state.error.message}
                  {"\n"}
                  {this.state.error.stack}
                </pre>
              </details>
            )}
            <div className="flex gap-3 justify-center">
              <button
                type="button"
                onClick={this.handleReset}
                className="px-4 py-2 text-sm bg-nps-bg-button text-white rounded hover:opacity-90 transition-opacity"
              >
                {t("common.retry")}
              </button>
              <a
                href="/dashboard"
                className="px-4 py-2 text-sm text-nps-text-dim border border-nps-border rounded hover:text-nps-text transition-colors"
              >
                {t("common.go_home")}
              </a>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export const ErrorBoundary = withTranslation()(ErrorBoundaryClass);
