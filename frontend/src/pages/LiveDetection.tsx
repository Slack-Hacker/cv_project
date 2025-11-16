import { useState, useEffect, useRef } from "react";
import axios from "axios";
import type { DetectResult } from "../types/detect";

export default function LiveDetection() {
  const [cameraUrl, setCameraUrl] = useState("");
  const [result, setResult] = useState<DetectResult | null>(null);

  const imgRef = useRef<HTMLImageElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Poll detection every 600ms
  useEffect(() => {
    if (!cameraUrl) return;

    const interval = setInterval(async () => {
      try {
        const res = await axios.get("/api/detect/stream", {
          params: { url: cameraUrl },
        });
        setResult(res.data.result);
      } catch {
        setResult({ error: "stream_error" });
      }
    }, 600);

    return () => clearInterval(interval);
  }, [cameraUrl]);

  // Draw bounding box on canvas
  useEffect(() => {
    if (!result || !result.bbox_px) {
      const ctx = canvasRef.current?.getContext("2d");
      if (ctx) ctx.clearRect(0, 0, canvasRef.current!.width, canvasRef.current!.height);
      return;
    }

    const img = imgRef.current;
    const canvas = canvasRef.current;

    if (!img || !canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Wait for image to load
    const displayW = img.clientWidth;
    const displayH = img.clientHeight;

    canvas.width = displayW;
    canvas.height = displayH;

    ctx.clearRect(0, 0, displayW, displayH);

    // Scale factors
    const naturalW = img.naturalWidth;
    const naturalH = img.naturalHeight;

    const scaleX = displayW / naturalW;
    const scaleY = displayH / naturalH;

    const [x1, y1, x2, y2] = result.bbox_px;

    ctx.strokeStyle = "lime";
    ctx.lineWidth = 3;
    ctx.strokeRect(
      x1 * scaleX,
      y1 * scaleY,
      (x2 - x1) * scaleX,
      (y2 - y1) * scaleY
    );

    // Label
    ctx.font = "16px Arial";
    ctx.fillStyle = "lime";
    ctx.fillText(
      result.region ?? "",
      x1 * scaleX + 5,
      Math.max(15, y1 * scaleY - 5)
    );

  }, [result]);

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Live Detection</h1>

      <input
        type="text"
        placeholder="http://192.168.x.x:8080/video"
        className="border p-2 w-full rounded"
        onChange={(e) => setCameraUrl(e.target.value)}
      />

      {/* Live Video + Overlay Box */}
      <div className="relative w-fit">
        {cameraUrl && (
          <>
            <img
              ref={imgRef}
              src={cameraUrl}
              alt="live"
              className="max-w-lg border rounded"
              onLoad={() => {
                // Resize canvas when image loads
                if (imgRef.current && canvasRef.current) {
                  canvasRef.current.width = imgRef.current.clientWidth;
                  canvasRef.current.height = imgRef.current.clientHeight;
                }
              }}
            />
            <canvas
              ref={canvasRef}
              className="absolute top-0 left-0 pointer-events-none"
            />
          </>
        )}
      </div>

      {/* Detection Info */}
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
