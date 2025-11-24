export default function Home() {
  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">Welcome to cv1 Project</h1>
      <p className="text-gray-700 text-lg leading-relaxed">
        Train a custom YOLO model and run real-time object detection using your Android phone camera.
      </p>

      <div className="grid md:grid-cols-2 gap-6">

        {/* Live Detection Card */}
        <a href="/live">
          <div className="p-6 bg-white rounded-lg shadow border hover:shadow-lg transition cursor-pointer">
            <h2 className="text-xl font-semibold mb-2">Live Detection</h2>
            <p className="text-gray-600">
              View real-time detection from your Android camera feed.
            </p>
          </div>
        </a>

        {/* Upload Detection */}
        <a href="/upload">
          <div className="p-6 bg-white rounded-lg shadow border hover:shadow-lg transition cursor-pointer">
            <h2 className="text-xl font-semibold mb-2">Upload Detection</h2>
            <p className="text-gray-600">
              Upload an image and detect your custom object.
            </p>
          </div>
        </a>

        {/* Train Model */}
        <a href="/train">
          <div className="p-6 bg-white rounded-lg shadow border hover:shadow-lg transition cursor-pointer">
            <h2 className="text-xl font-semibold mb-2">Train Model</h2>
            <p className="text-gray-600">
              Upload 10 images, auto-label, fix low-confidence labels and train YOLOv8n.
            </p>
          </div>
        </a>

      </div>
    </div>
  );
}
