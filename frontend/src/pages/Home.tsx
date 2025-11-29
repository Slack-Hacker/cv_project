export default function Home() {
  return (
    <div className="space-y-10">
      <div className="text-center space-y-3">
        <h1 className="text-4xl font-bold">Welcome to Thundrive CV Project</h1>
        <p className="text-gray-600 text-lg">
          Train your own object and detect it in real-time from your phone camera.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <a
          href="/live"
          className="p-6 bg-white rounded-xl shadow border hover:shadow-lg transition transform hover:-translate-y-1"
        >
          <h2 className="text-xl font-semibold mb-1">Live Detection</h2>
          <p className="text-gray-600">Real-time detection from your Android camera.</p>
        </a>

        <a
          href="/train"
          className="p-6 bg-white rounded-xl shadow border hover:shadow-lg transition transform hover:-translate-y-1"
        >
          <h2 className="text-xl font-semibold mb-1">Train Model</h2>
          <p className="text-gray-600">Upload images and train your YOLO model.</p>
        </a>

        <a
          href="/upload"
          className="p-6 bg-white rounded-xl shadow border hover:shadow-lg transition transform hover:-translate-y-1"
        >
          <h2 className="text-xl font-semibold mb-1">Detect in Image</h2>
          <p className="text-gray-600">Upload image and detect objects inside it.</p>
        </a>
      </div>
    </div>
  );
}
