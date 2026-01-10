import { CheckCircle, XCircle, LucideIcon } from 'lucide-react';
import type { DimensionMetrics } from '@/types';

interface DimensionCardProps {
  title: string;
  metrics: DimensionMetrics;
  icon: LucideIcon;
}

export default function DimensionCard({ title, metrics, icon: Icon }: DimensionCardProps) {
  const { score, threshold, passed } = metrics;
  const percentage = Math.round(score * 100);
  const thresholdPercent = Math.round(threshold * 100);

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow duration-300">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${passed ? 'bg-green-100' : 'bg-red-100'}`}>
            <Icon className={`h-6 w-6 ${passed ? 'text-green-600' : 'text-red-600'}`} />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
        {passed ? (
          <CheckCircle className="h-6 w-6 text-green-500" />
        ) : (
          <XCircle className="h-6 w-6 text-red-500" />
        )}
      </div>

      <div className="space-y-3">
        <div className="flex items-end gap-2">
          <span className={`text-3xl font-bold ${passed ? 'text-green-600' : 'text-red-600'}`}>
            {percentage}%
          </span>
          <span className="text-sm text-gray-500 mb-1">
            (threshold: {thresholdPercent}%)
          </span>
        </div>

        <div className="relative pt-1">
          <div className="overflow-hidden h-3 text-xs flex rounded-full bg-gray-200">
            <div
              style={{ width: `${percentage}%` }}
              className={`shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center transition-all duration-500 ${
                passed ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            {!passed && (
              <div
                style={{ left: `${thresholdPercent}%` }}
                className="absolute top-0 h-full w-0.5 bg-gray-700"
              />
            )}
          </div>
        </div>

        {metrics.details && Object.keys(metrics.details).length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-xs font-medium text-gray-500 uppercase mb-2">Details</p>
            <div className="space-y-1">
              {Object.entries(metrics.details).map(([key, value]) => (
                <div key={key} className="flex justify-between text-sm">
                  <span className="text-gray-600 capitalize">{key.replace(/_/g, ' ')}:</span>
                  <span className="font-medium text-gray-900">
                    {typeof value === 'number' ? value.toLocaleString() : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
