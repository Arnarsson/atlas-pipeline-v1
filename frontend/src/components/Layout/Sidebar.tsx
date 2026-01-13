import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  Home,
  Upload,
  Database,
  FileText,
  Shield,
  LayoutDashboard,
  Box,
  GitBranch,
  Search,
  Zap,
  ChevronDown,
  CheckCircle,
  Inbox,
} from 'lucide-react';

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  children?: NavItem[];
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Inbox', href: '/inbox', icon: Inbox },
  { name: 'Upload', href: '/upload', icon: Upload },
  {
    name: 'Connectors',
    href: '/connectors',
    icon: Database,
    children: [
      { name: 'Database', href: '/connectors', icon: Database },
      { name: 'AtlasIntelligence', href: '/atlas-intelligence', icon: Zap },
    ],
  },
  { name: 'Quality', href: '/reports', icon: FileText },
  { name: 'PII', href: '/pii', icon: Shield },
  { name: 'Catalog', href: '/catalog', icon: Search },
  { name: 'Features', href: '/features', icon: Box },
  { name: 'GDPR', href: '/gdpr', icon: Shield },
  { name: 'Lineage', href: '/lineage', icon: GitBranch },
  { name: 'Decisions', href: '/decisions', icon: CheckCircle },
];

export default function Sidebar() {
  const location = useLocation();
  const [expandedItems, setExpandedItems] = useState<string[]>(['Connectors']);

  const toggleExpanded = (name: string) => {
    setExpandedItems((prev) =>
      prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]
    );
  };

  const isChildActive = (item: NavItem): boolean => {
    if (item.children) {
      return item.children.some(
        (child) => location.pathname === child.href
      );
    }
    return false;
  };

  return (
    <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col border-r border-[hsl(var(--border))] bg-[hsl(var(--background))]" data-testid="sidebar">
      <div className="flex grow flex-col gap-y-5 overflow-y-auto px-6 py-4">
        <div className="flex h-14 shrink-0 items-center gap-3">
          <LayoutDashboard className="h-6 w-6 text-[hsl(var(--foreground))]" />
          <span className="text-lg font-semibold text-[hsl(var(--foreground))]">Atlas Pipeline</span>
        </div>
        <nav className="flex flex-1 flex-col" data-testid="main-navigation">
          <ul role="list" className="flex flex-1 flex-col gap-y-1">
            <li>
              <ul role="list" className="space-y-1">
                {navigation.map((item) => (
                  <li key={item.name}>
                    {item.children ? (
                      // Parent item with children
                      <div>
                        <button
                          onClick={() => toggleExpanded(item.name)}
                          data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                          className={`w-full group flex items-center justify-between gap-x-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                            isChildActive(item) || expandedItems.includes(item.name)
                              ? 'bg-[hsl(var(--secondary))] text-[hsl(var(--secondary-foreground))]'
                              : 'text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--secondary)/0.5)]'
                          }`}
                        >
                          <div className="flex items-center gap-x-3">
                            <item.icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                            {item.name}
                          </div>
                          <ChevronDown
                            className={`h-4 w-4 transition-transform ${
                              expandedItems.includes(item.name) ? 'rotate-180' : ''
                            }`}
                          />
                        </button>
                        {expandedItems.includes(item.name) && (
                          <ul className="mt-1 ml-6 space-y-1">
                            {item.children.map((child) => (
                              <li key={child.name}>
                                <NavLink
                                  to={child.href}
                                  data-testid={`nav-${child.name.toLowerCase().replace(/\s+/g, '-')}`}
                                  className={({ isActive }) =>
                                    `group flex gap-x-3 rounded-md px-3 py-1.5 text-sm transition-colors ${
                                      isActive
                                        ? 'text-[hsl(var(--foreground))] font-medium'
                                        : 'text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]'
                                    }`
                                  }
                                >
                                  <child.icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                                  {child.name}
                                </NavLink>
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    ) : (
                      // Regular nav item
                      <NavLink
                        to={item.href}
                        data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                        className={({ isActive }) =>
                          `group flex gap-x-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                            isActive
                              ? 'bg-[hsl(var(--secondary))] text-[hsl(var(--secondary-foreground))]'
                              : 'text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--secondary)/0.5)]'
                          }`
                        }
                      >
                        <item.icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                        {item.name}
                      </NavLink>
                    )}
                  </li>
                ))}
              </ul>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  );
}
