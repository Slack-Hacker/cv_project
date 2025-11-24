import Navbar from "./components/Navbar";
import { Routes, Route } from "react-router-dom";

import Home from "./pages/Home";
import LiveDetection from "./pages/LiveDetection";
import UploadDetect from "./pages/UploadDetect";
import TrainPage from "./pages/TrainPage";
import ManualLabelPage from "./pages/ManualLabelPage";

export default function App() {
  return (
    <>
      <Navbar />

      <div className="pt-16 px-4"> 
        {/* Push content below navbar */}
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/live" element={<LiveDetection />} />

          {/* Upload + auto-label (Stage 3-4) */}
          <Route path="/upload" element={<UploadDetect />} />

          {/* User model training (Stage 9) */}
          <Route path="/train" element={<TrainPage />} />

          {/* Manual labeling UI (Stage 4 extended) */}
          <Route path="/label/:img" element={<ManualLabelPage />} />
        </Routes>
      </div>
    </>
  );
}
