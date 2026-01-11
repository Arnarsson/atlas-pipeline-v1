import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, Loader2, CheckCircle, Sparkles, AlertTriangle } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
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
        <motion.div
          {...getRootProps()}
          data-testid="csv-dropzone"
          className={`relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300 overflow-hidden ${
            isDragActive
              ? 'border-primary-500 bg-gradient-to-br from-primary-50 to-blue-50 shadow-xl scale-105'
              : file
              ? 'border-green-500 bg-gradient-to-br from-green-50 to-emerald-50 shadow-lg'
              : 'border-gray-300 hover:border-primary-400 hover:bg-gradient-to-br hover:from-gray-50 hover:to-blue-50 hover:shadow-md'
          }`}
          whileHover={{ scale: file ? 1 : 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <input {...getInputProps()} data-testid="csv-file-input" />

          {/* Background shimmer effect when dragging */}
          <AnimatePresence>
            {isDragActive && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 bg-gradient-to-r from-transparent via-primary-100 to-transparent"
                style={{
                  backgroundSize: '200% 100%',
                }}
              >
                <motion.div
                  animate={{
                    x: ['-100%', '100%'],
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    ease: 'linear',
                  }}
                  className="h-full w-full bg-gradient-to-r from-transparent via-white/30 to-transparent"
                />
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence mode="wait">
            {file ? (
              <motion.div
                key="file-selected"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{ duration: 0.3 }}
                className="flex items-center justify-center gap-4 relative z-10"
              >
                <motion.div
                  initial={{ rotate: -10, scale: 0.8 }}
                  animate={{ rotate: 0, scale: 1 }}
                  transition={{ type: 'spring', stiffness: 200, damping: 15 }}
                >
                  <div className="relative">
                    <FileText className="h-16 w-16 text-green-600" />
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: 0.2 }}
                      className="absolute -top-2 -right-2"
                    >
                      <CheckCircle className="h-6 w-6 text-green-500 bg-white rounded-full" />
                    </motion.div>
                  </div>
                </motion.div>
                <div className="text-left">
                  <p className="text-lg font-bold text-gray-900">{file.name}</p>
                  <p className="text-sm text-gray-600 font-medium">
                    {(file.size / 1024).toFixed(2)} KB
                  </p>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: '100%' }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                    className="mt-2 h-1 bg-gradient-to-r from-green-400 to-emerald-500 rounded-full"
                  />
                </div>
                <motion.button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile();
                  }}
                  whileHover={{ scale: 1.1, rotate: 90 }}
                  whileTap={{ scale: 0.9 }}
                  className="p-2 hover:bg-red-100 rounded-full transition-colors"
                >
                  <X className="h-5 w-5 text-red-600" />
                </motion.button>
              </motion.div>
            ) : (
              <motion.div
                key="empty-state"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.3 }}
                className="relative z-10"
              >
                <motion.div
                  animate={{
                    y: isDragActive ? [0, -10, 0] : 0,
                  }}
                  transition={{
                    duration: 1,
                    repeat: isDragActive ? Infinity : 0,
                    ease: 'easeInOut',
                  }}
                >
                  <Upload className={`mx-auto h-16 w-16 ${isDragActive ? 'text-primary-600' : 'text-gray-400'} transition-colors`} />
                </motion.div>
                <p className="mt-6 text-xl font-bold text-gray-900">
                  {isDragActive ? (
                    <motion.span
                      initial={{ scale: 0.9 }}
                      animate={{ scale: 1 }}
                      className="text-primary-600 flex items-center justify-center gap-2"
                    >
                      <Sparkles className="h-5 w-5" />
                      Drop your CSV file here
                      <Sparkles className="h-5 w-5" />
                    </motion.span>
                  ) : (
                    'Drag & drop a CSV file here'
                  )}
                </p>
                <p className="mt-3 text-sm text-gray-500 font-medium">
                  or click to browse files
                </p>
                <div className="mt-6 flex items-center justify-center gap-4 text-xs text-gray-400">
                  <span className="flex items-center gap-1">
                    <CheckCircle className="h-4 w-4" />
                    PII Detection
                  </span>
                  <span className="flex items-center gap-1">
                    <CheckCircle className="h-4 w-4" />
                    Quality Validation
                  </span>
                  <span className="flex items-center gap-1">
                    <CheckCircle className="h-4 w-4" />
                    Instant Results
                  </span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Dataset Name Input */}
        <AnimatePresence>
          {file && (
            <motion.div
              initial={{ opacity: 0, y: 20, height: 0 }}
              animate={{ opacity: 1, y: 0, height: 'auto' }}
              exit={{ opacity: 0, y: -20, height: 0 }}
              transition={{ duration: 0.3 }}
            >
              <label
                htmlFor="dataset-name"
                className="block text-sm font-bold text-gray-700 mb-2"
              >
                Dataset Name
              </label>
              <input
                type="text"
                id="dataset-name"
                value={datasetName}
                onChange={(e) => setDatasetName(e.target.value)}
                placeholder="Enter dataset name"
                className="block w-full rounded-xl border-2 border-gray-300 shadow-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-500 sm:text-sm px-4 py-3 transition-all duration-200"
                required
              />
              <p className="mt-2 text-sm text-gray-500 font-medium">
                A unique identifier for this dataset
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Submit Button */}
        <AnimatePresence>
          {file && (
            <motion.button
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3, delay: 0.1 }}
              whileHover={{ scale: uploadMutation.isPending ? 1 : 1.02 }}
              whileTap={{ scale: uploadMutation.isPending ? 1 : 0.98 }}
              type="submit"
              data-testid="upload-submit-btn"
              disabled={!datasetName || uploadMutation.isPending}
              className="w-full flex justify-center items-center gap-2 py-4 px-6 border-2 border-transparent rounded-xl shadow-lg text-base font-bold text-white bg-gradient-to-r from-primary-600 to-blue-600 hover:from-primary-700 hover:to-blue-700 focus:outline-none focus:ring-4 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300"
            >
              {uploadMutation.isPending ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" data-testid="upload-spinner" />
                  <span>Processing Your Data...</span>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                  >
                    <Sparkles className="h-5 w-5" />
                  </motion.div>
                </>
              ) : (
                <>
                  <Upload className="h-5 w-5" />
                  <span>Upload & Process</span>
                  <Sparkles className="h-5 w-5" />
                </>
              )}
            </motion.button>
          )}
        </AnimatePresence>

        {/* Error Message */}
        <AnimatePresence>
          {uploadMutation.isError && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
              className="rounded-xl bg-gradient-to-r from-red-50 to-orange-50 border-2 border-red-200 p-4 shadow-md"
              data-testid="upload-error"
            >
              <div className="flex items-center gap-3">
                <div className="flex-shrink-0">
                  <motion.div
                    animate={{ rotate: [0, 10, -10, 0] }}
                    transition={{ duration: 0.5, repeat: 2 }}
                  >
                    <AlertTriangle className="h-6 w-6 text-red-600" />
                  </motion.div>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-red-900">Upload Failed</h3>
                  <p className="text-sm text-red-800 mt-1">
                    {uploadMutation.error.message}
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </form>
    </div>
  );
}
