import { Bell, Search, User, Moon, Sun } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';

export default function Header() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    // Check for saved preference or system preference
    const saved = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (saved === 'dark' || (!saved && prefersDark)) {
      setIsDark(true);
      document.documentElement.classList.add('dark');
    }
  }, []);

  const toggleDarkMode = () => {
    setIsDark(!isDark);
    if (isDark) {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    } else {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    }
  };

  return (
    <div className="sticky top-0 z-40 flex h-14 shrink-0 items-center gap-x-4 border-b border-[hsl(var(--border))] bg-[hsl(var(--background))] px-4 sm:gap-x-6 sm:px-6 lg:px-8">
      <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
        <form className="relative flex flex-1" action="#" method="GET">
          <label htmlFor="search-field" className="sr-only">
            Search
          </label>
          <Search
            className="pointer-events-none absolute inset-y-0 left-0 h-full w-4 text-[hsl(var(--muted-foreground))]"
            aria-hidden="true"
          />
          <input
            id="search-field"
            className="block h-full w-full border-0 py-0 pl-7 pr-0 text-[hsl(var(--foreground))] placeholder:text-[hsl(var(--muted-foreground))] focus:ring-0 bg-transparent text-sm"
            placeholder="Search..."
            type="search"
            name="search"
          />
        </form>
        <div className="flex items-center gap-x-2 lg:gap-x-4">
          <div className="hidden sm:flex items-center gap-1.5 px-2 py-1 rounded-full bg-green-500/10 text-green-600">
            <div className="h-1.5 w-1.5 bg-green-500 rounded-full"></div>
            <span className="text-xs font-medium">Online</span>
          </div>

          <Button
            variant="ghost"
            size="icon"
            onClick={toggleDarkMode}
            className="h-8 w-8"
          >
            {isDark ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
            <span className="sr-only">Toggle dark mode</span>
          </Button>

          <Button variant="ghost" size="icon" className="h-8 w-8">
            <Bell className="h-4 w-4" />
            <span className="sr-only">View notifications</span>
          </Button>

          <div
            className="hidden lg:block lg:h-4 lg:w-px bg-[hsl(var(--border))]"
            aria-hidden="true"
          />

          <button
            type="button"
            className="flex items-center gap-2 rounded-md px-2 py-1 hover:bg-[hsl(var(--secondary))] transition-colors"
          >
            <div className="h-7 w-7 rounded-full bg-[hsl(var(--secondary))] flex items-center justify-center">
              <User className="h-4 w-4 text-[hsl(var(--secondary-foreground))]" />
            </div>
            <span className="hidden lg:block text-sm font-medium text-[hsl(var(--foreground))]">
              Admin
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
