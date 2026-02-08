'use client';

import { Card, CardContent, CardHeader, CardTitle, Badge } from '@/components/ui';
import { formatCurrency, formatDate } from '@/lib/utils';
import { cn } from '@/lib/utils/cn';

interface Transaction {
  id: string;
  description: string;
  amount: number;
  transaction_type: 'income' | 'expense' | 'transfer';
  date: string;
  account_name?: string;
  category_name?: string;
}

interface RecentTransactionsProps {
  transactions: Transaction[];
}

export function RecentTransactions({ transactions }: RecentTransactionsProps) {
  if (transactions.length === 0) {
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
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
            Recent Transactions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
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
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
            <p>No transactions yet</p>
            <a
              href="/transactions/new/"
              className="text-primary-600 hover:text-primary-700 text-sm mt-2 inline-block"
            >
              Add your first transaction
            </a>
          </div>
        </CardContent>
      </Card>
    );
  }

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
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
          Recent Transactions
        </CardTitle>
        <a
          href="/transactions/"
          className="text-sm text-primary-600 hover:text-primary-700"
        >
          View all
        </a>
      </CardHeader>
      <CardContent className="p-0">
        <ul className="divide-y divide-gray-100">
          {transactions.map((txn) => (
            <li
              key={txn.id}
              className="px-6 py-3 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      'p-2 rounded-full',
                      txn.transaction_type === 'income'
                        ? 'bg-success-100'
                        : txn.transaction_type === 'expense'
                        ? 'bg-danger-100'
                        : 'bg-gray-100'
                    )}
                  >
                    {txn.transaction_type === 'income' ? (
                      <svg
                        className="h-4 w-4 text-success-600"
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
                    ) : txn.transaction_type === 'expense' ? (
                      <svg
                        className="h-4 w-4 text-danger-600"
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
                    ) : (
                      <svg
                        className="h-4 w-4 text-gray-600"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
                        />
                      </svg>
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{txn.description}</p>
                    <p className="text-sm text-gray-500">
                      {txn.account_name && <span>{txn.account_name}</span>}
                      {txn.account_name && txn.category_name && <span> &middot; </span>}
                      {txn.category_name && <span>{txn.category_name}</span>}
                      {!txn.account_name && !txn.category_name && (
                        <span>{formatDate(txn.date)}</span>
                      )}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p
                    className={cn(
                      'font-semibold',
                      txn.transaction_type === 'income'
                        ? 'text-success-600'
                        : txn.transaction_type === 'expense'
                        ? 'text-danger-600'
                        : 'text-gray-900'
                    )}
                  >
                    {txn.transaction_type === 'income' ? '+' : txn.transaction_type === 'expense' ? '-' : ''}
                    {formatCurrency(txn.amount)}
                  </p>
                  <p className="text-xs text-gray-400">{formatDate(txn.date)}</p>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
