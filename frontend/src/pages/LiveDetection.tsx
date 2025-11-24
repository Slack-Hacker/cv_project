import { useState, useEffect, useRef } from "react";
import axios from "axios";
import type { DetectResult } from "../types/detect";

export default function LiveDetection() {
  const [cameraUrl, setCameraUrl] = useState("");
  const [result, setResult] = useState<DetectResult | null>(null);

  const imgRef = useRef<HTMLImageElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // --------------------------------------------------------------
  // 1. POLL STREAM EVERY 600ms
  // --------------------------------------------------------------
  useEffect(() => {
    if (!cameraUrl) return;

    const interval = setInterval(async () => {
      try {
        const res = await axios.get("/api/detect/stream", {
          params: { url: cameraUrl },
        });
        setResult(res.data.result);
      } catch {
        setResult({ error: "stream_error" } as any);
      }
    }, 600);

    return () => clearInterval(interval);
  }, [cameraUrl]);

  // --------------------------------------------------------------
  // 2. DRAW GRID + PLACES + DETECTION
  // --------------------------------------------------------------
  useEffect(() => {
    const img = imgRef.current;
    const canvas = canvasRef.current;

    if (!img || !canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const displayW = img.clientWidth;
    const displayH = img.clientHeight;

    canvas.width = displayW;
    canvas.height = displayH;

    ctx.clearRect(0, 0, displayW, displayH);

    // ==========================================================
    // 9×9 GRID
    // ==========================================================
    const rows = 9, cols = 9;
    const cellW = displayW / cols;
    const cellH = displayH / rows;

    ctx.strokeStyle = "rgba(0,255,255,0.7)";
    ctx.lineWidth = 1;

    for (let i = 1; i < cols; i++) {
      ctx.beginPath();
      ctx.moveTo(i * cellW, 0);
      ctx.lineTo(i * cellW, displayH);
      ctx.stroke();
    }

    for (let j = 1; j < rows; j++) {
      ctx.beginPath();
      ctx.moveTo(0, j * cellH);
      ctx.lineTo(displayW, j * cellH);
      ctx.stroke();
    }

    // ==========================================================
    // 3×3 PLACES
    // ==========================================================
    ctx.strokeStyle = "cyan";
    ctx.lineWidth = 2;
    ctx.font = "18px Arial";
    ctx.fillStyle = "cyan";

    let idx = 1;
    for (let r = 0; r < 9; r += 3) {
      for (let c = 0; c < 9; c += 3) {
        const x1 = c * cellW;
        const y1 = r * cellH;

        ctx.strokeRect(x1, y1, cellW * 3, cellH * 3);
        ctx.fillText(`place${idx}`, x1 + 8, y1 + 22);

        idx++;
      }
    }

    // ==========================================================
    // HIGHLIGHT PLACE
    // ==========================================================
    if (result?.region_id && result.detected) {
      const rid = result.region_id - 1;
      const row = Math.floor(rid / 3);
      const col = rid % 3;

      ctx.fillStyle = "rgba(0,255,0,0.18)";
      ctx.fillRect(col * cellW * 3, row * cellH * 3, cellW * 3, cellH * 3);
    }

    // ==========================================================
    // DRAW DETECTION BBOX + CLASS NAME
    // ==========================================================
    if (result?.detected && result?.bbox_px) {
      const [x1, y1, x2, y2] = result.bbox_px;

      const naturalW = img.naturalWidth || displayW;
      const naturalH = img.naturalHeight || displayH;

      const scaleX = displayW / naturalW;
      const scaleY = displayH / naturalH;

      ctx.strokeStyle = "lime";
      ctx.lineWidth = 3;
      ctx.strokeRect(
        x1 * scaleX,
        y1 * scaleY,
        (x2 - x1) * scaleX,
        (y2 - y1) * scaleY
      );

      // Draw class + region label
      const label = `${result.class_name || ""} ${result.region ? `(${result.region})` : ""}`;

      ctx.font = "16px Arial";
      ctx.fillStyle = "lime";
      ctx.fillText(
        label,
        x1 * scaleX + 6,
        Math.max(16, y1 * scaleY - 4)
      );
    }

  }, [result]);

  // --------------------------------------------------------------
  // UI
  // --------------------------------------------------------------
  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Live Detection</h1>

      <input
        type="text"
        placeholder="http://192.168.x.x:8080/video"
        className="border p-2 w-full rounded"
        onChange={(e) => setCameraUrl(e.target.value)}
      />

      {/* STREAM DISPLAY */}
      <div
        style={{
          width: "640px",
          height: "480px",
          position: "relative",
          borderRadius: "6px",
          overflow: "hidden",
        }}
      >
        {cameraUrl && (
          <>
            <img
              ref={imgRef}
              src={cameraUrl}
              alt="live"
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                position: "absolute",
                top: 0,
                left: 0,
                zIndex: 1,
              }}
            />

            <canvas
              ref={canvasRef}
              style={{
                width: "100%",
                height: "100%",
                position: "absolute",
                top: 0,
                left: 0,
                pointerEvents: "none",
                zIndex: 2,
              }}
            />
          </>
        )}
      </div>

      {/* INFO PANEL */}
      {result && (
        <div className="bg-white border p-4 rounded shadow space-y-1">
          {result.error && (
            <p className="text-red-600 font-semibold">Error: {result.error}</p>
          )}

          {!result.error && (
            <>
              <p className="font-medium">
                {result.detected ? "✔ Object Detected" : "❌ No Detection"}
              </p>

              {result.detected && (
                <>
                  <p>
                    Class: <b>{result.class_name}</b>
                  </p>

                  <p>Region: {result.region}</p>

                  <p>
                    Visible ≥30%:{" "}
                    <b
                      className={
                        result.visible_30_percent
                          ? "text-green-600"
                          : "text-red-600"
                      }
                    >
                      {result.visible_30_percent ? "Yes" : "No"}
                    </b>
                  </p>
                </>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
