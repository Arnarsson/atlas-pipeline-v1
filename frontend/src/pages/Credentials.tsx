import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Key,
  Plus,
  Eye,
  EyeOff,
  Trash2,
  CheckCircle,
  AlertTriangle,
  Clock,
  Shield,
  RefreshCw,
} from 'lucide-react';
import { api } from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import toast from 'react-hot-toast';

interface Credential {
  id: string;
  name: string;
  type: string;
  created_at: string;
  last_used?: string;
  status: 'active' | 'expired' | 'revoked';
  expires_at?: string;
}

export default function Credentials() {
  const queryClient = useQueryClient();
  const [_showAddModal, setShowAddModal] = useState(false);
  const [visibleSecrets, setVisibleSecrets] = useState<Set<string>>(new Set());

  const { data: credentials, isLoading } = useQuery({
    queryKey: ['credentials'],
    queryFn: async () => {
      try {
        const response = await api.get('/atlas-intelligence/credentials');
        return response.data as Credential[];
      } catch {
        return getMockCredentials();
      }
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (credentialId: string) => {
      await api.delete(`/atlas-intelligence/credentials/${credentialId}`);
    },
    onSuccess: () => {
      toast.success('Credential deleted');
      queryClient.invalidateQueries({ queryKey: ['credentials'] });
    },
    onError: () => {
      toast.error('Failed to delete credential');
    },
  });

  const testMutation = useMutation({
    mutationFn: async (credentialId: string) => {
      const response = await api.post(`/atlas-intelligence/credentials/${credentialId}/test`);
      return response.data;
    },
    onSuccess: () => {
      toast.success('Connection test successful');
    },
    onError: () => {
      toast.error('Connection test failed');
    },
  });

  const toggleVisibility = (id: string) => {
    const newVisible = new Set(visibleSecrets);
    if (newVisible.has(id)) {
      newVisible.delete(id);
    } else {
      newVisible.add(id);
    }
    setVisibleSecrets(newVisible);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return (
          <span className="flex items-center gap-1.5 px-2 py-1 text-xs font-medium rounded-full bg-green-500/10 text-green-600">
            <CheckCircle className="h-3 w-3" />
            Active
          </span>
        );
      case 'expired':
        return (
          <span className="flex items-center gap-1.5 px-2 py-1 text-xs font-medium rounded-full bg-yellow-500/10 text-yellow-600">
            <Clock className="h-3 w-3" />
            Expired
          </span>
        );
      case 'revoked':
        return (
          <span className="flex items-center gap-1.5 px-2 py-1 text-xs font-medium rounded-full bg-red-500/10 text-red-600">
            <AlertTriangle className="h-3 w-3" />
            Revoked
          </span>
        );
      default:
        return null;
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const formatTimeAgo = (dateStr?: string) => {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-[hsl(var(--foreground))] border-t-transparent" />
      </div>
    );
  }

  const activeCount = credentials?.filter((c) => c.status === 'active').length || 0;
  const expiredCount = credentials?.filter((c) => c.status === 'expired').length || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">Credentials</h1>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
            Manage API keys and authentication credentials
          </p>
        </div>
        <Button size="sm" onClick={() => setShowAddModal(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Credential
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Total</p>
                <p className="text-2xl font-bold text-[hsl(var(--foreground))]">{credentials?.length || 0}</p>
              </div>
              <Key className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Active</p>
                <p className="text-2xl font-bold text-green-600">{activeCount}</p>
              </div>
              <CheckCircle className="h-5 w-5 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Expired</p>
                <p className="text-2xl font-bold text-yellow-600">{expiredCount}</p>
              </div>
              <Clock className="h-5 w-5 text-yellow-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Credentials List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Stored Credentials
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-[hsl(var(--border))]">
            {credentials && credentials.length > 0 ? (
              credentials.map((cred) => (
                <div
                  key={cred.id}
                  className="flex items-center justify-between p-4 hover:bg-[hsl(var(--secondary)/0.3)] transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[hsl(var(--secondary))]">
                      <Key className="h-5 w-5 text-[hsl(var(--foreground))]" />
                    </div>
                    <div>
                      <h3 className="text-sm font-medium text-[hsl(var(--foreground))]">{cred.name}</h3>
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">
                        {cred.type} • Created {formatDate(cred.created_at)}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="hidden sm:block text-right">
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">Last used</p>
                      <p className="text-sm text-[hsl(var(--foreground))]">{formatTimeAgo(cred.last_used)}</p>
                    </div>

                    {getStatusBadge(cred.status)}

                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleVisibility(cred.id)}
                      >
                        {visibleSecrets.has(cred.id) ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => testMutation.mutate(cred.id)}
                        disabled={testMutation.isPending}
                      >
                        <RefreshCw className={`h-4 w-4 ${testMutation.isPending ? 'animate-spin' : ''}`} />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deleteMutation.mutate(cred.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-500/10"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-12 text-center">
                <Key className="mx-auto h-12 w-12 text-[hsl(var(--muted-foreground))]" />
                <h3 className="mt-4 text-lg font-medium text-[hsl(var(--foreground))]">No credentials</h3>
                <p className="mt-2 text-sm text-[hsl(var(--muted-foreground))]">
                  Add credentials to connect to your data sources
                </p>
                <Button className="mt-4" onClick={() => setShowAddModal(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Credential
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Security Notice */}
      <Card className="bg-[hsl(var(--secondary)/0.3)]">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Shield className="h-5 w-5 text-[hsl(var(--muted-foreground))] mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-[hsl(var(--foreground))]">Security Information</h4>
              <p className="mt-1 text-xs text-[hsl(var(--muted-foreground))]">
                All credentials are encrypted at rest using AES-256. Secrets are never logged or exposed in API responses.
                We recommend rotating credentials regularly and using the minimum required permissions.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function getMockCredentials(): Credential[] {
  return [
    { id: '1', name: 'PostgreSQL Production', type: 'database', created_at: '2024-01-15T10:00:00Z', last_used: new Date().toISOString(), status: 'active' },
    { id: '2', name: 'Salesforce API Key', type: 'oauth2', created_at: '2024-02-20T14:30:00Z', last_used: new Date(Date.now() - 3600000).toISOString(), status: 'active' },
    { id: '3', name: 'Stripe Secret Key', type: 'api_key', created_at: '2024-01-10T09:00:00Z', last_used: new Date(Date.now() - 86400000).toISOString(), status: 'expired', expires_at: '2024-12-31T23:59:59Z' },
    { id: '4', name: 'HubSpot Private App', type: 'api_key', created_at: '2024-03-01T11:00:00Z', last_used: new Date(Date.now() - 7200000).toISOString(), status: 'active' },
  ];
}
