'use client';

import { useEffect } from 'react';
import { MainLayout } from '@/components/layout';
import { Button } from '@/components/ui';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error('Dashboard error:', error);
  }, [error]);

  return (
    <MainLayout>
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
        <svg
          className="h-16 w-16 text-danger-500 mb-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Something went wrong
        </h2>
        <p className="text-gray-500 mb-6 max-w-md">
          We encountered an error while loading the dashboard. Please try again
          or contact support if the problem persists.
        </p>
        <div className="flex gap-4">
          <Button onClick={() => reset()}>Try again</Button>
          <a href="/">
            <Button variant="outline">Go to home</Button>
          </a>
        </div>
        {error.digest && (
          <p className="text-xs text-gray-400 mt-4">
            Error ID: {error.digest}
          </p>
        )}
      </div>
    </MainLayout>
  );
}
