import type { BinStatus } from "../types";

const config: Record<
  BinStatus,
  { label: string; className: string; dot: string }
> = {
  normal: {
    label: "Normal",
    className: "badge badge--normal",
    dot: "var(--ok)",
  },
  warning: {
    label: "Warning",
    className: "badge badge--warning",
    dot: "var(--warn)",
  },
  critical: {
    label: "Critical",
    className: "badge badge--critical",
    dot: "var(--bad)",
  },
  fire_risk: {
    label: "Fire risk",
    className: "badge badge--fire",
    dot: "var(--fire)",
  },
  probable_fire: {
    label: "Probable fire",
    className: "badge badge--probable-fire",
    dot: "var(--severe)",
  },
};

export function StatusBadge({ status }: { status: string }) {
  const key = status in config ? (status as BinStatus) : "normal";
  const c = config[key];
  return (
    <span className={c.className} title={`Status: ${status}`}>
      <span className="badge__dot" style={{ background: c.dot }} aria-hidden />
      {c.label}
    </span>
  );
}
