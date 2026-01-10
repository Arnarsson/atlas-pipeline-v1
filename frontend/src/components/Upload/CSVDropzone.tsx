import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, Loader2 } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { uploadCSV } from '@/api/client';

interface CSVDropzoneProps {
  onUploadSuccess: (runId: string) => void;
}

export default function CSVDropzone({ onUploadSuccess }: CSVDropzoneProps) {
  const [file, setFile] = useState<File | null>(null);
  const [datasetName, setDatasetName] = useState('');

  const uploadMutation = useMutation({
    mutationFn: (data: { file: File; datasetName: string }) =>
      uploadCSV(data.file, data.datasetName),
    onSuccess: (data) => {
      onUploadSuccess(data.run_id);
      setFile(null);
      setDatasetName('');
    },
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const csvFile = acceptedFiles[0];
      setFile(csvFile);
      // Auto-generate dataset name from filename
      const name = csvFile.name.replace('.csv', '').replace(/[^a-zA-Z0-9_]/g, '_');
      setDatasetName(name);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.csv'],
    },
    maxFiles: 1,
    multiple: false,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (file && datasetName) {
      uploadMutation.mutate({ file, datasetName });
    }
  };

  const removeFile = () => {
    setFile(null);
    setDatasetName('');
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-6" data-testid="csv-upload-form">
        {/* Dropzone */}
        <div
          {...getRootProps()}
          data-testid="csv-dropzone"
          className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all duration-200 ${
            isDragActive
              ? 'border-primary-500 bg-primary-50'
              : file
              ? 'border-green-500 bg-green-50'
              : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          }`}
        >
          <input {...getInputProps()} data-testid="csv-file-input" />

          {file ? (
            <div className="flex items-center justify-center gap-4">
              <FileText className="h-12 w-12 text-green-600" />
              <div className="text-left">
                <p className="text-lg font-semibold text-gray-900">{file.name}</p>
                <p className="text-sm text-gray-500">
                  {(file.size / 1024).toFixed(2)} KB
                </p>
              </div>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile();
                }}
                className="p-2 hover:bg-red-100 rounded-full transition-colors"
              >
                <X className="h-5 w-5 text-red-600" />
              </button>
            </div>
          ) : (
            <div>
              <Upload className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-4 text-lg font-medium text-gray-900">
                {isDragActive ? 'Drop your CSV file here' : 'Drag & drop a CSV file here'}
              </p>
              <p className="mt-2 text-sm text-gray-500">
                or click to browse files
              </p>
            </div>
          )}
        </div>

        {/* Dataset Name Input */}
        {file && (
          <div className="animate-slide-up">
            <label
              htmlFor="dataset-name"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Dataset Name
            </label>
            <input
              type="text"
              id="dataset-name"
              value={datasetName}
              onChange={(e) => setDatasetName(e.target.value)}
              placeholder="Enter dataset name"
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-4 py-2 border"
              required
            />
            <p className="mt-2 text-sm text-gray-500">
              A unique identifier for this dataset
            </p>
          </div>
        )}

        {/* Submit Button */}
        {file && (
          <button
            type="submit"
            data-testid="upload-submit-btn"
            disabled={!datasetName || uploadMutation.isPending}
            className="w-full flex justify-center items-center gap-2 py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {uploadMutation.isPending ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" data-testid="upload-spinner" />
                Processing...
              </>
            ) : (
              <>
                <Upload className="h-5 w-5" />
                Upload & Process
              </>
            )}
          </button>
        )}

        {/* Error Message */}
        {uploadMutation.isError && (
          <div className="rounded-md bg-red-50 p-4" data-testid="upload-error">
            <p className="text-sm text-red-800">
              Upload failed: {uploadMutation.error.message}
            </p>
          </div>
        )}
      </form>
    </div>
  );
}
