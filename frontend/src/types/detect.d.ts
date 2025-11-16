export interface DetectResult {
  detected?: boolean;
  reason?: string;
  visible_30_percent?: boolean;
  region?: string;
  bbox_px?: [number, number, number, number];
  area_norm?: number;
  reference_area?: number;
  error?: string;
}
