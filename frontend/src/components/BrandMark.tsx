import { useId } from "react";

/** Waste-bin mark — distinct shape so the header isn’t a flat color block. */
export function BrandMark() {
  const gid = useId().replace(/:/g, "");
  return (
    <div className="brand__mark" aria-hidden>
      <svg viewBox="0 0 40 40" width="40" height="40" aria-hidden>
        <defs>
          <linearGradient id={`${gid}-g`} x1="8" y1="4" x2="34" y2="36" gradientUnits="userSpaceOnUse">
            <stop stopColor="#38bdf8" />
            <stop offset="1" stopColor="#6366f1" />
          </linearGradient>
        </defs>
        <rect x="4" y="4" width="32" height="32" rx="10" fill={`url(#${gid}-g)`} opacity="0.2" />
        <path
          fill={`url(#${gid}-g)`}
          d="M12 14h16v2H12v-2zm-1-4h18a2 2 0 0 1 2 2v2H9v-2a2 2 0 0 1 2-2zm1 8h16l-1.2 14a2 2 0 0 1-2 1.8H14.2a2 2 0 0 1-2-1.8L11 18z"
        />
        <rect x="14" y="10" width="12" height="3" rx="1" fill="#0c1220" opacity="0.35" />
      </svg>
    </div>
  );
}
