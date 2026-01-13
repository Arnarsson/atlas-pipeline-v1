import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  Home,
  Database,
  FileText,
  Shield,
  Box,
  GitBranch,
  Search,
  Zap,
  ChevronDown,
  ChevronRight,
  CheckCircle,
  Activity,
  Clock,
  FileCheck,
  Key,
  Play,
  BarChart3,
  Scale,
  Users,
  Layers,
} from 'lucide-react';

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

interface NavGroup {
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  items: NavItem[];
  defaultExpanded?: boolean;
}

const navGroups: NavGroup[] = [
  {
    name: 'SOURCES',
    icon: Database,
    defaultExpanded: true,
    items: [
      { name: 'Connections', href: '/connections', icon: Zap },
      { name: 'Catalog', href: '/sources', icon: Search, badge: '300+' },
      { name: 'Credentials', href: '/credentials', icon: Key },
    ],
  },
  {
    name: 'SYNCS',
    icon: Activity,
    defaultExpanded: true,
    items: [
      { name: 'Jobs', href: '/sync-jobs', icon: Play },
      { name: 'Schedules', href: '/schedules', icon: Clock },
      { name: 'Health', href: '/health', icon: BarChart3 },
    ],
  },
  {
    name: 'DATA',
    icon: Layers,
    defaultExpanded: true,
    items: [
      { name: 'Datasets', href: '/catalog', icon: Box },
      { name: 'Quality', href: '/reports', icon: FileCheck },
      { name: 'PII', href: '/pii', icon: Shield },
      { name: 'Lineage', href: '/lineage', icon: GitBranch },
      { name: 'Features', href: '/features', icon: FileText },
      { name: 'KPI', href: '/kpi', icon: BarChart3 },
    ],
  },
  {
    name: 'GOVERNANCE',
    icon: Scale,
    defaultExpanded: false,
    items: [
      { name: 'GDPR', href: '/gdpr', icon: Shield },
      { name: 'Decisions', href: '/decisions', icon: CheckCircle },
      { name: 'RBAC', href: '/rbac', icon: Users },
    ],
  },
];

export default function Sidebar() {
  const location = useLocation();
  const [expandedGroups, setExpandedGroups] = useState<string[]>(
    navGroups.filter(g => g.defaultExpanded).map(g => g.name)
  );

  const toggleGroup = (name: string) => {
    setExpandedGroups((prev) =>
      prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]
    );
  };

  const isGroupActive = (group: NavGroup): boolean => {
    return group.items.some((item) => location.pathname === item.href);
  };

  return (
    <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col border-r border-[hsl(var(--border))] bg-[hsl(var(--background))]" data-testid="sidebar">
      <div className="flex grow flex-col overflow-y-auto">
        {/* Logo */}
        <div className="flex h-14 shrink-0 items-center gap-3 px-6 border-b border-[hsl(var(--border))]">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-[hsl(var(--foreground))]">
            <Zap className="h-4 w-4 text-[hsl(var(--background))]" />
          </div>
          <span className="text-lg font-semibold text-[hsl(var(--foreground))]">Atlas</span>
        </div>

        {/* Home link */}
        <div className="px-3 py-3">
          <NavLink
            to="/"
            data-testid="nav-home"
            className={({ isActive }) =>
              `group flex items-center gap-x-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${
                isActive
                  ? 'bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))]'
                  : 'text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--secondary)/0.5)]'
              }`
            }
          >
            <Home className="h-5 w-5 shrink-0" aria-hidden="true" />
            Home
          </NavLink>
        </div>

        {/* Navigation Groups */}
        <nav className="flex-1 px-3 pb-4" data-testid="main-navigation">
          <div className="space-y-1">
            {navGroups.map((group) => {
              const isExpanded = expandedGroups.includes(group.name);
              const isActive = isGroupActive(group);

              return (
                <div key={group.name} className="py-1">
                  {/* Group Header */}
                  <button
                    onClick={() => toggleGroup(group.name)}
                    data-testid={`nav-group-${group.name.toLowerCase()}`}
                    className={`w-full group flex items-center justify-between px-3 py-2 text-xs font-semibold uppercase tracking-wider transition-colors ${
                      isActive
                        ? 'text-[hsl(var(--foreground))]'
                        : 'text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]'
                    }`}
                  >
                    <div className="flex items-center gap-x-2">
                      <group.icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                      {group.name}
                    </div>
                    {isExpanded ? (
                      <ChevronDown className="h-3.5 w-3.5" />
                    ) : (
                      <ChevronRight className="h-3.5 w-3.5" />
                    )}
                  </button>

                  {/* Group Items */}
                  {isExpanded && (
                    <ul className="mt-1 space-y-0.5">
                      {group.items.map((item) => (
                        <li key={item.name}>
                          <NavLink
                            to={item.href}
                            data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                            className={({ isActive }) =>
                              `group flex items-center justify-between gap-x-3 rounded-lg px-3 py-2 text-sm transition-all ml-2 ${
                                isActive
                                  ? 'bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))] font-medium'
                                  : 'text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--secondary)/0.5)]'
                              }`
                            }
                          >
                            <div className="flex items-center gap-x-3">
                              <item.icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                              {item.name}
                            </div>
                            {item.badge && (
                              <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-[hsl(var(--muted))] text-[hsl(var(--muted-foreground))]">
                                {item.badge}
                              </span>
                            )}
                          </NavLink>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              );
            })}
          </div>
        </nav>

        {/* Bottom section - Quick Stats */}
        <div className="border-t border-[hsl(var(--border))] p-4">
          <div className="rounded-lg bg-[hsl(var(--secondary)/0.5)] p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-[hsl(var(--muted-foreground))]">Sync Status</span>
              <span className="flex h-2 w-2 rounded-full bg-green-500"></span>
            </div>
            <div className="text-sm font-semibold text-[hsl(var(--foreground))]">All systems healthy</div>
            <div className="text-xs text-[hsl(var(--muted-foreground))] mt-1">Last sync: 2 min ago</div>
          </div>
        </div>
      </div>
    </div>
  );
}
