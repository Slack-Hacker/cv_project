import { Routes, Route, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";

import Sidebar from "./components/Sidebar";
import Loader from "./components/Loader";

import Home from "./pages/Home";
import UploadDetect from "./pages/UploadDetect";
import LiveDetection from "./pages/LiveDetection";
import TrainPage from "./pages/TrainPage";

export default function App() {
  const location = useLocation();

  return (
    <div className="flex min-h-screen bg-gray-100 text-gray-900">

      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <main className="flex-1 ml-64 p-8">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.25 }}
            className="max-w-6xl mx-auto space-y-8"
          >
            <Routes location={location}>
              <Route path="/" element={<Home />} />
              <Route path="/upload" element={<UploadDetect />} />
              <Route path="/live" element={<LiveDetection />} />
              <Route path="/train" element={<TrainPage />} />
            </Routes>
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
