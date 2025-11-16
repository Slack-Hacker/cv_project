export default function Home() {
  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">Welcome to cv1 Project</h1>
      <p className="text-gray-700 text-lg leading-relaxed">
        This application allows you to train a custom object detector and perform 
        live object detection using your Android IP webcam. Navigate using the 
        links above to get started.
      </p>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="p-6 bg-white rounded-lg shadow border hover:shadow-lg transition">
          <h2 className="text-xl font-semibold mb-2">Live Detection</h2>
          <p className="text-gray-600">
            View real-time detection from your Android camera feed.
          </p>
        </div>

        <div className="p-6 bg-white rounded-lg shadow border hover:shadow-lg transition">
          <h2 className="text-xl font-semibold mb-2">Upload Detection</h2>
          <p className="text-gray-600">
            Upload an image and detect your custom object with bounding boxes.
          </p>
        </div>
      </div>
    </div>
  );
}
