import { useParams, useNavigate } from "react-router-dom";
import { useRef, useState, useEffect } from "react";
import axios from "axios";

export default function ManualLabelPage() {
  const { img } = useParams();
  const navigate = useNavigate();

  const imgRef = useRef<HTMLImageElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const [points, setPoints] = useState<number[][]>([]);

  const imgUrl = `http://localhost:8000/user_images/${img}`;

  const DISPLAY_W = 480;
  const DISPLAY_H = 640;

  useEffect(() => {
    drawBox();
  }, [points]);

  const handleImageLoad = () => {
    const imgEl = imgRef.current!;
    const canvas = canvasRef.current!;
    if (!imgEl || !canvas) return;

    // Fix display size
    imgEl.style.width = `${DISPLAY_W}px`;
    imgEl.style.height = `${DISPLAY_H}px`;
    imgEl.style.pointerEvents = "none";       // IMPORTANT
    imgEl.style.position = "absolute";
    imgEl.style.top = "0";
    imgEl.style.left = "0";
    imgEl.style.zIndex = "5";

    // Canvas must be on top
    canvas.width = DISPLAY_W;
    canvas.height = DISPLAY_H;
    canvas.style.width = `${DISPLAY_W}px`;
    canvas.style.height = `${DISPLAY_H}px`;
    canvas.style.position = "absolute";
    canvas.style.top = "0";
    canvas.style.left = "0";
    canvas.style.zIndex = "10";               // ABOVE image
  };

  const handleCanvasClick = (e: any) => {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();

    const x = Math.round((e.clientX - rect.left) * (canvas.width / rect.width));
    const y = Math.round((e.clientY - rect.top) * (canvas.height / rect.height));

    if (points.length === 0) setPoints([[x, y]]);
    else if (points.length === 1) setPoints([...points, [x, y]]);
    else setPoints([[x, y]]);
  };

  const drawBox = () => {
    const canvas = canvasRef.current!;
    const ctx = canvas.getContext("2d")!;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (points.length !== 2) return;

    const [p1, p2] = points;
    const [x1, y1] = p1;
    const [x2, y2] = p2;

    ctx.strokeStyle = "lime";
    ctx.lineWidth = 3;
    ctx.strokeRect(
      Math.min(x1, x2),
      Math.min(y1, y2),
      Math.abs(x2 - x1),
      Math.abs(y2 - y1)
    );
  };

  const handleSave = async () => {
    if (points.length !== 2) {
      alert("Select two corners");
      return;
    }

    const imgEl = imgRef.current!;
    const naturalW = imgEl.naturalWidth;
    const naturalH = imgEl.naturalHeight;

    // convert display → natural
    const scaleX = naturalW / DISPLAY_W;
    const scaleY = naturalH / DISPLAY_H;

    const [p1, p2] = points;
    const [dx1, dy1] = p1;
    const [dx2, dy2] = p2;

    const x1 = Math.round(dx1 * scaleX);
    const y1 = Math.round(dy1 * scaleY);
    const x2 = Math.round(dx2 * scaleX);
    const y2 = Math.round(dy2 * scaleY);

    await axios.post("http://localhost:8000/api/label/manual", {
      image: img,
      x1,
      y1,
      x2,
      y2,
      img_w: naturalW,
      img_h: naturalH,
    });

    const list = JSON.parse(localStorage.getItem("low_conf_images") || "[]");
    const updated = list.filter((item: any) => item.image !== img);
    localStorage.setItem("low_conf_images", JSON.stringify(updated));

    alert("Saved!");
    navigate("/train");
  };

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-4">
      <h1 className="text-xl font-bold">Fix Label — {img}</h1>

      <div
        className="relative border"
        style={{ width: DISPLAY_W, height: DISPLAY_H }}
      >
        <img ref={imgRef} src={imgUrl} onLoad={handleImageLoad} />

        <canvas
          ref={canvasRef}
          onClick={handleCanvasClick}
          className="cursor-crosshair"
        />
      </div>

      <button
        onClick={handleSave}
        className="bg-blue-600 text-white px-4 py-2 rounded"
      >
        Save Label
      </button>
    </div>
  );
}
