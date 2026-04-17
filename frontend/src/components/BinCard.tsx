import { Link } from "react-router-dom";
import type { BinLatest } from "../types";
import { usageRate } from "../utils/metrics";
import {
  fillSignal,
  PRIORITY_HELP,
  tempSignal,
} from "../utils/healthSignals";
import { AlertChips } from "./AlertChips";
import { BinFillGlyph } from "./BinFillGlyph";
import { StatusBadge } from "./StatusBadge";

export function BinCard({
  bin,
  staggerIndex = 0,
}: {
  bin: BinLatest;
  /** Staggered entrance delay for grid lists (0-based). */
  staggerIndex?: number;
}) {
  const fill = Math.min(100, Math.max(0, bin.fill_level));
  const fs = fillSignal(fill);
  const ts = tempSignal(Number(bin.temperature));
  const nearFull = fill >= 95;

  let accent = "";
  switch (bin.status) {
    case "probable_fire":
      accent = " bin-card--probable-fire";
      break;
    case "fire_risk":
      accent = " bin-card--fire-risk";
      break;
    case "critical":
      accent = " bin-card--status-critical";
      break;
    default:
      if (nearFull) accent = " bin-card--near-full";
      else if (ts.tone === "severe") accent = " bin-card--temp-severe";
      else if (ts.tone === "fire") accent = " bin-card--temp-heat";
      break;
  }

  return (
    <article
      className={"bin-card bin-card--enter" + accent}
      style={{
        animationDelay: `${Math.min(staggerIndex, 20) * 0.055}s`,
      }}
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
      <div className="bin-card__body">
        <div className="bin-card__bin" title={`Fill ${fill.toFixed(0)}%`}>
          <BinFillGlyph
            fillPct={fill}
            nearFull={nearFull}
            hot={ts.tone === "fire" || ts.tone === "severe"}
          />
        </div>
        <div className="bin-card__body-main">
          <p className="bin-card__meter-caption mono">
            {fill.toFixed(0)}% full
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
        </div>
      </div>
    </article>
  );
}
