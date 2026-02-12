interface SkeletonProps {
  variant: "line" | "card" | "circle" | "grid" | "list" | "reading";
  count?: number;
  className?: string;
}

function ShimmerBar({ className }: { className?: string }) {
  return (
    <div
      className={`rounded bg-[var(--nps-bg-input)] animate-shimmer ${className ?? ""}`}
      style={{
        backgroundImage:
          "linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent)",
        backgroundSize: "200% 100%",
      }}
    />
  );
}

function LineSkeleton() {
  return <ShimmerBar className="h-4 w-full" />;
}

function CardSkeleton() {
  return <ShimmerBar className="h-24 w-full rounded-lg" />;
}

function CircleSkeleton() {
  return <ShimmerBar className="w-10 h-10 rounded-full" />;
}

function GridSkeleton() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <CardSkeleton />
      <CardSkeleton />
      <CardSkeleton />
      <CardSkeleton />
    </div>
  );
}

function ListSkeleton() {
  return (
    <div className="space-y-2">
      <ShimmerBar className="h-4 w-full" />
      <ShimmerBar className="h-4 w-3/4" />
      <ShimmerBar className="h-4 w-5/6" />
      <ShimmerBar className="h-4 w-2/3" />
      <ShimmerBar className="h-4 w-4/5" />
    </div>
  );
}

function ReadingSkeleton() {
  return (
    <div className="flex gap-3">
      <CircleSkeleton />
      <div className="flex-1 space-y-2">
        <ShimmerBar className="h-4 w-1/2" />
        <ShimmerBar className="h-4 w-full" />
        <ShimmerBar className="h-4 w-3/4" />
        <CardSkeleton />
      </div>
    </div>
  );
}

const VARIANT_MAP: Record<SkeletonProps["variant"], () => JSX.Element> = {
  line: LineSkeleton,
  card: CardSkeleton,
  circle: CircleSkeleton,
  grid: GridSkeleton,
  list: ListSkeleton,
  reading: ReadingSkeleton,
};

export function LoadingSkeleton({
  variant,
  count = 1,
  className,
}: SkeletonProps) {
  const Component = VARIANT_MAP[variant];
  const items = Array.from({ length: count }, (_, i) => i);

  return (
    <div
      aria-hidden="true"
      className={`space-y-3 ${className ?? ""}`}
      data-testid="loading-skeleton"
    >
      <span className="sr-only">Loading</span>
      {items.map((i) => (
        <Component key={i} />
      ))}
    </div>
  );
}
