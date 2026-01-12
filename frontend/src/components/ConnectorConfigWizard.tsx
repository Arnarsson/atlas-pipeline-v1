import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  X,
  ChevronRight,
  ChevronLeft,
  Check,
  Database,
  Settings,
  Play,
  AlertCircle,
  Loader2
} from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '@/api/client';

interface ConnectorSpec {
  type: string;
  required?: string[];
  properties: Record<string, {
    type: string;
    description?: string;
    default?: any;
    airbyte_secret?: boolean;
    enum?: string[];
    format?: string;
  }>;
}

interface ConnectorConfigWizardProps {
  connector: {
    id: string;
    name: string;
    category: string;
  };
  onClose: () => void;
  onSuccess?: (sourceId: string) => void;
}

// Fetch connector spec
const getConnectorSpec = async (sourceId: string) => {
  const response = await api.get(`/atlas-intelligence/pyairbyte/connectors/${sourceId}/spec`);
  return response.data;
};

// Configure connector
const configureConnector = async (data: { source_name: string; config: Record<string, any>; streams?: string[] }) => {
  const response = await api.post('/atlas-intelligence/pyairbyte/configure', data);
  return response.data;
};

// Discover streams
const discoverStreams = async (sourceName: string) => {
  const response = await api.get(`/atlas-intelligence/pyairbyte/sources/${sourceName}/streams`);
  return response.data;
};

// Create state for source
const createSourceState = async (data: { source_name: string; source_id: string; streams: string[] }) => {
  const response = await api.post('/atlas-intelligence/state/sources', data);
  return response.data;
};

type WizardStep = 'config' | 'streams' | 'review';

export default function ConnectorConfigWizard({ connector, onClose, onSuccess }: ConnectorConfigWizardProps) {
  const [step, setStep] = useState<WizardStep>('config');
  const [config, setConfig] = useState<Record<string, any>>({});
  const [selectedStreams, setSelectedStreams] = useState<string[]>([]);
  const [sourceId, setSourceId] = useState<string>('');
  const [configError, setConfigError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Fetch spec
  const { data: specData, isLoading: loadingSpec } = useQuery({
    queryKey: ['connector-spec', connector.id],
    queryFn: () => getConnectorSpec(connector.id),
  });

  const spec: ConnectorSpec | undefined = specData?.spec;

  // Configure mutation
  const configureMutation = useMutation({
    mutationFn: configureConnector,
    onSuccess: (data) => {
      if (data.status === 'configured' || data.status === 'simulated') {
        setSourceId(connector.id + '-' + Date.now());
        toast.success('Configuration validated');
        setStep('streams');
      } else if (data.status === 'error') {
        setConfigError(data.error || 'Configuration failed');
        toast.error(data.error || 'Configuration failed');
      }
    },
    onError: (error: any) => {
      setConfigError(error?.response?.data?.detail || 'Configuration failed');
      toast.error('Configuration failed');
    },
  });

  // Discover streams
  const { data: streamsData, isLoading: loadingStreams, refetch: refetchStreams } = useQuery({
    queryKey: ['connector-streams', connector.id],
    queryFn: () => discoverStreams(connector.id),
    enabled: step === 'streams',
  });

  // Create state mutation
  const createStateMutation = useMutation({
    mutationFn: createSourceState,
    onSuccess: (data) => {
      toast.success('Connector configured successfully');
      queryClient.invalidateQueries({ queryKey: ['pyairbyte-connectors'] });
      queryClient.invalidateQueries({ queryKey: ['platform-stats'] });
      onSuccess?.(data.source_id);
      onClose();
    },
    onError: () => {
      toast.error('Failed to save connector state');
    },
  });

  const handleConfigChange = (field: string, value: any) => {
    setConfig(prev => ({ ...prev, [field]: value }));
    setConfigError(null);
  };

  const handleValidateConfig = () => {
    // Check required fields
    const required = spec?.required || [];
    const missing = required.filter(field => !config[field]);

    if (missing.length > 0) {
      setConfigError(`Missing required fields: ${missing.join(', ')}`);
      return;
    }

    configureMutation.mutate({
      source_name: connector.id,
      config,
    });
  };

  const handleStreamToggle = (streamName: string) => {
    setSelectedStreams(prev =>
      prev.includes(streamName)
        ? prev.filter(s => s !== streamName)
        : [...prev, streamName]
    );
  };

  const handleSelectAllStreams = () => {
    const allStreams = streamsData?.streams?.map((s: any) => s.name) || [];
    setSelectedStreams(allStreams);
  };

  const handleFinish = () => {
    createStateMutation.mutate({
      source_name: connector.id,
      source_id: sourceId,
      streams: selectedStreams,
    });
  };

  const renderConfigStep = () => {
    if (loadingSpec) {
      return (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-[hsl(var(--muted-foreground))]" />
        </div>
      );
    }

    if (!spec || !spec.properties) {
      return (
        <div className="text-center py-8">
          <AlertCircle className="w-12 h-12 mx-auto text-yellow-500 mb-4" />
          <p className="text-[hsl(var(--foreground))]">No configuration schema available</p>
          <p className="text-sm text-[hsl(var(--muted-foreground))] mt-2">
            This connector may not require configuration or PyAirbyte is not installed.
          </p>
          <Button className="mt-4" onClick={() => setStep('streams')}>
            Continue Anyway
          </Button>
        </div>
      );
    }

    const required = spec.required || [];

    return (
      <div className="space-y-4">
        {Object.entries(spec.properties).map(([field, fieldSpec]) => (
          <div key={field} className="space-y-1">
            <label className="text-sm font-medium text-[hsl(var(--foreground))]">
              {field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              {required.includes(field) && <span className="text-red-500 ml-1">*</span>}
            </label>
            {fieldSpec.description && (
              <p className="text-xs text-[hsl(var(--muted-foreground))]">{fieldSpec.description}</p>
            )}
            {fieldSpec.enum ? (
              <select
                value={config[field] || ''}
                onChange={(e) => handleConfigChange(field, e.target.value)}
                className="w-full px-3 py-2 border border-[hsl(var(--border))] rounded-md bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
              >
                <option value="">Select...</option>
                {fieldSpec.enum.map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            ) : fieldSpec.type === 'boolean' ? (
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={config[field] || false}
                  onChange={(e) => handleConfigChange(field, e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm text-[hsl(var(--muted-foreground))]">
                  {config[field] ? 'Enabled' : 'Disabled'}
                </span>
              </div>
            ) : fieldSpec.type === 'integer' || fieldSpec.type === 'number' ? (
              <input
                type="number"
                value={config[field] ?? fieldSpec.default ?? ''}
                onChange={(e) => handleConfigChange(field, parseInt(e.target.value) || 0)}
                placeholder={fieldSpec.default?.toString()}
                className="w-full px-3 py-2 border border-[hsl(var(--border))] rounded-md bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
              />
            ) : (
              <input
                type={fieldSpec.airbyte_secret ? 'password' : 'text'}
                value={config[field] || ''}
                onChange={(e) => handleConfigChange(field, e.target.value)}
                placeholder={fieldSpec.default || `Enter ${field}`}
                className="w-full px-3 py-2 border border-[hsl(var(--border))] rounded-md bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
              />
            )}
          </div>
        ))}

        {configError && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
            <p className="text-sm text-red-600">{configError}</p>
          </div>
        )}
      </div>
    );
  };

  const renderStreamsStep = () => {
    if (loadingStreams) {
      return (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-[hsl(var(--muted-foreground))]" />
          <span className="ml-2 text-[hsl(var(--muted-foreground))]">Discovering streams...</span>
        </div>
      );
    }

    const streams = streamsData?.streams || [];

    if (streams.length === 0) {
      return (
        <div className="text-center py-8">
          <Database className="w-12 h-12 mx-auto text-[hsl(var(--muted-foreground))] mb-4" />
          <p className="text-[hsl(var(--foreground))]">No streams discovered</p>
          <p className="text-sm text-[hsl(var(--muted-foreground))] mt-2">
            The connector will sync all available data.
          </p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-[hsl(var(--muted-foreground))]">
            {selectedStreams.length} of {streams.length} streams selected
          </p>
          <Button size="sm" variant="outline" onClick={handleSelectAllStreams}>
            Select All
          </Button>
        </div>

        <div className="max-h-[300px] overflow-y-auto space-y-2">
          {streams.map((stream: any) => (
            <div
              key={stream.name}
              onClick={() => handleStreamToggle(stream.name)}
              className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                selectedStreams.includes(stream.name)
                  ? 'border-[hsl(var(--foreground))] bg-[hsl(var(--secondary))]'
                  : 'border-[hsl(var(--border))] hover:bg-[hsl(var(--secondary))]'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`w-4 h-4 rounded border flex items-center justify-center ${
                    selectedStreams.includes(stream.name)
                      ? 'bg-[hsl(var(--foreground))] border-[hsl(var(--foreground))]'
                      : 'border-[hsl(var(--border))]'
                  }`}>
                    {selectedStreams.includes(stream.name) && (
                      <Check className="w-3 h-3 text-[hsl(var(--background))]" />
                    )}
                  </div>
                  <span className="font-medium text-[hsl(var(--foreground))]">{stream.name}</span>
                </div>
                <div className="flex gap-1">
                  {stream.supported_sync_modes?.map((mode: string) => (
                    <span key={mode} className="px-2 py-0.5 text-xs rounded bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))]">
                      {mode}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderReviewStep = () => {
    return (
      <div className="space-y-4">
        <div className="p-4 bg-[hsl(var(--secondary))] rounded-lg">
          <h4 className="font-medium text-[hsl(var(--foreground))] mb-2">Configuration Summary</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-[hsl(var(--muted-foreground))]">Connector</span>
              <span className="text-[hsl(var(--foreground))]">{connector.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[hsl(var(--muted-foreground))]">Source ID</span>
              <span className="text-[hsl(var(--foreground))] font-mono text-xs">{sourceId}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[hsl(var(--muted-foreground))]">Selected Streams</span>
              <span className="text-[hsl(var(--foreground))]">{selectedStreams.length}</span>
            </div>
          </div>
        </div>

        {selectedStreams.length > 0 && (
          <div className="p-4 border border-[hsl(var(--border))] rounded-lg">
            <h4 className="font-medium text-[hsl(var(--foreground))] mb-2">Streams to Sync</h4>
            <div className="flex flex-wrap gap-2">
              {selectedStreams.map(stream => (
                <span key={stream} className="px-2 py-1 text-xs rounded bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))]">
                  {stream}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
          <div className="flex items-center gap-2">
            <Check className="w-5 h-5 text-green-600" />
            <span className="text-green-600 font-medium">Ready to configure</span>
          </div>
          <p className="text-sm text-[hsl(var(--muted-foreground))] mt-1">
            Click "Finish" to save this connector configuration.
          </p>
        </div>
      </div>
    );
  };

  const steps: { key: WizardStep; label: string }[] = [
    { key: 'config', label: 'Configure' },
    { key: 'streams', label: 'Select Streams' },
    { key: 'review', label: 'Review' },
  ];

  const currentStepIndex = steps.findIndex(s => s.key === step);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-hidden">
        <CardContent className="p-0">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-[hsl(var(--border))]">
            <div className="flex items-center gap-3">
              <Database className="w-6 h-6 text-[hsl(var(--foreground))]" />
              <div>
                <h2 className="font-semibold text-[hsl(var(--foreground))]">Configure {connector.name}</h2>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">{connector.id}</p>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>

          {/* Progress Steps */}
          <div className="flex items-center justify-center p-4 border-b border-[hsl(var(--border))]">
            {steps.map((s, i) => (
              <div key={s.key} className="flex items-center">
                <div className={`flex items-center gap-2 px-3 py-1 rounded-full ${
                  i <= currentStepIndex
                    ? 'bg-[hsl(var(--foreground))] text-[hsl(var(--background))]'
                    : 'bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))]'
                }`}>
                  <span className="text-sm font-medium">{i + 1}</span>
                  <span className="text-sm">{s.label}</span>
                </div>
                {i < steps.length - 1 && (
                  <ChevronRight className="w-4 h-4 mx-2 text-[hsl(var(--muted-foreground))]" />
                )}
              </div>
            ))}
          </div>

          {/* Content */}
          <div className="p-4 overflow-y-auto max-h-[50vh]">
            {step === 'config' && renderConfigStep()}
            {step === 'streams' && renderStreamsStep()}
            {step === 'review' && renderReviewStep()}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-4 border-t border-[hsl(var(--border))]">
            <Button
              variant="outline"
              onClick={() => {
                if (step === 'config') onClose();
                else if (step === 'streams') setStep('config');
                else setStep('streams');
              }}
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              {step === 'config' ? 'Cancel' : 'Back'}
            </Button>

            {step === 'config' && (
              <Button
                onClick={handleValidateConfig}
                disabled={configureMutation.isPending}
              >
                {configureMutation.isPending ? (
                  <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                ) : (
                  <Settings className="w-4 h-4 mr-1" />
                )}
                Validate & Continue
              </Button>
            )}

            {step === 'streams' && (
              <Button onClick={() => setStep('review')}>
                Continue
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            )}

            {step === 'review' && (
              <Button
                onClick={handleFinish}
                disabled={createStateMutation.isPending}
              >
                {createStateMutation.isPending ? (
                  <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                ) : (
                  <Play className="w-4 h-4 mr-1" />
                )}
                Finish
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
