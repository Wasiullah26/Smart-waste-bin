export type BinStatus =
  | "normal"
  | "warning"
  | "critical"
  | "fire_risk"
  | "probable_fire";

export interface BinLatest {
  bin_id: string;
  zone: string;
  latest_timestamp: number;
  fill_level: number;
  weight: number;
  temperature: number;
  /** Normalized 0–100 usage; legacy rows may only have `usage_count`. */
  usage_rate?: number;
  usage_count?: number;
  priority: number;
  status: BinStatus;
  last_message_type?: string;
  fog_node_id?: string;
  /** True when temperature ≥ probable-fire threshold (see shared/constants.py). */
  probable_fire_alert?: boolean;
}

export interface BinEvent {
  bin_id: string;
  event_sk: string;
  zone: string;
  timestamp: number;
  emitted_at: number;
  fill_level: number;
  weight: number;
  temperature: number;
  usage_rate?: number;
  usage_count?: number;
  priority: number;
  status: BinStatus;
  message_type: string;
  fill_alert: string;
  fire_risk: boolean;
  probable_fire_alert?: boolean;
  fog_node_id?: string;
}
