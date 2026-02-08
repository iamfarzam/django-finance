'use client';

import { MainLayout } from '@/components/layout';
import {
  NetWorthCard,
  StatsGrid,
  RecentTransactions,
  SocialFinanceSummary,
  EmptyState,
} from '@/components/dashboard';
import { useDashboard } from '@/lib/hooks';
import { SkeletonCard } from '@/components/ui';

export default function DashboardPage() {
  const { data, isLoading, error } = useDashboard();

  // Get user from data
  const user = data?.user
    ? { name: data.user.full_name, email: data.user.email }
    : null;

  return (
    <MainLayout user={user}>
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">
          {data?.user
            ? `Welcome back, ${data.user.first_name || 'there'}! Here's your financial overview.`
            : "Welcome back! Here's your financial overview."}
        </p>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="space-y-6">
          <SkeletonCard />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            <SkeletonCard className="h-80" />
            <SkeletonCard className="h-80" />
          </div>
        </div>
      )}

      {/* Error State */}
      {error && !isLoading && (
        <EmptyState
          title="Unable to load dashboard"
          description={error}
          actionLabel="Try again"
          actionHref="/react/dashboard/"
        />
      )}

      {/* Dashboard Content */}
      {data && !isLoading && (
        <div className="space-y-6 animate-fade-in">
          {/* Net Worth Card */}
          <NetWorthCard
            totalAssets={data.net_worth.total_assets}
            totalLiabilities={data.net_worth.total_liabilities}
            netWorth={data.net_worth.net_worth}
            currency={data.net_worth.currency}
          />

          {/* Stats Grid */}
          <StatsGrid stats={data.stats} />

          {/* Two Column Layout */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Recent Transactions */}
            <RecentTransactions transactions={data.recent_transactions} />

            {/* Social Finance Summary */}
            <SocialFinanceSummary
              totalTheyOwe={data.social.total_they_owe}
              totalYouOwe={data.social.total_you_owe}
              netBalance={data.social.net_balance}
              currency={data.social.currency}
            />
          </div>
        </div>
      )}
    </MainLayout>
  );
}
