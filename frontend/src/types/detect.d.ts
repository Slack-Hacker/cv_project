export interface DetectResult {
  detected?: boolean;
  reason?: string;

  // Add this line ↓↓↓
  class_name?: string;

  visible_30_percent?: boolean;

  region?: string;
  region_id?: number;

  bbox_px?: [number, number, number, number];

  area_norm?: number;
  reference_area?: number;

  error?: string;
}
