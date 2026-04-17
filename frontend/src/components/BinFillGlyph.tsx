import { useId } from "react";

const VB = { w: 80, h: 118 };

/** Inner cavity where waste level is drawn (viewBox coords). */
const CHAMBER = { x: 20.5, y: 41, w: 39, h: 54, rx: 5 };

type BinFillGlyphProps = {
  fillPct: number;
  nearFull: boolean;
  hot: boolean;
};

/**
 * Front-view wheelie bin: domed lid, body, chamber fill, two wheels.
 */
export function BinFillGlyph({ fillPct, nearFull, hot }: BinFillGlyphProps) {
  const rawId = useId().replace(/:/g, "");
  const clipId = `bin-ch-${rawId}`;
  const gWaste = `bin-gw-${rawId}`;
  const gFull = `bin-gf-${rawId}`;

  const fill = Math.min(100, Math.max(0, fillPct));
  const fillH = (CHAMBER.h * fill) / 100;
  const fillY = CHAMBER.y + CHAMBER.h - fillH;

  const shellClass =
    "bin-fill-glyph__shell" +
    (nearFull ? " bin-fill-glyph__shell--near-full" : "") +
    (hot ? " bin-fill-glyph__shell--hot" : "");

  return (
    <svg
      className="bin-fill-glyph"
      viewBox={`0 0 ${VB.w} ${VB.h}`}
      width={72}
      height={106}
      aria-hidden
    >
      <defs>
        <clipPath id={clipId}>
          <rect
            x={CHAMBER.x}
            y={CHAMBER.y}
            width={CHAMBER.w}
            height={CHAMBER.h}
            rx={CHAMBER.rx}
          />
        </clipPath>
        <linearGradient id={gWaste} x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#c8f031" />
          <stop offset="32%" stopColor="#eab308" />
          <stop offset="68%" stopColor="#f97316" />
          <stop offset="100%" stopColor="#e879a9" />
        </linearGradient>
        <linearGradient id={gFull} x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#fbbf24" />
          <stop offset="35%" stopColor="#f97316" />
          <stop offset="72%" stopColor="#ef4444" />
          <stop offset="100%" stopColor="#991b1b" />
        </linearGradient>
      </defs>

      <ellipse
        className="bin-fill-glyph__shadow"
        cx={VB.w / 2}
        cy={112}
        rx={26}
        ry={4}
      />

      <g className="bin-fill-glyph__wheels">
        <circle cx={22} cy={104} r={6.5} />
        <circle cx={58} cy={104} r={6.5} />
        <circle className="bin-fill-glyph__wheel-hub" cx={22} cy={104} r={2.2} />
        <circle className="bin-fill-glyph__wheel-hub" cx={58} cy={104} r={2.2} />
      </g>

      <rect
        className={shellClass}
        x={13}
        y={36}
        width={54}
        height={66}
        rx={11}
        ry={11}
      />

      <path
        className="bin-fill-glyph__sheen"
        d="M 22 40 Q 24 70 23 98"
        fill="none"
        strokeWidth={3}
        strokeLinecap="round"
      />

      {/* Side grab handle (typical wheelie bin) */}
      <path
        className="bin-fill-glyph__handle"
        d="M 11 46 C 7 46 5.5 49 5.5 52 L 5.5 78 C 5.5 81 7.5 83 10 83"
        fill="none"
        strokeWidth={3.2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Dark throat visible under the lid swing line */}
      <path className="bin-fill-glyph__throat" d="M 17 36 L 63 36 L 61 41 L 19 41 Z" />

      <rect
        className="bin-fill-glyph__chamber"
        x={CHAMBER.x}
        y={CHAMBER.y}
        width={CHAMBER.w}
        height={CHAMBER.h}
        rx={CHAMBER.rx}
      />

      <g clipPath={`url(#${clipId})`}>
        <rect
          className="bin-fill-glyph__fill"
          x={CHAMBER.x}
          y={fillY}
          width={CHAMBER.w}
          height={fill > 0 ? Math.max(fillH, 0.5) : 0}
          fill={nearFull ? `url(#${gFull})` : `url(#${gWaste})`}
        />
      </g>

      <line className="bin-fill-glyph__seam" x1={14} y1={36.5} x2={66} y2={36.5} />

      {/* Domed lid — modest overhang, shallow dome (reads smaller vs body) */}
      <path
        className="bin-fill-glyph__lid"
        d="M 12 27 C 12 16 68 16 68 27 L 68 36 L 12 36 Z"
      />
      <path
        className="bin-fill-glyph__lid-shine"
        d="M 20 21 Q 40 17 60 21"
        fill="none"
        strokeWidth={1.8}
        strokeLinecap="round"
      />

      <rect className="bin-fill-glyph__hinge" x={37} y={31} width={6} height={4} rx={1.2} />
    </svg>
  );
}
