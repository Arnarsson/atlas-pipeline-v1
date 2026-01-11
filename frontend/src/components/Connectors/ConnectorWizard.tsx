import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { createConnector, updateConnector, testConnection } from '@/api/client';
import { Connector, ConnectorFormData } from '@/types';
import { X, ChevronRight, ChevronLeft, Check, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import CronBuilder from './CronBuilder';

interface Props {
  onClose: () => void;
  connector?: Connector | null;
  onSuccess: () => void;
}

type Step = 1 | 2 | 3 | 4 | 5;

export default function ConnectorWizard({ onClose, connector, onSuccess }: Props) {
  const [step, setStep] = useState<Step>(1);
  const [formData, setFormData] = useState<ConnectorFormData>({
    name: connector?.name || '',
    type: connector?.type || 'postgresql',
    config: connector?.config || {},
    schedule: connector?.schedule || '',
  });
  const [draftConnectorId, setDraftConnectorId] = useState<string | null>(
    connector?.id || null
  );
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  const createMutation = useMutation({
    mutationFn: createConnector,
    onSuccess: () => {
      toast.success('Connector created successfully');
      onSuccess();
    },
    onError: () => {
      toast.error('Failed to create connector');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ConnectorFormData }) =>
      updateConnector(id, data),
    onSuccess: () => {
      toast.success('Connector updated successfully');
      onSuccess();
    },
    onError: () => {
      toast.error('Failed to update connector');
    },
  });

  const handleTestConnection = async () => {
    setIsTesting(true);
    try {
      let connectorId = draftConnectorId;

      if (!connectorId) {
        const created = await createConnector(formData);
        connectorId = created.id;
        setDraftConnectorId(connectorId);
      }

      const result = await testConnection(connectorId);
      setTestResult(result);
      if (result.success) {
        toast.success('Connection test successful');
      } else {
        toast.error('Connection test failed');
      }
    } catch (error) {
      setTestResult({ success: false, message: 'Connection test failed' });
      toast.error('Connection test failed');
    } finally {
      setIsTesting(false);
    }
  };

  const handleSubmit = () => {
    if (connector || draftConnectorId) {
      updateMutation.mutate({ id: (connector?.id || draftConnectorId) as string, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const canProceed = () => {
    switch (step) {
      case 1:
        return formData.type !== undefined;
      case 2:
        if (formData.type === 'postgresql' || formData.type === 'mysql') {
          return formData.config.host && formData.config.database && formData.config.username;
        }
        if (formData.type === 'rest_api') {
          return formData.config.url;
        }
        return true;
      case 3:
        return true; // Schedule is optional
      case 4:
        return testResult?.success || false;
      default:
        return true;
    }
  };

  const steps = [
    { number: 1, title: 'Type', description: 'Select connector type' },
    { number: 2, title: 'Config', description: 'Configure connection' },
    { number: 3, title: 'Schedule', description: 'Set sync schedule' },
    { number: 4, title: 'Test', description: 'Test connection' },
    { number: 5, title: 'Review', description: 'Review and create' },
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" data-testid="connector-wizard">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {connector ? 'Edit Connector' : 'Create Connector'}
            </h2>
            <p className="text-sm text-gray-600 mt-1">Step {step} of 5</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600" data-testid="close-wizard-btn">
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="px-6 py-4 bg-gray-50">
          <div className="flex items-center justify-between">
            {steps.map((s, idx) => (
              <div key={s.number} className="flex items-center flex-1">
                <div
                  className={`flex items-center justify-center w-8 h-8 rounded-full ${
                    step >= s.number
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-600'
                  }`}
                >
                  {step > s.number ? <Check className="w-5 h-5" /> : s.number}
                </div>
                <div className="ml-2 flex-1">
                  <p className={`text-xs font-medium ${step >= s.number ? 'text-blue-600' : 'text-gray-600'}`}>
                    {s.title}
                  </p>
                </div>
                {idx < steps.length - 1 && (
                  <ChevronRight className="w-4 h-4 text-gray-400 mx-2" />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-250px)]">
          {/* Step 1: Type Selection */}
          {step === 1 && (
            <div className="space-y-4" data-testid="wizard-step-type">
              <h3 className="text-lg font-medium text-gray-900">Select Connector Type</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4" data-testid="connector-types">
                {[
                  { type: 'postgresql', icon: '🐘', label: 'PostgreSQL', desc: 'PostgreSQL database' },
                  { type: 'mysql', icon: '🐬', label: 'MySQL', desc: 'MySQL database' },
                  { type: 'rest_api', icon: '🌐', label: 'REST API', desc: 'HTTP REST API' },
                ].map((option) => (
                  <button
                    key={option.type}
                    data-testid={`connector-type-${option.type}`}
                    onClick={() => setFormData({ ...formData, type: option.type as any })}
                    className={`p-6 border-2 rounded-lg text-center hover:border-blue-500 transition-colors ${
                      formData.type === option.type ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                    }`}
                  >
                    <div className="text-4xl mb-2">{option.icon}</div>
                    <h4 className="font-medium text-gray-900">{option.label}</h4>
                    <p className="text-sm text-gray-600 mt-1">{option.desc}</p>
                  </button>
                ))}
              </div>
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Connector Name
                </label>
                <input
                  type="text"
                  data-testid="connector-name-input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="My Data Source"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          )}

          {/* Step 2: Configuration */}
          {step === 2 && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Configure Connection</h3>

              {(formData.type === 'postgresql' || formData.type === 'mysql') && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Host</label>
                    <input
                      type="text"
                      value={formData.config.host || ''}
                      onChange={(e) => setFormData({ ...formData, config: { ...formData.config, host: e.target.value } })}
                      placeholder="localhost"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Port</label>
                    <input
                      type="number"
                      value={formData.config.port || (formData.type === 'postgresql' ? 5432 : 3306)}
                      onChange={(e) => setFormData({ ...formData, config: { ...formData.config, port: Number(e.target.value) } })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Database</label>
                    <input
                      type="text"
                      value={formData.config.database || ''}
                      onChange={(e) => setFormData({ ...formData, config: { ...formData.config, database: e.target.value } })}
                      placeholder="my_database"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                    <input
                      type="text"
                      value={formData.config.username || ''}
                      onChange={(e) => setFormData({ ...formData, config: { ...formData.config, username: e.target.value } })}
                      placeholder="user"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                    <input
                      type="password"
                      value={formData.config.password || ''}
                      onChange={(e) => setFormData({ ...formData, config: { ...formData.config, password: e.target.value } })}
                      placeholder="••••••••"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Query (Optional)</label>
                    <textarea
                      value={formData.config.query || ''}
                      onChange={(e) => setFormData({ ...formData, config: { ...formData.config, query: e.target.value } })}
                      placeholder="SELECT * FROM table"
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
              )}

              {formData.type === 'rest_api' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Base URL</label>
                    <input
                      type="url"
                      value={formData.config.url || ''}
                      onChange={(e) => setFormData({ ...formData, config: { ...formData.config, url: e.target.value } })}
                      placeholder="https://api.example.com"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Headers (JSON)
                    </label>
                    <textarea
                      value={formData.config.headers ? JSON.stringify(formData.config.headers, null, 2) : ''}
                      onChange={(e) => {
                        try {
                          const headers = JSON.parse(e.target.value);
                          setFormData({ ...formData, config: { ...formData.config, headers } });
                        } catch (error) {
                          // Invalid JSON, ignore
                        }
                      }}
                      placeholder='{"Authorization": "Bearer token"}'
                      rows={4}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 3: Schedule */}
          {step === 3 && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Set Sync Schedule</h3>
              <CronBuilder
                value={formData.schedule || ''}
                onChange={(schedule) => setFormData({ ...formData, schedule })}
              />
            </div>
          )}

          {/* Step 4: Test Connection */}
          {step === 4 && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Test Connection</h3>
              <div className="bg-gray-50 rounded-lg p-6 text-center">
                {!testResult ? (
                  <div>
                    <p className="text-gray-600 mb-4">
                      Test your connection to ensure it's configured correctly
                    </p>
                    <button
                      onClick={handleTestConnection}
                      disabled={isTesting}
                      className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                    >
                      {isTesting ? (
                        <>
                          <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                          Testing...
                        </>
                      ) : (
                        'Test Connection'
                      )}
                    </button>
                  </div>
                ) : (
                  <div>
                    {testResult.success ? (
                      <div className="text-green-600">
                        <Check className="w-16 h-16 mx-auto mb-4" />
                        <h4 className="text-lg font-medium mb-2">Connection Successful!</h4>
                        <p className="text-sm">{testResult.message}</p>
                      </div>
                    ) : (
                      <div className="text-red-600">
                        <X className="w-16 h-16 mx-auto mb-4" />
                        <h4 className="text-lg font-medium mb-2">Connection Failed</h4>
                        <p className="text-sm">{testResult.message}</p>
                        <button
                          onClick={() => {
                            setTestResult(null);
                            setStep(2);
                          }}
                          className="mt-4 text-blue-600 hover:text-blue-800"
                        >
                          Go back and fix configuration
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Step 5: Review */}
          {step === 5 && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Review Configuration</h3>
              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                <div>
                  <p className="text-sm text-gray-600">Name</p>
                  <p className="font-medium">{formData.name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Type</p>
                  <p className="font-medium capitalize">{formData.type.replace('_', ' ')}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Schedule</p>
                  <p className="font-medium">{formData.schedule || 'Manual'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Configuration</p>
                  <pre className="mt-1 text-sm bg-white p-2 rounded border border-gray-200 overflow-x-auto">
                    {JSON.stringify(formData.config, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200">
          <button
            onClick={() => step > 1 ? setStep((step - 1) as Step) : onClose()}
            className="px-4 py-2 text-gray-700 hover:text-gray-900"
          >
            <ChevronLeft className="w-5 h-5 inline mr-1" />
            {step === 1 ? 'Cancel' : 'Previous'}
          </button>
          <button
            onClick={() => {
              if (step < 5) {
                setStep((step + 1) as Step);
              } else {
                handleSubmit();
              }
            }}
            disabled={!canProceed() || createMutation.isPending || updateMutation.isPending}
            className="inline-flex items-center px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {step === 5 ? (
              createMutation.isPending || updateMutation.isPending ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                connector || draftConnectorId ? 'Save Connector' : 'Create Connector'
              )
            ) : (
              <>
                Next
                <ChevronRight className="w-5 h-5 ml-1" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
