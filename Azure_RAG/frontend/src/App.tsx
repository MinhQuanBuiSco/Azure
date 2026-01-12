import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PDFUploader } from './components/PDFUploader';
import { IndexingStatusComponent } from './components/IndexingStatus';
import { SearchStrategySelector } from './components/SearchStrategySelector';
import { ChatInterface } from './components/ChatInterface';
import { SearchResults } from './components/SearchResults';
import { apiClient } from './services/api';
import type { UploadResponse, QueryResponse } from './types';
import { SearchStrategy } from './types';

function App() {
  const [uploadResponse, setUploadResponse] = useState<UploadResponse | null>(null);
  const [isIndexing, setIsIndexing] = useState(false);
  const [isIndexed, setIsIndexed] = useState(false);
  const [searchStrategy, setSearchStrategy] = useState<SearchStrategy>(SearchStrategy.HYBRID);
  const [queryResponse, setQueryResponse] = useState<QueryResponse | null>(null);
  const [isClearingCache, setIsClearingCache] = useState(false);

  const handleUploadSuccess = async (response: UploadResponse) => {
    setUploadResponse(response);
    setIsIndexing(true);
    setIsIndexed(false);

    try {
      await apiClient.startIndexing(response.document_id, true);
    } catch (error) {
      console.error('Failed to start indexing:', error);
    }
  };

  const handleIndexingComplete = () => {
    setIsIndexing(false);
    setIsIndexed(true);
  };

  const handleQueryResponse = (response: QueryResponse) => {
    setQueryResponse(response);
  };

  const handleClearCache = async () => {
    setIsClearingCache(true);
    try {
      const result = await apiClient.clearCache();
      console.log(`Cache cleared: ${result.cleared_keys} keys deleted`);
      // Optionally show a toast notification
    } catch (error) {
      console.error('Failed to clear cache:', error);
    } finally {
      setIsClearingCache(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            rotate: [0, 90, 0],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-purple-400/20 to-pink-400/20 blur-3xl"
        />
        <motion.div
          animate={{
            scale: [1.2, 1, 1.2],
            rotate: [90, 0, 90],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{
            duration: 25,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-to-tl from-blue-400/20 to-indigo-400/20 blur-3xl"
        />
      </div>

      {/* Header */}
      <motion.header
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="relative backdrop-blur-xl bg-white/70 border-b border-white/20 shadow-lg"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-between">
            <motion.div
              initial={{ x: -50, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.2, duration: 0.6 }}
            >
              <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                RAG Intelligence
              </h1>
              <p className="mt-2 text-sm text-gray-600 font-medium">
                Advanced document analysis powered by Azure AI
              </p>
            </motion.div>
            <motion.div
              initial={{ x: 50, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.3, duration: 0.6 }}
              className="flex items-center space-x-3 px-4 py-2 rounded-full bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200/50"
            >
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="w-2.5 h-2.5 bg-green-500 rounded-full shadow-lg shadow-green-500/50"
              />
              <span className="text-sm font-medium text-gray-700">System Online</span>
            </motion.div>
          </div>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="space-y-8">
          <AnimatePresence mode="wait">
            {/* Step 1: Upload */}
            {!uploadResponse && (
              <motion.section
                key="upload"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.5 }}
              >
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 }}
                  className="mb-6"
                >
                  <div className="flex items-center space-x-3 mb-2">
                    <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white font-bold shadow-lg">
                      1
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900">Upload Document</h2>
                  </div>
                  <p className="text-gray-600 ml-13">
                    Start by uploading a PDF document for intelligent analysis
                  </p>
                </motion.div>
                <PDFUploader onUploadSuccess={handleUploadSuccess} />
              </motion.section>
            )}

            {/* Step 2: Indexing Status */}
            {isIndexing && uploadResponse && (
              <motion.section
                key="indexing"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.5 }}
              >
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 }}
                  className="mb-6"
                >
                  <div className="flex items-center space-x-3 mb-2">
                    <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-600 text-white font-bold shadow-lg">
                      2
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900">Processing Document</h2>
                  </div>
                  <p className="text-gray-600 ml-13">
                    Extracting entities, generating embeddings, and indexing content
                  </p>
                </motion.div>
                <IndexingStatusComponent
                  documentId={uploadResponse.document_id}
                  onComplete={handleIndexingComplete}
                />
              </motion.section>
            )}

            {/* Step 3: Query Interface */}
            {isIndexed && (
              <motion.div
                key="query"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
              >
                <motion.section
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 }}
                >
                  <div className="mb-6">
                    <div className="flex items-center space-x-3 mb-2">
                      <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-br from-pink-500 to-rose-600 text-white font-bold shadow-lg">
                        3
                      </div>
                      <h2 className="text-2xl font-bold text-gray-900">Ask Questions</h2>
                    </div>
                    <p className="text-gray-600 ml-13">
                      Query your document using advanced AI search strategies
                    </p>
                  </div>

                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.3 }}
                    className="backdrop-blur-xl bg-white/70 rounded-3xl border border-white/20 shadow-2xl p-8 space-y-8"
                  >
                    {/* Document Info */}
                    <motion.div
                      whileHover={{ scale: 1.01 }}
                      className="flex items-center justify-between pb-6 border-b border-gray-200/50"
                    >
                      <div className="flex items-center space-x-4">
                        <div className="p-3 rounded-2xl bg-gradient-to-br from-red-500 to-pink-600 shadow-lg">
                          <svg
                            className="w-6 h-6 text-white"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                              clipRule="evenodd"
                            />
                          </svg>
                        </div>
                        <div>
                          <h3 className="font-bold text-gray-900 text-lg">
                            {uploadResponse?.filename}
                          </h3>
                          <p className="text-sm text-gray-500">
                            {((uploadResponse?.size_bytes || 0) / 1024 / 1024).toFixed(2)} MB • Ready for queries
                          </p>
                        </div>
                      </div>
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => {
                          setUploadResponse(null);
                          setIsIndexed(false);
                          setQueryResponse(null);
                        }}
                        className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium shadow-lg hover:shadow-xl transition-shadow"
                      >
                        New Document
                      </motion.button>
                    </motion.div>

                    {/* Search Strategy Selector with Clear Cache Button */}
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <h3 className="text-sm font-medium text-gray-700">Search Strategy</h3>
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={handleClearCache}
                          disabled={isClearingCache}
                          className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-orange-50 hover:bg-orange-100 text-orange-700 text-xs font-medium transition-colors border border-orange-200 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                          <span>{isClearingCache ? 'Clearing...' : 'Clear Cache'}</span>
                        </motion.button>
                      </div>
                      <SearchStrategySelector
                        selected={searchStrategy}
                        onChange={setSearchStrategy}
                      />
                    </div>

                    {/* Chat Interface */}
                    <ChatInterface strategy={searchStrategy} onResponse={handleQueryResponse} />
                  </motion.div>
                </motion.section>

                {/* Results */}
                <AnimatePresence>
                  {queryResponse && (
                    <motion.section
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      transition={{ delay: 0.2 }}
                      className="mt-8"
                    >
                      <SearchResults response={queryResponse} />
                    </motion.section>
                  )}
                </AnimatePresence>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Footer */}
      <motion.footer
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="relative mt-20 backdrop-blur-xl bg-white/70 border-t border-white/20"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-600 font-medium">
            Powered by{' '}
            <span className="font-semibold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              Azure OpenAI
            </span>{' '}
            •{' '}
            <span className="font-semibold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              Azure AI Search
            </span>{' '}
            •{' '}
            <span className="font-semibold bg-gradient-to-r from-pink-600 to-rose-600 bg-clip-text text-transparent">
              Redis Cache
            </span>
          </p>
        </div>
      </motion.footer>
    </div>
  );
}

export default App;
