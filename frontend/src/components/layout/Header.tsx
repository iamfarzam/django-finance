'use client';

import { useState } from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils/cn';

interface NavItem {
  label: string;
  href: string;
}

const navItems: NavItem[] = [
  { label: 'Dashboard', href: '/react/dashboard/' },
  { label: 'Accounts', href: '/accounts/' },
  { label: 'Transactions', href: '/transactions/' },
  { label: 'Contacts', href: '/contacts/' },
  { label: 'Debts', href: '/debts/' },
];

interface HeaderProps {
  user?: {
    name: string;
    email: string;
  } | null;
}

export function Header({ user }: HeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo and Desktop Nav */}
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <Link href="/react/dashboard/" className="flex items-center gap-2">
                <svg
                  className="h-8 w-8 text-primary-600"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <span className="font-semibold text-xl text-gray-900">
                  Django Finance
                </span>
              </Link>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden sm:ml-8 sm:flex sm:space-x-1">
              {navItems.map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'inline-flex items-center px-3 py-2 text-sm font-medium rounded-md',
                    'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  )}
                >
                  {item.label}
                </a>
              ))}
            </div>
          </div>

          {/* User Menu */}
          <div className="hidden sm:ml-6 sm:flex sm:items-center">
            {user ? (
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900 focus:outline-none"
                >
                  <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                    <span className="text-primary-700 font-medium">
                      {user.name.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <span className="font-medium">{user.name}</span>
                  <svg
                    className={cn(
                      'h-4 w-4 transition-transform',
                      userMenuOpen && 'rotate-180'
                    )}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>

                {userMenuOpen && (
                  <div className="absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5">
                    <div className="py-1">
                      <a
                        href="/profile/"
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        Profile
                      </a>
                      <a
                        href="/settings/"
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        Settings
                      </a>
                      <hr className="my-1" />
                      <a
                        href="/accounts/logout/"
                        className="block px-4 py-2 text-sm text-danger-600 hover:bg-gray-100"
                      >
                        Sign out
                      </a>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <a
                href="/accounts/login/"
                className="inline-flex items-center px-4 py-2 text-sm font-medium rounded-lg bg-primary-600 text-white hover:bg-primary-700"
              >
                Sign in
              </a>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="flex items-center sm:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none"
            >
              <svg
                className="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                {mobileMenuOpen ? (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                ) : (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="sm:hidden border-t border-gray-200 pt-2 pb-3">
            {navItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="block px-3 py-2 text-base font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-md"
              >
                {item.label}
              </a>
            ))}
            <hr className="my-2" />
            {user ? (
              <>
                <div className="px-3 py-2 text-sm text-gray-500">{user.email}</div>
                <a
                  href="/profile/"
                  className="block px-3 py-2 text-base font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-md"
                >
                  Profile
                </a>
                <a
                  href="/accounts/logout/"
                  className="block px-3 py-2 text-base font-medium text-danger-600 hover:bg-gray-50 rounded-md"
                >
                  Sign out
                </a>
              </>
            ) : (
              <a
                href="/accounts/login/"
                className="block px-3 py-2 text-base font-medium text-primary-600 hover:bg-gray-50 rounded-md"
              >
                Sign in
              </a>
            )}
          </div>
        )}
      </nav>
    </header>
  );
}
