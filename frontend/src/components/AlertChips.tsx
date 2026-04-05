import type { SignalTone } from "../utils/healthSignals";

const toneClass: Record<SignalTone, string> = {
  ok: "signal-chip--ok",
  warn: "signal-chip--warn",
  crit: "signal-chip--crit",
  fire: "signal-chip--fire",
  warm: "signal-chip--warm",
  severe: "signal-chip--severe",
};

export function AlertChips({
  items,
}: {
  items: { label: string; tone: SignalTone }[];
}) {
  return (
    <ul className="signal-chips" aria-label="Sensor hints">
      {items.map((it, i) => (
        <li
          key={`${it.tone}-${i}-${it.label}`}
          className={`signal-chip ${toneClass[it.tone]}`}
        >
          {it.label}
        </li>
      ))}
    </ul>
  );
}
