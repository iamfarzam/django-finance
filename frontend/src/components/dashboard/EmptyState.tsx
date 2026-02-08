'use client';

import { Button } from '@/components/ui';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  actionLabel?: string;
  actionHref?: string;
}

export function EmptyState({
  title,
  description,
  icon,
  actionLabel,
  actionHref,
}: EmptyStateProps) {
  return (
    <div className="text-center py-12 px-6">
      {icon ? (
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
          {icon}
        </div>
      ) : (
        <svg
          className="h-16 w-16 mx-auto mb-4 text-gray-300"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
          />
        </svg>
      )}
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-500 max-w-sm mx-auto mb-6">{description}</p>
      {actionLabel && actionHref && (
        <a href={actionHref}>
          <Button variant="primary">{actionLabel}</Button>
        </a>
      )}
    </div>
  );
}
