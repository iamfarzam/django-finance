export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white border-t border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2 text-gray-500 text-sm">
            <svg
              className="h-5 w-5 text-primary-600"
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
            <span>&copy; {currentYear} Django Finance. All rights reserved.</span>
          </div>
          <div className="flex gap-6 text-sm text-gray-500">
            <a href="/privacy/" className="hover:text-gray-700">
              Privacy Policy
            </a>
            <a href="/terms/" className="hover:text-gray-700">
              Terms of Service
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
