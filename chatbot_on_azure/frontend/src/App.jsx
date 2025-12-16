import { useState, useRef, useEffect } from 'react';
import ChatMessage from './components/ChatMessage';
import TypingIndicator from './components/TypingIndicator';
import { sendChatMessageStream } from './services/api';
import './index.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    // Focus input on mount
    inputRef.current?.focus();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setError(null);

    // Add user message to chat
    const newUserMessage = { role: 'user', content: userMessage };
    setMessages((prev) => [...prev, newUserMessage]);

    setIsLoading(true);

    // Add placeholder for AI response
    setMessages((prev) => [
      ...prev,
      { role: 'assistant', content: '', streaming: true },
    ]);

    try {
      // Prepare messages for API (include conversation history)
      const conversationHistory = [...messages, newUserMessage];

      // Send to backend with streaming - SIMPLE DIRECT UPDATE
      await sendChatMessageStream(conversationHistory, (chunk) => {
        console.log('Received chunk:', chunk);

        // Direct setState update - React 18 will handle batching
        setMessages((prev) => {
          const newMessages = [...prev];
          const lastIndex = newMessages.length - 1;
          const currentContent = newMessages[lastIndex].content;
          const newContent = currentContent + chunk;

          newMessages[lastIndex] = {
            role: 'assistant',
            content: newContent,
            streaming: true,
          };

          console.log('UI updated, content length:', newContent.length);
          return newMessages;
        });
      });

      // Final update - mark streaming as complete
      setMessages((prev) => {
        const newMessages = [...prev];
        const lastIndex = newMessages.length - 1;
        if (newMessages[lastIndex]) {
          newMessages[lastIndex].streaming = false;
        }
        return newMessages;
      });

      console.log('Streaming complete!');
    } catch (err) {
      // Remove the placeholder message on error
      setMessages((prev) => prev.slice(0, -1));
      setError(err.message || 'Failed to get response. Please try again.');
      console.error('Chat error:', err);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError(null);
    inputRef.current?.focus();
  };

  return (
    <div className="min-h-screen w-full relative overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Animated mesh gradient background */}
      <div className="fixed inset-0 bg-gradient-to-br from-blue-600/20 via-purple-600/20 to-cyan-600/20 opacity-50" />

      {/* Grid pattern overlay */}
      <div className="fixed inset-0 opacity-[0.02]">
        <div className="absolute inset-0" style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
          backgroundSize: '50px 50px'
        }} />
      </div>

      {/* Floating gradient orbs */}
      <div className="fixed top-20 left-20 w-96 h-96 bg-blue-500/30 rounded-full mix-blend-normal filter blur-3xl opacity-40 animate-float" />
      <div className="fixed top-40 right-20 w-96 h-96 bg-purple-500/30 rounded-full mix-blend-normal filter blur-3xl opacity-40 animate-float" style={{ animationDelay: '2s' }} />
      <div className="fixed bottom-20 left-1/2 w-96 h-96 bg-cyan-500/30 rounded-full mix-blend-normal filter blur-3xl opacity-40 animate-float" style={{ animationDelay: '4s' }} />

      {/* Main container */}
      <div className="relative z-10 flex flex-col h-screen max-w-5xl mx-auto p-4 md:p-6">
        {/* Header */}
        <header className="mb-6 animate-in fade-in slide-in-from-top duration-700">
          <div className="backdrop-blur-xl bg-slate-800/40 rounded-2xl shadow-2xl border border-slate-700/50 p-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="relative w-11 h-11 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                  <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-slate-800"></div>
                </div>
                <div>
                  <h1 className="text-xl md:text-2xl font-bold text-white">
                    AI Assistant
                  </h1>
                  <p className="text-xs text-slate-400">Powered by OpenAI GPT-4</p>
                </div>
              </div>

              {messages.length > 0 && (
                <button
                  onClick={clearChat}
                  className="px-4 py-2 bg-slate-700/50 hover:bg-slate-600/50 backdrop-blur-sm text-slate-200 rounded-xl transition-all duration-300 border border-slate-600/50 hover:border-slate-500/50 text-sm font-medium"
                >
                  Clear Chat
                </button>
              )}
            </div>
          </div>
        </header>

        {/* Chat messages container */}
        <main className="flex-1 overflow-hidden mb-4 animate-in fade-in slide-in-from-bottom duration-700">
          <div className="h-full backdrop-blur-xl bg-slate-800/30 rounded-2xl shadow-2xl border border-slate-700/50 p-6 overflow-y-auto">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center px-4">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center mb-6 shadow-2xl shadow-blue-500/30 animate-float">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h2 className="text-2xl md:text-3xl font-bold text-white mb-2">
                  How can I help you today?
                </h2>
                <p className="text-slate-400 text-base max-w-md mb-8">
                  Ask me anything - from coding help to creative ideas
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl w-full">
                  {[
                    { icon: '💻', text: 'Explain quantum computing' },
                    { icon: '✨', text: 'Creative writing tips' },
                    { icon: '🚀', text: 'Latest tech trends' },
                    { icon: '📚', text: 'Recommend a book' },
                  ].map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => setInputValue(suggestion.text)}
                      className="group px-4 py-3 bg-slate-700/30 hover:bg-slate-700/50 backdrop-blur-sm text-slate-200 rounded-xl transition-all duration-300 border border-slate-600/30 hover:border-blue-500/50 text-sm text-left flex items-center gap-3"
                    >
                      <span className="text-xl">{suggestion.icon}</span>
                      <span className="group-hover:text-white transition-colors">{suggestion.text}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-1">
                {messages.map((msg, index) => (
                  <ChatMessage
                    key={`${index}-${msg.content.length}`}
                    message={msg.content}
                    isUser={msg.role === 'user'}
                    isStreaming={msg.streaming}
                  />
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </main>

        {/* Error message */}
        {error && (
          <div className="mb-4 animate-in fade-in slide-in-from-bottom duration-300">
            <div className="backdrop-blur-xl bg-red-500/10 border border-red-500/30 rounded-xl p-4">
              <div className="flex items-center space-x-3">
                <svg className="w-5 h-5 text-red-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p className="text-red-200 text-sm flex-1">{error}</p>
                <button
                  onClick={() => setError(null)}
                  className="ml-auto text-red-300 hover:text-red-100 transition-colors flex-shrink-0"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Input form */}
        <footer className="animate-in fade-in slide-in-from-bottom duration-700" style={{ animationDelay: '100ms' }}>
          <form onSubmit={handleSubmit} className="backdrop-blur-xl bg-slate-800/40 rounded-2xl shadow-2xl border border-slate-700/50 p-4">
            <div className="flex items-end space-x-3">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message..."
                  rows="1"
                  disabled={isLoading}
                  className="w-full px-4 py-3 bg-slate-700/50 backdrop-blur-sm rounded-xl border border-slate-600/50 focus:border-blue-500/50 focus:outline-none focus:ring-2 focus:ring-blue-500/20 resize-none text-slate-100 placeholder-slate-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 max-h-32"
                  style={{ minHeight: '48px' }}
                />
              </div>
              <button
                type="submit"
                disabled={!inputValue.trim() || isLoading}
                className="px-5 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white rounded-xl font-medium transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50 flex items-center space-x-2"
              >
                <span>Send</span>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </form>
        </footer>
      </div>
    </div>
  );
}

export default App;
