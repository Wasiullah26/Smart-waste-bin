import { useCallback, useMemo } from "react";
import { Link } from "react-router-dom";
import { fetchAllBins } from "../api/client";
import type { BinLatest } from "../types";
import { useFetchedData } from "../hooks/useFetchedData";

export function ZoneHubPage() {
  const fetcher = useCallback(() => fetchAllBins(), []);
  const { data: bins, error: err, loading, lastUpdated } = useFetchedData(
    "zones-hub",
    fetcher,
  );

  const zones = useMemo(() => {
    if (!bins) return [];
    const z = new Set(bins.map((b: BinLatest) => b.zone));
    return [...z].sort();
  }, [bins]);

  return (
    <div className="page">
      <header className="page__hero">
        <h1 className="page__title">Zones</h1>
        <p className="page__lead">Choose a zone to see bins in that area.</p>
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
        <ul className="zone-list">
          {zones.length === 0 ? (
            <li className="muted">No zones yet. Once data arrives, zones will list here.</li>
          ) : (
            zones.map((z) => (
              <li key={z}>
                <Link className="zone-pill" to={`/zones/${encodeURIComponent(z)}`}>
                  <span className="zone-pill__name">{z}</span>
                  <span className="zone-pill__arrow" aria-hidden>
                    →
                  </span>
                </Link>
              </li>
            ))
          )}
        </ul>
      ) : null}
    </div>
  );
}
