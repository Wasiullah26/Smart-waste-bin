import { Link } from "react-router-dom";
import type { BinLatest } from "../types";
import { usageRate } from "../utils/metrics";
import {
  fillSignal,
  PRIORITY_HELP,
  tempSignal,
} from "../utils/healthSignals";
import { AlertChips } from "./AlertChips";
import { StatusBadge } from "./StatusBadge";

export function BinCard({ bin }: { bin: BinLatest }) {
  const fill = Math.min(100, Math.max(0, bin.fill_level));
  const fs = fillSignal(fill);
  const ts = tempSignal(Number(bin.temperature));
  const nearFull = fill >= 95;

  return (
    <article
      className={
        "bin-card" +
        (nearFull ? " bin-card--near-full" : "") +
        (ts.tone === "fire" || ts.tone === "severe"
          ? " bin-card--temp-fire"
          : "")
      }
    >
      <div className="bin-card__top">
        <div>
          <h3 className="bin-card__title">
            <Link to={`/bins/${encodeURIComponent(bin.bin_id)}`}>
              {bin.bin_id}
            </Link>
          </h3>
          <p className="bin-card__meta">
            <span className="mono">{bin.zone}</span>
            {bin.fog_node_id ? (
              <>
                {" · "}
                <span>{bin.fog_node_id}</span>
              </>
            ) : null}
          </p>
        </div>
        <StatusBadge status={bin.status} />
      </div>
      <AlertChips items={[fs, ts]} />
      <div className="bin-card__meter" aria-hidden>
        <div
          className={
            "bin-card__meter-fill" +
            (nearFull ? " bin-card__meter-fill--full" : "")
          }
          style={{ width: `${fill}%` }}
        />
      </div>
      <p className="bin-card__meter-caption mono">
        {fill.toFixed(0)}% · {fs.label}
      </p>
      <dl className="bin-card__stats">
        <div>
          <dt>Fill</dt>
          <dd className="mono">{fill.toFixed(1)}%</dd>
        </div>
        <div>
          <dt title="Usage on a 0–100 scale for comparison">Usage (norm.)</dt>
          <dd className="mono">{usageRate(bin).toFixed(1)}</dd>
        </div>
        <div>
          <dt>Temp</dt>
          <dd className="mono">{Number(bin.temperature).toFixed(1)}°C</dd>
        </div>
        <div>
          <dt title={PRIORITY_HELP}>Routing score</dt>
          <dd className="mono">{Number(bin.priority).toFixed(1)}</dd>
        </div>
      </dl>
    </article>
  );
}
