import { Link, useLocation } from "react-router-dom";
import { Home, ImageIcon, Camera, Cog } from "lucide-react";

const links = [
  { to: "/", label: "Dashboard", icon: Home },
  { to: "/upload", label: "Upload Detect", icon: ImageIcon },
  { to: "/live", label: "Live Detection", icon: Camera },
  { to: "/train", label: "Train Model", icon: Cog },
];

export default function Sidebar() {
  const { pathname } = useLocation();

  return (
    <aside className="fixed inset-y-0 left-0 w-64 bg-white border-r border-gray-200 
      px-6 py-8 flex flex-col gap-6 shadow-sm">

      {/* Logo / Title */}
      <div>
        <h1 className="text-xl font-bold text-gray-800">CV Project</h1>
        <p className="text-xs text-gray-500">YOLOv8 Dashboard</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1">
        {links.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.to;

          return (
            <Link
              key={item.to}
              to={item.to}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all
                ${
                  active
                    ? "bg-blue-100 text-blue-700 font-medium"
                    : "text-gray-700 hover:bg-gray-100"
                }`}
            >
              <Icon size={18} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="text-[11px] text-gray-400">
        Computer Vision Project UI
      </div>
    </aside>
  );
}
