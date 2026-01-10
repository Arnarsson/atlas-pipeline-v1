import { Bell, Search, User } from 'lucide-react';

export default function Header() {
  return (
    <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b-4 border-indigo-600 bg-gradient-to-r from-white via-blue-50 to-indigo-50 px-4 shadow-xl sm:gap-x-6 sm:px-6 lg:px-8">
      <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
        <form className="relative flex flex-1" action="#" method="GET">
          <label htmlFor="search-field" className="sr-only">
            Search
          </label>
          <Search
            className="pointer-events-none absolute inset-y-0 left-0 h-full w-5 text-indigo-500"
            aria-hidden="true"
          />
          <input
            id="search-field"
            className="block h-full w-full border-0 py-0 pl-8 pr-0 text-gray-900 placeholder:text-gray-500 focus:ring-2 focus:ring-indigo-500 bg-transparent sm:text-sm font-semibold"
            placeholder="Search pipelines, connectors..."
            type="search"
            name="search"
          />
        </form>
        <div className="flex items-center gap-x-4 lg:gap-x-6">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-green-100 border-2 border-green-500 rounded-full">
            <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-xs font-bold text-green-700">ONLINE</span>
          </div>

          <button
            type="button"
            className="-m-2.5 p-2.5 text-indigo-600 hover:text-indigo-800 hover:bg-indigo-100 rounded-lg transition-all"
          >
            <span className="sr-only">View notifications</span>
            <Bell className="h-6 w-6" aria-hidden="true" />
          </button>

          <div
            className="hidden lg:block lg:h-6 lg:w-px lg:bg-indigo-300"
            aria-hidden="true"
          />

          <div className="relative">
            <button
              type="button"
              className="-m-1.5 flex items-center p-1.5 hover:bg-indigo-100 rounded-lg transition-all"
            >
              <span className="sr-only">Open user menu</span>
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center border-2 border-white shadow-lg">
                <User className="h-5 w-5 text-white" />
              </div>
              <span className="hidden lg:flex lg:items-center">
                <span
                  className="ml-4 text-sm font-bold leading-6 text-gray-900"
                  aria-hidden="true"
                >
                  Admin User
                </span>
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
