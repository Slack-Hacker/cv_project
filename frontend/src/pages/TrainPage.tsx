import axios from "axios";
import { useState, useEffect, useRef } from "react";

export default function TrainPage() {
  const [files, setFiles] = useState<File[] | null>(null);
  const [needsManual, setNeedsManual] = useState<string[]>([]);
  const [status, setStatus] = useState<any>(null);
  const polling = useRef<any>(null);

  async function upload() {
    if (!files) return alert("Select at least 5–10 images.");

    const form = new FormData();
    files.forEach((f) => form.append("files", f));

    const res = await axios.post("/api/train/upload", form);
    const low = await axios.get("/api/train/low_conf");
    setNeedsManual(low.data.needs_manual || []);
  }

  function startTrain() {
    axios.post("/api/train/start");

    polling.current = setInterval(async () => {
      const s = await axios.get("/api/train/status");
      setStatus(s.data);
      if (!s.data.running) clearInterval(polling.current);
    }, 1500);
  }

  return (
    <div className="space-y-10">
      <h1 className="text-3xl font-bold">Train Your Model</h1>

      <div className="bg-white p-6 rounded-xl shadow border space-y-4">
        <input
          type="file"
          multiple
          onChange={(e) => setFiles(e.target.files ? [...e.target.files] : null)}
          className="border p-3 rounded-lg w-full"
        />

        <button
          onClick={upload}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          Upload & Auto Label
        </button>
      </div>

      <div className="bg-white p-6 rounded-xl shadow border space-y-3">
        <h2 className="text-xl font-bold">Fix Low-Confidence Images</h2>

        {needsManual.length === 0 && (
          <p className="text-gray-500 text-sm">No images need manual labeling.</p>
        )}

        {needsManual.map((n) => (
          <div key={n} className="flex items-center gap-4 bg-gray-50 p-3 rounded-lg border">
            <img
              src={`/user_images/${n}`}
              className="h-16 w-24 object-cover rounded border"
            />
            <div>
              <p>{n}</p>
              <a
                href={"/manual?img=" + n}
                className="text-blue-600 hover:underline text-sm"
              >
                Fix Now
              </a>
            </div>
          </div>
        ))}
      </div>

      <button
        onClick={startTrain}
        className="bg-green-600 text-white px-4 py-3 rounded-lg hover:bg-green-700"
      >
        Start Training
      </button>

      {status && (
        <div className="bg-gray-100 p-4 rounded-lg border shadow text-sm space-y-1">
          <p>Status: {status.status}</p>
          <p>Progress: {(status.progress * 100).toFixed(1)}%</p>
          <pre className="text-xs max-h-40 overflow-auto">{status.log_tail.join("\n")}</pre>
        </div>
      )}
    </div>
  );
}
