import { useId } from "react";

/** Waste-bin mark — chartreuse ink accent, readable at small sizes. */
export function BrandMark() {
  const gid = useId().replace(/:/g, "");
  return (
    <div className="brand__mark" aria-hidden>
      <svg viewBox="0 0 40 40" width="40" height="40" aria-hidden>
        <defs>
          <linearGradient id={`${gid}-g`} x1="6" y1="4" x2="36" y2="38" gradientUnits="userSpaceOnUse">
            <stop stopColor="#d4f932" />
            <stop offset="0.55" stopColor="#a3e635" />
            <stop offset="1" stopColor="#65a30d" />
          </linearGradient>
          <filter id={`${gid}-d`} x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.35" />
          </filter>
        </defs>
        <rect x="3" y="3" width="34" height="34" rx="11" fill="#0c0f14" stroke="rgba(212,249,50,0.35)" strokeWidth="1" />
        <path
          filter={`url(#${gid}-d)`}
          fill={`url(#${gid}-g)`}
          d="M12 14h16v2H12v-2zm-1-4h18a2 2 0 0 1 2 2v2H9v-2a2 2 0 0 1 2-2zm1 8h16l-1.2 14a2 2 0 0 1-2 1.8H14.2a2 2 0 0 1-2-1.8L11 18z"
        />
        <rect x="14" y="10" width="12" height="3" rx="1" fill="#0c0f14" opacity="0.5" />
      </svg>
    </div>
  );
}
