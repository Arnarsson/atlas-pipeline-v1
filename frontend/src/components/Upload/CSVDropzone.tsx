import { useCallback, useEffect, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, Loader2, CheckCircle, AlertTriangle } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { uploadCSV } from '@/api/client';
import { Button } from '@/components/ui/button';

interface CSVDropzoneProps {
  onUploadSuccess: (runId: string) => void;
}

export default function CSVDropzone({ onUploadSuccess }: CSVDropzoneProps) {
  const [file, setFile] = useState<File | null>(null);
  const [datasetName, setDatasetName] = useState('');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [shouldAutoUpload, setShouldAutoUpload] = useState(false);

  const uploadMutation = useMutation({
    mutationFn: (data: { file: File; datasetName: string }) =>
      uploadCSV(data.file, data.datasetName),
    onSuccess: (data) => {
      setUploadError(null);
      setShouldAutoUpload(false);
      onUploadSuccess(data.run_id);
      setFile(null);
      setDatasetName('');
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error
          ? error.message
          : 'Upload failed. Please check your file and try again.';
      setUploadError(message);
      setShouldAutoUpload(false);
    },
  });
  const { mutate: triggerUpload, isPending, isError, error } = uploadMutation;

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const csvFile = acceptedFiles[0];
      setUploadError(null);

      if (csvFile.size === 0) {
        setUploadError('Selected CSV file is empty. Please upload a file with data.');
        setFile(null);
        setDatasetName('');
        setShouldAutoUpload(false);
        return;
      }

      setFile(csvFile);
      const name = csvFile.name.replace('.csv', '').replace(/[^a-zA-Z0-9_]/g, '_');
      setDatasetName(name);
      setShouldAutoUpload(true);
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
    setShouldAutoUpload(false);
    setUploadError(null);
    if (file && datasetName) {
      triggerUpload({ file, datasetName });
    }
  };

  const removeFile = () => {
    setFile(null);
    setDatasetName('');
    setUploadError(null);
    setShouldAutoUpload(false);
  };

  useEffect(() => {
    if (shouldAutoUpload && file && datasetName && !isPending) {
      triggerUpload({ file, datasetName });
      setShouldAutoUpload(false);
    }
  }, [shouldAutoUpload, file, datasetName, isPending, triggerUpload]);

  const mutationErrorMessage =
    isError && error instanceof Error
      ? error.message
      : isError
        ? 'Upload failed. Please try again.'
        : null;

  const errorMessage = uploadError || mutationErrorMessage;

  return (
    <div className="w-full max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-4" data-testid="csv-upload-form">
        {/* Dropzone */}
        <div
          {...getRootProps()}
          data-testid="csv-dropzone"
          className={`relative border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-[hsl(var(--foreground))] bg-[hsl(var(--secondary))]'
              : file
              ? 'border-green-500 bg-green-500/5'
              : 'border-[hsl(var(--border))] hover:border-[hsl(var(--foreground)/0.5)] hover:bg-[hsl(var(--secondary)/0.5)]'
          }`}
        >
          <input {...getInputProps()} data-testid="csv-file-input" />

          {file ? (
            <div className="flex items-center justify-center gap-4">
              <div className="relative">
                <FileText className="h-12 w-12 text-green-600" />
                <CheckCircle className="absolute -top-1 -right-1 h-5 w-5 text-green-500 bg-[hsl(var(--background))] rounded-full" />
              </div>
              <div className="text-left">
                <p className="text-sm font-medium text-[hsl(var(--foreground))]">{file.name}</p>
                <p className="text-xs text-[hsl(var(--muted-foreground))]">
                  {(file.size / 1024).toFixed(2)} KB
                </p>
              </div>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile();
                }}
                className="p-1.5 hover:bg-[hsl(var(--secondary))] rounded-md transition-colors"
              >
                <X className="h-4 w-4 text-[hsl(var(--muted-foreground))]" />
              </button>
            </div>
          ) : (
            <div>
              <Upload className={`mx-auto h-10 w-10 ${isDragActive ? 'text-[hsl(var(--foreground))]' : 'text-[hsl(var(--muted-foreground))]'}`} />
              <p className="mt-4 text-sm font-medium text-[hsl(var(--foreground))]">
                {isDragActive ? 'Drop your CSV file here' : 'Drag & drop a CSV file here'}
              </p>
              <p className="mt-1 text-xs text-[hsl(var(--muted-foreground))]">
                or click to browse files
              </p>
              <div className="mt-4 flex items-center justify-center gap-4 text-xs text-[hsl(var(--muted-foreground))]">
                <span className="flex items-center gap-1">
                  <CheckCircle className="h-3 w-3" />
                  PII Detection
                </span>
                <span className="flex items-center gap-1">
                  <CheckCircle className="h-3 w-3" />
                  Quality Validation
                </span>
                <span className="flex items-center gap-1">
                  <CheckCircle className="h-3 w-3" />
                  Instant Results
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Dataset Name Input */}
        {file && (
          <div>
            <label
              htmlFor="dataset-name"
              className="block text-sm font-medium text-[hsl(var(--foreground))] mb-1.5"
            >
              Dataset Name
            </label>
            <input
              type="text"
              id="dataset-name"
              value={datasetName}
              onChange={(e) => setDatasetName(e.target.value)}
              placeholder="Enter dataset name"
              className="block w-full rounded-md border border-[hsl(var(--input))] bg-[hsl(var(--background))] px-3 py-2 text-sm text-[hsl(var(--foreground))] placeholder:text-[hsl(var(--muted-foreground))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))] focus:ring-offset-2 focus:ring-offset-[hsl(var(--background))]"
              required
            />
          </div>
        )}

        {/* Submit Button */}
        {file && (
          <Button
            type="submit"
            data-testid="upload-submit-btn"
            disabled={!datasetName || isPending}
            className="w-full"
          >
            {isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" data-testid="upload-spinner" />
                Processing...
              </>
            ) : (
              <>
                <Upload className="h-4 w-4 mr-2" />
                Upload & Process
              </>
            )}
          </Button>
        )}

        {/* Error Message */}
        {errorMessage && (
          <div
            className="rounded-md border border-red-200 bg-red-50 p-3"
            data-testid="upload-error"
          >
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <p className="text-sm text-red-800">{errorMessage}</p>
            </div>
          </div>
        )}
      </form>
    </div>
  );
}
