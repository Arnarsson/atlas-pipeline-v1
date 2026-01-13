import { Users, Shield, Lock, Key } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const ROLES = [
  { name: 'Admin', users: 2, permissions: 'Full access to all resources' },
  { name: 'Data Engineer', users: 5, permissions: 'Create/manage connections, run syncs' },
  { name: 'Analyst', users: 12, permissions: 'View data, run queries, create reports' },
  { name: 'Viewer', users: 8, permissions: 'Read-only access to dashboards' },
];

export default function RBAC() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">Access Control</h1>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
            Manage roles and permissions for your team
          </p>
        </div>
        <Button size="sm">
          <Users className="h-4 w-4 mr-2" />
          Invite User
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Total Users</p>
                <p className="text-2xl font-bold text-[hsl(var(--foreground))]">27</p>
              </div>
              <Users className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Roles</p>
                <p className="text-2xl font-bold text-[hsl(var(--foreground))]">4</p>
              </div>
              <Shield className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Permissions</p>
                <p className="text-2xl font-bold text-[hsl(var(--foreground))]">14</p>
              </div>
              <Lock className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">API Keys</p>
                <p className="text-2xl font-bold text-[hsl(var(--foreground))]">8</p>
              </div>
              <Key className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Roles */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">Roles</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-[hsl(var(--border))]">
            {ROLES.map((role) => (
              <div key={role.name} className="flex items-center justify-between p-4 hover:bg-[hsl(var(--secondary)/0.3)] transition-colors">
                <div className="flex items-center gap-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[hsl(var(--secondary))]">
                    <Shield className="h-5 w-5 text-[hsl(var(--foreground))]" />
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-[hsl(var(--foreground))]">{role.name}</h3>
                    <p className="text-xs text-[hsl(var(--muted-foreground))]">{role.permissions}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-[hsl(var(--muted-foreground))]">{role.users} users</span>
                  <Button variant="ghost" size="sm">Edit</Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Info Banner */}
      <Card className="bg-[hsl(var(--secondary)/0.3)]">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Shield className="h-5 w-5 text-[hsl(var(--muted-foreground))] mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-[hsl(var(--foreground))]">Enterprise Feature</h4>
              <p className="mt-1 text-xs text-[hsl(var(--muted-foreground))]">
                Advanced RBAC with custom roles, SSO integration, and audit logging is available on the Enterprise plan.
                Contact sales for more information.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
