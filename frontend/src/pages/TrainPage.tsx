import { useEffect, useRef, useState } from "react";
import axios from "axios";

export default function TrainPage() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [labelName, setLabelName] = useState("");

  // Upload states
  const [uploadPhase, setUploadPhase] =
    useState<"idle" | "uploading" | "auto-labeling" | "done" | "failed">("idle");
  const [uploadPercent, setUploadPercent] = useState(0);
  const [uploadCurrent, setUploadCurrent] = useState<string | null>(null);
  const [autoLabelErrors, setAutoLabelErrors] = useState<any[]>([]);
  const [uploadDone, setUploadDone] = useState(false);

  // Training states
  const [trainingStatus, setTrainingStatus] = useState<any | null>(null);
  const [pollTraining, setPollTraining] = useState(false);

  const [message, setMessage] = useState("");

  const uploadIntervalRef = useRef<number | null>(null);

  // ------------------------------------------------------------
  // LOAD EXISTING LOW-CONFIDENCE IMAGES (manual + auto)
  // ------------------------------------------------------------
  useEffect(() => {
    const refresh = () => {
      const saved = localStorage.getItem("low_conf_images");
      const parsed = saved ? JSON.parse(saved) : [];

      setAutoLabelErrors(parsed);

      // If we have saved errors → mark upload done
      setUploadDone(true);
    };

    refresh();

    // Refresh when user comes back from /label/:img
    window.addEventListener("focus", refresh);
    return () => window.removeEventListener("focus", refresh);
  }, []);

  // ------------------------------------------------------------
  // TRAIN STATUS POLLING
  // ------------------------------------------------------------
  useEffect(() => {
    if (!pollTraining) return;

    const id = window.setInterval(async () => {
      try {
        const res = await axios.get("/api/train/status");
        setTrainingStatus(res.data);

        if (!res.data.running) {
          setPollTraining(false);
        }
      } catch (err) {
        setMessage("Failed to fetch training status.");
        setPollTraining(false);
      }
    }, 1000);

    return () => clearInterval(id);
  }, [pollTraining]);

  // ------------------------------------------------------------
  // UPLOAD POLLING
  // ------------------------------------------------------------
  const pollUploadStatus = () => {
    if (uploadIntervalRef.current) {
      clearInterval(uploadIntervalRef.current);
      uploadIntervalRef.current = null;
    }

    const id = window.setInterval(async () => {
      try {
        const res = await axios.get("/api/train/upload-status");
        const s = res.data;

        setUploadPhase(s.phase ?? "idle");
        setUploadPercent(Number(s.percent) || 0);
        setUploadCurrent(s.current ?? null);

        // live errors from backend
        const errorsArray = Array.isArray(s.errors) ? s.errors : [];
        setAutoLabelErrors(errorsArray);

        // update localStorage continuously
        localStorage.setItem("low_conf_images", JSON.stringify(errorsArray));

        if (s.phase === "done") {
          clearInterval(id);
          uploadIntervalRef.current = null;

          setUploadDone(true);
          setMessage("Upload + Auto-label completed.");
        }

        if (s.phase === "failed") {
          clearInterval(id);
          uploadIntervalRef.current = null;

          setUploadDone(false);
          setMessage("Upload / auto-label failed.");
        }
      } catch (err) {
        clearInterval(id);
        uploadIntervalRef.current = null;
        setMessage("Failed to fetch upload status.");
      }
    }, 500);

    uploadIntervalRef.current = id;
  };

  // ------------------------------------------------------------
  // START UPLOAD
  // ------------------------------------------------------------
  const handleUpload = async () => {
    if (!labelName.trim()) {
      alert("Enter a label name!");
      return;
    }
    if (!files || files.length === 0) {
      alert("Select images first");
      return;
    }

    setMessage("Uploading…");
    setUploadDone(false);
    setUploadPhase("uploading");
    setUploadPercent(0);
    setUploadCurrent(null);
    setTrainingStatus(null);
    setAutoLabelErrors([]);

    localStorage.removeItem("low_conf_images"); // reset

    const form = new FormData();
    form.append("label", labelName);

    for (let i = 0; i < files.length; i++) {
      form.append("files", files[i]);
    }

    try {
      await axios.post("/api/train/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      pollUploadStatus();
    } catch (err) {
      setMessage("Upload failed.");
      setUploadPhase("failed");
    }
  };

  // ------------------------------------------------------------
  // START TRAINING
  // ------------------------------------------------------------
  const startTraining = async () => {
    setMessage("Training started…");
    setTrainingStatus({ status: "training", progress: 0 });
    setPollTraining(true);

    try {
      await axios.post("/api/train/start");
      const s = await axios.get("/api/train/status");
      setTrainingStatus(s.data);
    } catch (err: any) {
      setTrainingStatus({
        status: "failed",
        progress: 0,
        error: err?.response?.data?.detail || err?.message || "Failed",
      });
      setPollTraining(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-8">
      <h1 className="text-3xl font-bold">Train Custom YOLO Model</h1>

      {message && (
        <div className="p-3 bg-blue-100 border border-blue-300 rounded text-blue-700">
          {message}
        </div>
      )}

      {/* ------------------------------------------------------------
          1. Upload & Auto-label Section
      ------------------------------------------------------------ */}
      <div className="p-6 bg-white rounded shadow border space-y-4">
        <h2 className="text-xl font-semibold">1. Upload Images</h2>

        <input
          type="text"
          placeholder="Enter label name (e.g., phone)"
          className="border p-2 rounded w-full"
          value={labelName}
          onChange={(e) => setLabelName(e.target.value)}
        />

        <input
          type="file"
          multiple
          accept="image/*"
          className="border p-2 rounded"
          onChange={(e) => setFiles(e.target.files)}
        />

        <button
          onClick={handleUpload}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Upload & Auto-label
        </button>

        {/* Progress */}
        {uploadPhase !== "idle" && !uploadDone && (
          <div className="space-y-2 mt-3">
            <p className="font-medium">Phase: <b>{uploadPhase}</b></p>

            <div className="w-full bg-gray-300 h-4 rounded">
              <div
                className="bg-blue-600 h-4 rounded"
                style={{ width: `${uploadPercent}%` }}
              ></div>
            </div>

            {uploadCurrent && (
              <p className="text-gray-700 text-sm">
                Processing: {uploadCurrent}
              </p>
            )}
          </div>
        )}
      </div>

      {/* ------------------------------------------------------------
          2. Manual Fix List (localStorage driven)
      ------------------------------------------------------------ */}
      {uploadDone && (
        <div className="p-6 bg-white rounded shadow border space-y-3">
          <h2 className="text-xl font-semibold">2. Manual Fix Needed</h2>

          <ManualFixList autoLabelErrors={autoLabelErrors} />
        </div>
      )}


      {/* ------------------------------------------------------------
          3. Training Section
      ------------------------------------------------------------ */}
      {uploadDone && (
        <div className="p-6 bg-white rounded shadow border space-y-3">
          <h2 className="text-xl font-semibold">3. Train Model</h2>

          <button
            onClick={startTraining}
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
          >
            Start Training
          </button>

          {trainingStatus && (
            <div className="space-y-3 mt-3">
              <div className="w-full bg-gray-200 h-4 rounded">
                <div
                  className="bg-green-600 h-4 rounded"
                  style={{
                    width: `${trainingStatus.progress || 0}%`,
                    transition: "width 0.4s",
                  }}
                ></div>
              </div>

              <p>Status: <b>{trainingStatus.status}</b></p>

              {trainingStatus.error && (
                <p className="text-red-600">Error: {trainingStatus.error}</p>
              )}

              {trainingStatus.status === "done" && (
                <p className="text-green-700 font-bold">
                  ✔ Training Completed — Model Updated!
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}


function ManualFixList({ autoLabelErrors }: any) {
  const [existingLabels, setExistingLabels] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/labels/status");
        const data = await res.json();
        setExistingLabels(data);
      } catch (err) {
        console.error("label status load failed", err);
      }
    };

    load();

    // re-check when user returns from /label
    window.addEventListener("focus", load);
    return () => window.removeEventListener("focus", load);
  }, []);

  // filter images that don't have a label.txt
  const pending = autoLabelErrors.filter((err: any) => {
    const name = err.image.split(".")[0];
    return !existingLabels[name];
  });

  if (pending.length === 0) {
    return <p className="text-green-600">All images fixed ✔</p>;
  }

  return (
    <>
      <p className="text-red-600 font-semibold">Low-confidence images:</p>

      <ul className="list-disc pl-6">
        {pending.map((err: any, idx: number) => (
          <li key={idx} className="flex items-center gap-4">
            <span><b>{err.image}</b> — {err.reason}</span>

            <button
              onClick={() => (window.location.href = `/label/${err.image}`)}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Fix
            </button>
          </li>
        ))}
      </ul>
    </>
  );
}
