export function LoadingSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-4 bg-midnight-800 rounded w-3/4 shimmer" />
      <div className="h-4 bg-midnight-800 rounded w-full shimmer" />
      <div className="h-4 bg-midnight-800 rounded w-5/6 shimmer" />
      <div className="h-4 bg-midnight-800 rounded w-2/3 shimmer" />
    </div>
  );
}

