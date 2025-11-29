import { Link, useLocation } from "react-router-dom";

export default function Navbar() {
  const { pathname } = useLocation();

  const navLink = (to: string, label: string) => (
    <Link
      to={to}
      className={`px-4 py-2 rounded-md transition-all duration-200 font-medium ${
        pathname === to
          ? "bg-blue-600 text-white shadow"
          : "text-gray-700 hover:bg-blue-100 hover:text-blue-700"
      }`}
    >
      {label}
    </Link>
  );

  return (
    <nav className="bg-white shadow border-b sticky top-0 z-50">
      <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link to="/" className="text-2xl font-bold text-blue-600">
          Thundrive
        </Link>

        <div className="flex items-center gap-3">
          {navLink("/", "Home")}
          {navLink("/live", "Live Detection")}
          {navLink("/upload", "Upload Detect")}
          {navLink("/train", "Train Model")}
        </div>
      </div>
    </nav>
  );
}
