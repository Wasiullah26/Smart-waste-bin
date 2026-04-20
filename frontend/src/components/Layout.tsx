import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { getConfiguredApiBase, postAdminPurge } from "../api/client";
import { BrandMark } from "./BrandMark";
import { dispatchDashboardRefetch } from "../hooks/useRefetchOnIngest";

const nav = [
  { to: "/", label: "All bins", end: true },
  { to: "/critical", label: "Attention" },
  { to: "/zones", label: "By zone" },
];

export function Layout() {
  const api = getConfiguredApiBase();
  const [purging, setPurging] = useState(false);
  const [purgeMsg, setPurgeMsg] = useState<string | null>(null);

  async function purge() {
    if (
      !window.confirm(
        "Delete all bin data shown in this app? This removes stored readings and cannot be undone.",
      )
    ) {
      return;
    }
    setPurging(true);
    setPurgeMsg(null);
    try {
      const out = await postAdminPurge();
      dispatchDashboardRefetch();
      const latest = out.deleted_latest ?? 0;
      const events = out.deleted_events ?? 0;
      const fog = out.deleted_fog_state;
      const fogNote =
        typeof fog === "number"
          ? ` Cleared ${fog} MQTT fog state row(s) (prevents old zones from reappearing after summary).`
          : "";
      const sqsNote = out.sqs_purged ? " Ingestion queue purged." : "";
      const mismatchHint =
        latest === 0 && events === 0
          ? " If bins were still visible before this, VITE_API_BASE_URL may point at a different API than the one your MQTT pipeline writes to — purge ran against empty tables."
          : "";
      setPurgeMsg(
        `Cleared ${latest} current row(s) and ${events} history row(s).${fogNote}${sqsNote}${mismatchHint}`,
      );
    } catch (e: unknown) {
      setPurgeMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setPurging(false);
    }
  }

  const purgeOk = Boolean(purgeMsg?.startsWith("Cleared"));

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <BrandMark />
          <div>
            <div className="brand__name">Waste Bin Ops</div>
            <div className="brand__tag">Fleet monitoring</div>
          </div>
        </div>
        <nav className="nav" aria-label="Main">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                "nav__link" + (isActive ? " nav__link--active" : "")
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar__purge">
          <div className="sidebar__purge-label">Data</div>
          <button
            type="button"
            className="sidebar__purge-btn"
            disabled={purging || !api}
            title={!api ? "Configure the API URL in your environment to enable this action." : undefined}
            onClick={() => void purge()}
          >
            {purging ? "Clearing…" : "Clear all data"}
          </button>
          {purgeMsg ? (
            <p
              className={
                "sidebar__purge-msg " +
                (purgeOk ? "sidebar__purge-msg--ok" : "sidebar__purge-msg--err")
              }
            >
              {purgeMsg}
            </p>
          ) : null}
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
