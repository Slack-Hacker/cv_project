export default function Loader() {
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="flex flex-col items-center gap-3 p-4 rounded-2xl bg-slate-900 text-slate-100 shadow-lg">
        <div className="h-10 w-10 border-2 border-slate-500 border-t-sky-400 rounded-full animate-spin" />
        <p className="text-sm text-slate-200">Running detection…</p>
      </div>
    </div>
  );
}
