import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchBin, fetchHistory } from "../api/client";
import type { BinEvent, BinLatest } from "../types";
import { AlertChips } from "../components/AlertChips";
import { StatusBadge } from "../components/StatusBadge";
import { useRefetchOnIngest } from "../hooks/useRefetchOnIngest";
import { useRefreshOnInterval } from "../hooks/useRefreshOnInterval";
import { FILL_CRITICAL_PCT, fillSignal, PRIORITY_HELP, tempSignal } from "../utils/healthSignals";
import { usageRate } from "../utils/metrics";

export function BinDetailPage() {
  const { binId } = useParams<{ binId: string }>();
  const id = binId ? decodeURIComponent(binId) : "";
  const [latest, setLatest] = useState<BinLatest | null>(null);
  const [events, setEvents] = useState<BinEvent[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const load = useCallback(
    async (initial: boolean) => {
      if (!id) return;
      if (initial) setLoading(true);
      try {
        const [bin, hist] = await Promise.all([
          fetchBin(id),
          fetchHistory(id, 80),
        ]);
        setLatest(bin);
        setEvents(hist.events);
        setErr(null);
        setLastUpdated(new Date());
      } catch (e: unknown) {
        setErr(e instanceof Error ? e.message : String(e));
        if (initial) {
          setLatest(null);
          setEvents([]);
        }
      } finally {
        setLoading(false);
      }
    },
    [id],
  );

  useEffect(() => {
    void load(true);
  }, [id, load]);

  useRefreshOnInterval(() => {
    void load(false);
  }, [id, load]);

  useRefetchOnIngest(() => {
    void load(false);
  }, [load]);

  const fillHint = useMemo(() => {
    if (!latest || loading) return null;
    return fillSignal(Number(latest.fill_level));
  }, [latest, loading]);

  const tempHint = useMemo(() => {
    if (!latest || loading) return null;
    return tempSignal(Number(latest.temperature));
  }, [latest, loading]);

  if (!id) {
    return (
      <div className="page">
        <p className="muted">Missing bin id.</p>
        <Link to="/">Back</Link>
      </div>
    );
  }

  return (
    <div className="page page--detail">
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link to="/">All bins</Link>
        <span aria-hidden> / </span>
        <span className="mono">{id}</span>
      </nav>

      {lastUpdated ? (
        <p className="page__updated mono">
          Last updated {lastUpdated.toLocaleTimeString()}
        </p>
      ) : null}

      {loading ? <p className="muted">Loading…</p> : null}
      {err ? (
        <div className="callout callout--error" role="alert">
          {err}
        </div>
      ) : null}

      {latest && !loading ? (
        <>
          <header className="detail-head">
            <div>
              <h1 className="page__title mono">{latest.bin_id}</h1>
              <p className="page__lead">
                Zone <span className="mono">{latest.zone}</span>
                {latest.fog_node_id ? (
                  <>
                    {" "}
                    · device <span className="mono">{latest.fog_node_id}</span>
                  </>
                ) : null}
              </p>
            </div>
            <StatusBadge status={latest.status} />
          </header>

          {fillHint && tempHint ? (
            <AlertChips items={[fillHint, tempHint]} />
          ) : null}

          {fillHint && tempHint &&
            (tempHint.tone === "severe" ||
              tempHint.tone === "fire" ||
              fillHint.tone === "crit") && (
            <div className="callout callout--alert-strip" role="status">
              {tempHint.tone === "severe" ? (
                <p>
                  <strong>Strong heat:</strong> this reading suggests a probable fire.
                  Verify on site and follow your safety procedures.
                </p>
              ) : null}
              {tempHint.tone === "fire" ? (
                <p>
                  <strong>Elevated temperature:</strong> treated as a fire-risk signal
                  until readings return to normal.
                </p>
              ) : null}
              {fillHint.tone === "crit" ? (
                <p>
                  <strong>Very full:</strong> this bin is at or above {FILL_CRITICAL_PCT}%
                  capacity and may need collection soon.
                </p>
              ) : null}
            </div>
          )}

          <section className="detail-kpis">
            <div className="kpi">
              <span className="kpi__label">Fill</span>
              <span className="kpi__value mono">
                {Number(latest.fill_level).toFixed(1)}%
              </span>
            </div>
            <div className="kpi">
              <span
                className="kpi__label"
                title="Usage scaled to a 0–100 scale for comparison across bins"
              >
                Usage (norm.)
              </span>
              <span className="kpi__value mono">
                {usageRate(latest).toFixed(2)}
              </span>
            </div>
            <div className="kpi">
              <span className="kpi__label">Temperature</span>
              <span className="kpi__value mono">
                {Number(latest.temperature).toFixed(1)}°C
              </span>
            </div>
            <div className="kpi">
              <span
                className="kpi__label"
                title={PRIORITY_HELP}
              >
                Routing score
              </span>
              <span className="kpi__value mono">
                {Number(latest.priority).toFixed(2)}
              </span>
              <span className="kpi__hint">0–100</span>
            </div>
            <div className="kpi">
              <span className="kpi__label">Weight</span>
              <span className="kpi__value mono">
                {Number(latest.weight).toFixed(2)} kg
              </span>
            </div>
          </section>

          <section className="history">
            <h2 className="history__title">Recent events</h2>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Kind</th>
                    <th>Status</th>
                    <th>Fill</th>
                    <th>Usage</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((ev) => (
                    <tr key={ev.event_sk}>
                      <td className="mono">
                        {typeof ev.timestamp === "number"
                          ? new Date(ev.timestamp * 1000).toLocaleString()
                          : "—"}
                      </td>
                      <td>
                        {ev.message_type === "summary"
                          ? "Scheduled update"
                          : ev.message_type === "alert"
                            ? "Alert"
                            : ev.message_type}
                      </td>
                      <td>
                        <StatusBadge status={ev.status} />
                      </td>
                      <td className="mono">
                        {Number(ev.fill_level).toFixed(1)}%
                      </td>
                      <td className="mono">{usageRate(ev).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {events.length === 0 ? (
              <p className="muted history__empty">No history rows yet.</p>
            ) : null}
          </section>
        </>
      ) : null}
    </div>
  );
}
