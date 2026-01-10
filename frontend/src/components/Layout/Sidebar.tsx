import { NavLink } from 'react-router-dom';
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
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Upload', href: '/upload', icon: Upload },
  { name: 'Connectors', href: '/connectors', icon: Database },
  { name: 'Quality', href: '/reports', icon: FileText },
  { name: 'PII', href: '/pii', icon: Shield },
  { name: 'Catalog', href: '/catalog', icon: Search },
  { name: 'Features', href: '/features', icon: Box },
  { name: 'GDPR', href: '/gdpr', icon: Shield },
  { name: 'Lineage', href: '/lineage', icon: GitBranch },
];

export default function Sidebar() {
  return (
    <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col border-r-4 border-indigo-600" data-testid="sidebar">
      <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-gradient-to-b from-indigo-900 via-blue-900 to-indigo-800 px-6 pb-4 shadow-2xl">
        <div className="flex h-16 shrink-0 items-center gap-3 border-b-2 border-indigo-700 pb-4 mb-2">
          <LayoutDashboard className="h-8 w-8 text-yellow-400" />
          <span className="text-xl font-bold text-white tracking-wide">Atlas Pipeline</span>
        </div>
        <nav className="flex flex-1 flex-col" data-testid="main-navigation">
          <ul role="list" className="flex flex-1 flex-col gap-y-7">
            <li>
              <ul role="list" className="-mx-2 space-y-2">
                {navigation.map((item) => (
                  <li key={item.name}>
                    <NavLink
                      to={item.href}
                      data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                      className={({ isActive }) =>
                        `group flex gap-x-3 rounded-lg p-3 text-sm leading-6 font-semibold transition-all duration-200 border-2 ${
                          isActive
                            ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-gray-900 border-yellow-300 shadow-lg scale-105'
                            : 'text-blue-100 hover:text-white hover:bg-indigo-700 border-transparent hover:border-blue-500 hover:shadow-md'
                        }`
                      }
                    >
                      <item.icon className="h-6 w-6 shrink-0" aria-hidden="true" />
                      {item.name}
                    </NavLink>
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
