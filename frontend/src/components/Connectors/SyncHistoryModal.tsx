import { useQuery } from '@tanstack/react-query';
import { getSyncHistory } from '@/api/client';
import { X, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';

interface Props {
  connectorId: string;
  onClose: () => void;
}

export default function SyncHistoryModal({ connectorId, onClose }: Props) {
  const { data: history = [], isLoading } = useQuery({
    queryKey: ['syncHistory', connectorId],
    queryFn: () => getSyncHistory(connectorId),
  });

  const getStatusIcon = (status: 'running' | 'completed' | 'failed') => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'running':
        return <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />;
    }
  };

  const getStatusBadge = (status: 'running' | 'completed' | 'failed') => {
    const styles = {
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      running: 'bg-blue-100 text-blue-800',
    };
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status]}`}>
        {status}
      </span>
    );
  };

  const getDuration = (startedAt: string, completedAt?: string) => {
    if (!completedAt) return 'Running...';
    const start = new Date(startedAt);
    const end = new Date(completedAt);
    const durationMs = end.getTime() - start.getTime();
    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Sync History</h2>
            <p className="text-sm text-gray-600 mt-1">
              Last 10 synchronization runs
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(80vh-140px)]">
          {isLoading ? (
            <div className="text-center py-12">
              <Loader2 className="w-12 h-12 mx-auto text-blue-600 animate-spin mb-4" />
              <p className="text-gray-600">Loading sync history...</p>
            </div>
          ) : history.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-400 mb-4">📋</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No sync history</h3>
              <p className="text-gray-600">
                This connector hasn't been synced yet
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {history.map((sync) => (
                <div
                  key={sync.id}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(sync.status)}
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-medium text-gray-900">
                            {format(new Date(sync.started_at), 'MMM dd, yyyy HH:mm:ss')}
                          </span>
                          {getStatusBadge(sync.status)}
                        </div>
                        <p className="text-sm text-gray-500 mt-1">
                          {formatDistanceToNow(new Date(sync.started_at), { addSuffix: true })}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        {sync.records_processed.toLocaleString()} records
                      </p>
                      <p className="text-sm text-gray-500">
                        Duration: {getDuration(sync.started_at, sync.completed_at)}
                      </p>
                    </div>
                  </div>

                  {sync.error_message && (
                    <div className="mt-3 bg-red-50 border border-red-200 rounded p-3">
                      <p className="text-sm font-medium text-red-800 mb-1">Error</p>
                      <p className="text-sm text-red-700">{sync.error_message}</p>
                    </div>
                  )}

                  {sync.status === 'completed' && (
                    <div className="mt-3 flex items-center space-x-6 text-sm text-gray-600">
                      <div>
                        <span className="font-medium">Started:</span>{' '}
                        {format(new Date(sync.started_at), 'HH:mm:ss')}
                      </div>
                      <div>
                        <span className="font-medium">Completed:</span>{' '}
                        {sync.completed_at
                          ? format(new Date(sync.completed_at), 'HH:mm:ss')
                          : 'N/A'}
                      </div>
                      <div>
                        <span className="font-medium">Rate:</span>{' '}
                        {sync.completed_at
                          ? (
                              sync.records_processed /
                              (new Date(sync.completed_at).getTime() -
                                new Date(sync.started_at).getTime()) *
                              1000
                            ).toFixed(0)
                          : '0'}{' '}
                        records/sec
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
