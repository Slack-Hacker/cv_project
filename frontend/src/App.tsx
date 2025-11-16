import Navbar from "./components/Navbar";
import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import LiveDetection from "./pages/LiveDetection";
import UploadDetect from "./pages/UploadDetect";

export default function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/live" element={<LiveDetection />} />
        <Route path="/upload" element={<UploadDetect />} />
      </Routes>
    </>
  );
}
