import { useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchZoneBins } from "../api/client";
import type { BinLatest } from "../types";
import { BinCard } from "../components/BinCard";
import { useFetchedData } from "../hooks/useFetchedData";

export function ZonePage() {
  const { zone } = useParams<{ zone: string }>();
  const decoded = zone ? decodeURIComponent(zone) : "";

  const fetcher = useCallback(
    () => fetchZoneBins(decoded),
    [decoded],
  );

  const { data: bins, error: err, loading, lastUpdated } = useFetchedData(
    `zone-${decoded}`,
    fetcher,
  );

  if (!decoded) {
    return (
      <div className="page">
        <p className="muted">Missing zone in URL.</p>
        <Link to="/zones">Back to zones</Link>
      </div>
    );
  }

  return (
    <div className="page">
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link to="/zones">Zones</Link>
        <span aria-hidden> / </span>
        <span className="mono">{decoded}</span>
      </nav>
      <header className="page__hero">
        <h1 className="page__title">Zone {decoded}</h1>
        <p className="page__lead">Bins located in this zone.</p>
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
            <p className="muted">No bins in this zone.</p>
          ) : (
            bins.map((b: BinLatest) => (
              <BinCard key={b.bin_id} bin={b} />
            ))
          )}
        </div>
      ) : null}
    </div>
  );
}
