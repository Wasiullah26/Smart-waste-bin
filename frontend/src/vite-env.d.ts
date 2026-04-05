/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  /** Polling interval for GET routes (ms). Default 4000, min 2000. */
  readonly VITE_POLL_INTERVAL_MS: string;
  /** If your API uses an admin key, set the same value for protected actions (e.g. clear data). */
  readonly VITE_ADMIN_API_KEY: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
