import { Link, useLocation } from "react-router-dom";

export default function Navbar() {
  const { pathname } = useLocation();

  const navLink = (to: string, label: string) => (
    <Link
      to={to}
      className={`px-4 py-2 rounded-md text-sm font-medium transition-all
        ${pathname === to 
          ? "bg-blue-600 text-white shadow" 
          : "text-gray-700 hover:bg-blue-100"
        }`}
    >
      {label}
    </Link>
  );

  return (
    <nav className="bg-white border-b shadow-sm sticky top-0 z-50">
      <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link to="/" className="text-2xl font-bold text-blue-600 tracking-tight">
          Thundrive
        </Link>
        <div className="flex items-center gap-2">
          {navLink("/", "Home")}
          {navLink("/live", "Live Detection")}
          {navLink("/upload", "Upload Detect")}
        </div>
      </div>
    </nav>
  );
}
