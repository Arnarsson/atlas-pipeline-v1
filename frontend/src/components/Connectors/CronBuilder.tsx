import { useState, useEffect } from 'react';

interface Props {
  value: string;
  onChange: (value: string) => void;
}

export default function CronBuilder({ value, onChange }: Props) {
  const [preset, setPreset] = useState<string>('custom');
  const [customCron, setCustomCron] = useState(value);

  const presets = [
    { label: 'Every hour', value: '0 * * * *', description: 'Runs at the start of every hour' },
    { label: 'Every day at midnight', value: '0 0 * * *', description: 'Runs at 00:00 every day' },
    { label: 'Every day at 9 AM', value: '0 9 * * *', description: 'Runs at 09:00 every day' },
    { label: 'Every Monday at 9 AM', value: '0 9 * * 1', description: 'Runs at 09:00 every Monday' },
    { label: 'First day of month', value: '0 0 1 * *', description: 'Runs at 00:00 on the 1st of every month' },
    { label: 'Manual', value: '', description: 'No automatic sync, trigger manually' },
  ];

  useEffect(() => {
    const matchedPreset = presets.find(p => p.value === value);
    if (matchedPreset) {
      setPreset(matchedPreset.value);
    } else {
      setPreset('custom');
      setCustomCron(value);
    }
  }, [value]);

  const handlePresetChange = (presetValue: string) => {
    setPreset(presetValue);
    if (presetValue !== 'custom') {
      onChange(presetValue);
    }
  };

  const handleCustomChange = (cronValue: string) => {
    setCustomCron(cronValue);
    onChange(cronValue);
  };

  const getCronDescription = (cron: string): string => {
    if (!cron) return 'No automatic sync';

    const parts = cron.split(' ');
    if (parts.length !== 5) return 'Invalid cron expression';

    const [minute, hour, dayOfMonth, month, dayOfWeek] = parts;

    let description = 'Runs ';

    // Time
    if (minute === '*' && hour === '*') {
      description += 'every minute ';
    } else if (minute !== '*' && hour === '*') {
      description += `at :${minute.padStart(2, '0')} of every hour `;
    } else if (minute !== '*' && hour !== '*') {
      description += `at ${hour.padStart(2, '0')}:${minute.padStart(2, '0')} `;
    }

    // Day of month
    if (dayOfMonth !== '*') {
      description += `on day ${dayOfMonth} `;
    }

    // Month
    if (month !== '*') {
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      description += `in ${months[parseInt(month) - 1]} `;
    }

    // Day of week
    if (dayOfWeek !== '*') {
      const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
      description += `on ${days[parseInt(dayOfWeek)]} `;
    }

    // Default
    if (dayOfMonth === '*' && month === '*' && dayOfWeek === '*') {
      description += 'every day';
    }

    return description.trim();
  };

  return (
    <div className="space-y-4">
      {/* Preset Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Choose a schedule
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {presets.map((p) => (
            <button
              key={p.value}
              onClick={() => handlePresetChange(p.value)}
              className={`p-4 border-2 rounded-lg text-left transition-colors ${
                preset === p.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-gray-900">{p.label}</span>
                {preset === p.value && (
                  <span className="text-blue-600">✓</span>
                )}
              </div>
              <p className="text-sm text-gray-600">{p.description}</p>
              {p.value && (
                <p className="text-xs text-gray-500 mt-1 font-mono">{p.value}</p>
              )}
            </button>
          ))}

          {/* Custom Option */}
          <button
            onClick={() => setPreset('custom')}
            className={`p-4 border-2 rounded-lg text-left transition-colors ${
              preset === 'custom'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-medium text-gray-900">Custom</span>
              {preset === 'custom' && (
                <span className="text-blue-600">✓</span>
              )}
            </div>
            <p className="text-sm text-gray-600">Define your own cron expression</p>
          </button>
        </div>
      </div>

      {/* Custom Cron Input */}
      {preset === 'custom' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Custom Cron Expression
          </label>
          <input
            type="text"
            value={customCron}
            onChange={(e) => handleCustomChange(e.target.value)}
            placeholder="0 9 * * 1-5"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 font-mono"
          />
          <p className="text-xs text-gray-500 mt-1">
            Format: minute hour day month day-of-week
          </p>
        </div>
      )}

      {/* Live Preview */}
      {(preset !== 'custom' ? preset : customCron) && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm font-medium text-blue-900 mb-1">Schedule Preview</p>
          <p className="text-sm text-blue-800">
            {getCronDescription(preset !== 'custom' ? preset : customCron)}
          </p>
          {(preset !== 'custom' ? preset : customCron) && (
            <p className="text-xs text-blue-700 mt-1 font-mono">
              Cron: {preset !== 'custom' ? preset : customCron}
            </p>
          )}
        </div>
      )}

      {/* Help Text */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Cron Expression Help</h4>
        <div className="text-xs text-gray-600 space-y-1">
          <p>• <code className="bg-white px-1 rounded">*</code> - Any value</p>
          <p>• <code className="bg-white px-1 rounded">5</code> - Specific value (e.g., 5th minute)</p>
          <p>• <code className="bg-white px-1 rounded">1-5</code> - Range (e.g., Monday to Friday)</p>
          <p>• <code className="bg-white px-1 rounded">*/15</code> - Every N units (e.g., every 15 minutes)</p>
        </div>
        <div className="mt-3 text-xs text-gray-600">
          <p className="font-medium mb-1">Examples:</p>
          <p>• <code className="bg-white px-1 rounded">0 9 * * 1-5</code> - Every weekday at 9:00 AM</p>
          <p>• <code className="bg-white px-1 rounded">*/30 * * * *</code> - Every 30 minutes</p>
          <p>• <code className="bg-white px-1 rounded">0 0 1 * *</code> - First day of every month at midnight</p>
        </div>
      </div>
    </div>
  );
}
