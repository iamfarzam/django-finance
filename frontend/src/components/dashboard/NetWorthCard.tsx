'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui';
import { formatCurrency } from '@/lib/utils';
import { cn } from '@/lib/utils/cn';

interface NetWorthCardProps {
  totalAssets: number;
  totalLiabilities: number;
  netWorth: number;
  currency?: string;
}

export function NetWorthCard({
  totalAssets,
  totalLiabilities,
  netWorth,
  currency = 'USD',
}: NetWorthCardProps) {
  const isPositive = netWorth >= 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <svg
            className="h-5 w-5 text-primary-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          Net Worth
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4">
          {/* Assets */}
          <div className="text-center">
            <p className="text-sm text-gray-500 mb-1">Assets</p>
            <p className="text-lg font-semibold text-success-600">
              {formatCurrency(totalAssets, currency)}
            </p>
          </div>

          {/* Liabilities */}
          <div className="text-center">
            <p className="text-sm text-gray-500 mb-1">Liabilities</p>
            <p className="text-lg font-semibold text-danger-600">
              {formatCurrency(totalLiabilities, currency)}
            </p>
          </div>

          {/* Net Worth */}
          <div className="text-center">
            <p className="text-sm text-gray-500 mb-1">Net Worth</p>
            <p
              className={cn(
                'text-lg font-bold',
                isPositive ? 'text-success-600' : 'text-danger-600'
              )}
            >
              {formatCurrency(netWorth, currency)}
            </p>
          </div>
        </div>

        {/* Progress bar visualization */}
        <div className="mt-4">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Assets vs Liabilities</span>
            <span>
              {totalAssets > 0
                ? ((totalAssets / (totalAssets + totalLiabilities)) * 100).toFixed(0)
                : 0}
              % Assets
            </span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-success-500 rounded-full transition-all duration-500"
              style={{
                width: `${
                  totalAssets + totalLiabilities > 0
                    ? (totalAssets / (totalAssets + totalLiabilities)) * 100
                    : 50
                }%`,
              }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
