import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  X,
  Database,
  Table,
  ChevronRight,
  ChevronDown,
  RefreshCw,
  Copy,
  Check
} from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '@/api/client';

interface Stream {
  name: string;
  supported_sync_modes: string[];
  source_defined_cursor?: boolean;
}

interface SchemaBrowserProps {
  sourceName: string;
  sourceDisplayName: string;
  onClose: () => void;
}

const getStreams = async (sourceName: string) => {
  const response = await api.get(`/atlas-intelligence/pyairbyte/sources/${sourceName}/streams`);
  return response.data;
};

const getSpec = async (sourceName: string) => {
  const response = await api.get(`/atlas-intelligence/pyairbyte/connectors/${sourceName}/spec`);
  return response.data;
};

export default function SchemaBrowser({ sourceName, sourceDisplayName, onClose }: SchemaBrowserProps) {
  const [expandedStreams, setExpandedStreams] = useState<Set<string>>(new Set());
  const [copiedStream, setCopiedStream] = useState<string | null>(null);

  const { data: streamsData, isLoading: loadingStreams, refetch } = useQuery({
    queryKey: ['schema-streams', sourceName],
    queryFn: () => getStreams(sourceName),
  });

  const { data: specData } = useQuery({
    queryKey: ['schema-spec', sourceName],
    queryFn: () => getSpec(sourceName),
  });

  const streams: Stream[] = streamsData?.streams || [];
  const spec = specData?.spec;

  const toggleStream = (streamName: string) => {
    setExpandedStreams(prev => {
      const newSet = new Set(prev);
      if (newSet.has(streamName)) {
        newSet.delete(streamName);
      } else {
        newSet.add(streamName);
      }
      return newSet;
    });
  };

  const copyStreamName = async (streamName: string) => {
    try {
      await navigator.clipboard.writeText(streamName);
      setCopiedStream(streamName);
      toast.success('Stream name copied');
      setTimeout(() => setCopiedStream(null), 2000);
    } catch {
      toast.error('Failed to copy');
    }
  };

  const getSyncModeColor = (mode: string) => {
    switch (mode) {
      case 'incremental':
        return 'bg-green-500/10 text-green-600';
      case 'full_refresh':
        return 'bg-blue-500/10 text-blue-600';
      default:
        return 'bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))]';
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-3xl max-h-[85vh] overflow-hidden">
        <CardContent className="p-0">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-[hsl(var(--border))]">
            <div className="flex items-center gap-3">
              <Database className="w-6 h-6 text-blue-500" />
              <div>
                <h2 className="font-semibold text-[hsl(var(--foreground))]">Schema Browser</h2>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">{sourceDisplayName} ({sourceName})</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => refetch()}>
                <RefreshCw className="w-4 h-4" />
              </Button>
              <Button variant="ghost" size="sm" onClick={onClose}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Summary */}
          <div className="p-4 bg-[hsl(var(--secondary))] border-b border-[hsl(var(--border))]">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">{streams.length}</p>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Streams</p>
              </div>
              <div>
                <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">
                  {streams.filter(s => s.supported_sync_modes?.includes('incremental')).length}
                </p>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Incremental</p>
              </div>
              <div>
                <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">
                  {spec?.properties ? Object.keys(spec.properties).length : 0}
                </p>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Config Fields</p>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="overflow-y-auto max-h-[50vh]">
            {loadingStreams ? (
              <div className="flex items-center justify-center py-12">
                <RefreshCw className="w-8 h-8 animate-spin text-[hsl(var(--muted-foreground))]" />
              </div>
            ) : streams.length === 0 ? (
              <div className="text-center py-12">
                <Table className="w-12 h-12 mx-auto text-[hsl(var(--muted-foreground))] mb-4" />
                <p className="text-[hsl(var(--foreground))]">No streams available</p>
                <p className="text-sm text-[hsl(var(--muted-foreground))] mt-2">
                  Configure the connector to discover streams
                </p>
              </div>
            ) : (
              <div className="divide-y divide-[hsl(var(--border))]">
                {streams.map((stream) => (
                  <div key={stream.name} className="group">
                    <div
                      className="flex items-center justify-between p-4 hover:bg-[hsl(var(--secondary))] cursor-pointer"
                      onClick={() => toggleStream(stream.name)}
                    >
                      <div className="flex items-center gap-3">
                        {expandedStreams.has(stream.name) ? (
                          <ChevronDown className="w-4 h-4 text-[hsl(var(--muted-foreground))]" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-[hsl(var(--muted-foreground))]" />
                        )}
                        <Table className="w-5 h-5 text-[hsl(var(--muted-foreground))]" />
                        <span className="font-medium text-[hsl(var(--foreground))]">{stream.name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {stream.supported_sync_modes?.map((mode) => (
                          <span key={mode} className={`px-2 py-0.5 text-xs rounded ${getSyncModeColor(mode)}`}>
                            {mode.replace('_', ' ')}
                          </span>
                        ))}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={(e) => {
                            e.stopPropagation();
                            copyStreamName(stream.name);
                          }}
                        >
                          {copiedStream === stream.name ? (
                            <Check className="w-4 h-4 text-green-500" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </Button>
                      </div>
                    </div>

                    {expandedStreams.has(stream.name) && (
                      <div className="px-12 pb-4 bg-[hsl(var(--secondary))]">
                        <div className="text-sm space-y-2">
                          <div className="flex justify-between py-1 border-b border-[hsl(var(--border))]">
                            <span className="text-[hsl(var(--muted-foreground))]">Stream Name</span>
                            <span className="font-mono text-[hsl(var(--foreground))]">{stream.name}</span>
                          </div>
                          <div className="flex justify-between py-1 border-b border-[hsl(var(--border))]">
                            <span className="text-[hsl(var(--muted-foreground))]">Sync Modes</span>
                            <span className="text-[hsl(var(--foreground))]">
                              {stream.supported_sync_modes?.join(', ') || 'N/A'}
                            </span>
                          </div>
                          <div className="flex justify-between py-1 border-b border-[hsl(var(--border))]">
                            <span className="text-[hsl(var(--muted-foreground))]">Cursor Support</span>
                            <span className={stream.source_defined_cursor ? 'text-green-600' : 'text-[hsl(var(--muted-foreground))]'}>
                              {stream.source_defined_cursor ? 'Yes' : 'No'}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-4 border-t border-[hsl(var(--border))] bg-[hsl(var(--background))]">
            <p className="text-sm text-[hsl(var(--muted-foreground))]">
              {streams.length} streams available
            </p>
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
