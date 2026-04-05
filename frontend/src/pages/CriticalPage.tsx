import { useCallback } from "react";
import { fetchCritical } from "../api/client";
import { BinCard } from "../components/BinCard";
import { useFetchedData } from "../hooks/useFetchedData";

export function CriticalPage() {
  const fetcher = useCallback(() => fetchCritical(), []);
  const { data: bins, error: err, loading, lastUpdated } = useFetchedData(
    "critical",
    fetcher,
  );

  return (
    <div className="page">
      <header className="page__hero">
        <h1 className="page__title">Attention</h1>
        <p className="page__lead">
          Bins that need attention: very full, elevated temperature, or a possible
          fire risk.
        </p>
        {lastUpdated ? (
          <p className="page__updated mono">
            Last updated {lastUpdated.toLocaleTimeString()}
          </p>
        ) : null}
      </header>
      {loading ? <p className="muted">Loading…</p> : null}
      {err ? (
        <div className="callout callout--error" role="alert">
          {err}
        </div>
      ) : null}
      {bins && !loading ? (
        <div className="grid">
          {bins.length === 0 ? (
            <p className="muted">No critical bins right now.</p>
          ) : (
            bins.map((b) => <BinCard key={b.bin_id} bin={b} />)
          )}
        </div>
      ) : null}
    </div>
  );
}
