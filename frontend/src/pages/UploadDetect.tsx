import { useState } from "react";
import axios from "axios";

export default function UploadDetect() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  async function detect() {
    if (!file) return;

    const form = new FormData();
    form.append("file", file);

    const res = await axios.post("/api/detect/image", form);
    setResult(res.data.result);
  }

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Upload Detection</h1>

      <div className="bg-white p-6 rounded-xl shadow border space-y-4">
        <input
          type="file"
          accept="image/*"
          className="border p-3 rounded-lg w-full"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (!f) return;
            setFile(f);
            setPreview(URL.createObjectURL(f));
          }}
        />

        {preview && (
          <img
            src={preview}
            className="max-w-md rounded-lg border shadow"
            alt="preview"
          />
        )}

        <button
          onClick={detect}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          Detect
        </button>
      </div>

      {result && (
        <div className="bg-white p-4 rounded-xl border shadow space-y-1 text-sm">
          <p className="font-semibold">
            {result.detected ? "✔ Detected" : "❌ Not Detected"}
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
        </div>
      )}
    </div>
  );
}
