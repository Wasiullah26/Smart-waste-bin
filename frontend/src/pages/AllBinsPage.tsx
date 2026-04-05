import { useCallback } from "react";
import { fetchAllBins } from "../api/client";
import { BinCard } from "../components/BinCard";
import { useFetchedData } from "../hooks/useFetchedData";

export function AllBinsPage() {
  const fetcher = useCallback(() => fetchAllBins(), []);
  const { data: bins, error: err, loading, lastUpdated } = useFetchedData(
    "all-bins",
    fetcher,
  );

  return (
    <div className="page">
      <header className="page__hero">
        <h1 className="page__title">Fleet overview</h1>
        <p className="page__lead">
          Latest reading for each bin. Updates every few seconds while you keep this
          page open.
        </p>
        {lastUpdated ? (
          <p className="page__updated mono">
            Last updated {lastUpdated.toLocaleTimeString()}
          </p>
        ) : null}
      </header>
      {loading ? <p className="muted">Loading bins…</p> : null}
      {err ? (
        <div className="callout callout--error" role="alert">
          {err}
        </div>
      ) : null}
      {bins && !loading ? (
        <div className="grid">
          {bins.length === 0 ? (
            <p className="muted">No bins to show yet. When your devices send data, they will appear here.</p>
          ) : (
            bins.map((b) => <BinCard key={b.bin_id} bin={b} />)
          )}
        </div>
      ) : null}
    </div>
  );
}
