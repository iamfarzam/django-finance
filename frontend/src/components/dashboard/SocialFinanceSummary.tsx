'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui';
import { formatCurrency } from '@/lib/utils';
import { cn } from '@/lib/utils/cn';

interface SocialFinanceSummaryProps {
  totalTheyOwe: number;
  totalYouOwe: number;
  netBalance: number;
  currency?: string;
}

export function SocialFinanceSummary({
  totalTheyOwe,
  totalYouOwe,
  netBalance,
  currency = 'USD',
}: SocialFinanceSummaryProps) {
  const hasData = totalTheyOwe > 0 || totalYouOwe > 0;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
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
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
          Social Finance
        </CardTitle>
        <a
          href="/debts/"
          className="text-sm text-primary-600 hover:text-primary-700"
        >
          View all
        </a>
      </CardHeader>
      <CardContent>
        {!hasData ? (
          <div className="text-center py-4 text-gray-500">
            <svg
              className="h-12 w-12 mx-auto mb-4 text-gray-300"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            <p>No debts tracked</p>
            <a
              href="/debts/new/"
              className="text-primary-600 hover:text-primary-700 text-sm mt-2 inline-block"
            >
              Track a debt
            </a>
          </div>
        ) : (
          <div className="space-y-4">
            {/* They Owe You */}
            <div className="flex items-center justify-between p-3 bg-success-50 rounded-lg">
              <div className="flex items-center gap-2">
                <svg
                  className="h-5 w-5 text-success-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 11l5-5m0 0l5 5m-5-5v12"
                  />
                </svg>
                <span className="text-sm text-success-700">They owe you</span>
              </div>
              <span className="font-semibold text-success-700">
                {formatCurrency(totalTheyOwe, currency)}
              </span>
            </div>

            {/* You Owe Them */}
            <div className="flex items-center justify-between p-3 bg-danger-50 rounded-lg">
              <div className="flex items-center gap-2">
                <svg
                  className="h-5 w-5 text-danger-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17 13l-5 5m0 0l-5-5m5 5V6"
                  />
                </svg>
                <span className="text-sm text-danger-700">You owe them</span>
              </div>
              <span className="font-semibold text-danger-700">
                {formatCurrency(totalYouOwe, currency)}
              </span>
            </div>

            {/* Net Balance */}
            <div className="border-t pt-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Net Balance</span>
                <span
                  className={cn(
                    'font-bold text-lg',
                    netBalance >= 0 ? 'text-success-600' : 'text-danger-600'
                  )}
                >
                  {netBalance >= 0 ? '+' : ''}
                  {formatCurrency(netBalance, currency)}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {netBalance > 0
                  ? 'People owe you more than you owe them'
                  : netBalance < 0
                  ? 'You owe more than people owe you'
                  : 'All balanced!'}
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
