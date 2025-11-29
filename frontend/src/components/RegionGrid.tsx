type RegionGridProps = {
  activeIndex?: number | null; // 0–8, if you want to highlight
};

export default function RegionGrid({ activeIndex = null }: RegionGridProps) {
  return (
    <div className="w-full max-w-md mx-auto">
      <h2 className="mb-3 text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
        Region Visualization (3 × 3)
      </h2>
      <div className="grid grid-cols-3 gap-2">
        {Array.from({ length: 9 }).map((_, idx) => {
          const isActive = activeIndex === idx;
          return (
            <div
              key={idx}
              className={`aspect-square rounded-xl border flex items-center justify-center text-xs font-medium
              ${
                isActive
                  ? "border-amber-400 bg-amber-400/15 text-amber-300"
                  : "border-slate-700/70 bg-slate-900/40 text-slate-400"
              }`}
            >
              {`Region ${idx + 1}`}
            </div>
          );
        })}
      </div>
      <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
        (You can map detection confidence to specific regions later.)
      </p>
    </div>
  );
}
