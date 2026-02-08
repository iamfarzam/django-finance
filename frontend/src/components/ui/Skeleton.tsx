import { cn } from '@/lib/utils/cn';

export interface SkeletonProps {
  className?: string;
}

function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-md bg-gray-200',
        className
      )}
    />
  );
}

function SkeletonText({ className }: SkeletonProps) {
  return <Skeleton className={cn('h-4 w-full', className)} />;
}

function SkeletonCircle({ className }: SkeletonProps) {
  return <Skeleton className={cn('h-10 w-10 rounded-full', className)} />;
}

function SkeletonCard({ className }: SkeletonProps) {
  return (
    <div className={cn('rounded-lg bg-white shadow-sm p-6 space-y-4', className)}>
      <Skeleton className="h-6 w-1/3" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-2/3" />
    </div>
  );
}

export { Skeleton, SkeletonText, SkeletonCircle, SkeletonCard };
