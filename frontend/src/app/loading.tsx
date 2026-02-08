import { MainLayout } from '@/components/layout';
import { SkeletonCard, Skeleton } from '@/components/ui';

export default function Loading() {
  return (
    <MainLayout>
      {/* Page Header */}
      <div className="mb-8">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-5 w-80 mt-2" />
      </div>

      {/* Dashboard Loading Skeleton */}
      <div className="space-y-6">
        {/* Net Worth Card */}
        <SkeletonCard className="h-40" />

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <SkeletonCard className="h-24" />
          <SkeletonCard className="h-24" />
          <SkeletonCard className="h-24" />
          <SkeletonCard className="h-24" />
        </div>

        {/* Two Column Layout */}
        <div className="grid md:grid-cols-2 gap-6">
          <SkeletonCard className="h-80" />
          <SkeletonCard className="h-80" />
        </div>
      </div>
    </MainLayout>
  );
}
