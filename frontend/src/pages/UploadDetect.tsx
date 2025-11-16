import { useState } from "react";
import axios from "axios";

export default function UploadDetect() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const handleUpload = async () => {
    if (!file) return;

    const form = new FormData();
    form.append("file", file);

    const res = await axios.post("/api/detect/image", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    setResult(res.data.result);
  };

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Upload Detection</h1>

      <input
        type="file"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (!f) return;
          setFile(f);
          setPreview(URL.createObjectURL(f));
        }}
        className="border p-2 rounded"
      />

      {preview && (
        <img
          src={preview}
          alt="preview"
          className="max-w-md border rounded shadow"
        />
      )}

      <button
        onClick={handleUpload}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        Detect
      </button>

      {result && (
        <div className="p-4 bg-white border rounded shadow space-y-2">
          <p className="font-semibold">
            {result.detected ? "✔ Detected" : "❌ Not Detected"}
          </p>

          {result.detected && (
            <>
              <p>Region: {result.region}</p>
              <p>
                Visible ≥30%:{" "}
                <b className={result.visible_30_percent ? "text-green-600" : "text-red-600"}>
                  {result.visible_30_percent ? "Yes" : "No"}
                </b>
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
}
