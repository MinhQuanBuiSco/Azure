import { useEffect, useRef } from 'react';

const ChatMessage = ({ message, isUser, isStreaming = false }) => {
  const messageRef = useRef(null);

  useEffect(() => {
    if (messageRef.current) {
      messageRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [message]); // ← Re-run when message changes for streaming updates

  return (
    <div
      ref={messageRef}
      className={`flex w-full mb-4 animate-in fade-in slide-in-from-bottom-2 duration-500 ${
        isUser ? 'justify-end' : 'justify-start'
      }`}
    >
      <div
        className={`flex items-start max-w-[85%] ${
          isUser ? 'flex-row-reverse' : 'flex-row'
        }`}
      >
        {/* Avatar */}
        <div
          className={`flex-shrink-0 ${isUser ? 'ml-3' : 'mr-3'}`}
        >
          <div
            className={`w-9 h-9 rounded-xl flex items-center justify-center font-semibold text-xs ${
              isUser
                ? 'bg-gradient-to-br from-blue-500 to-cyan-500 text-white shadow-lg shadow-blue-500/30'
                : 'bg-gradient-to-br from-slate-700 to-slate-600 text-slate-200 shadow-lg'
            }`}
          >
            {isUser ? (
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z" />
                <path d="M15 7v2a4 4 0 01-4 4H9.828l-1.766 1.767c.28.149.599.233.938.233h2l3 3v-3h2a2 2 0 002-2V9a2 2 0 00-2-2h-1z" />
              </svg>
            )}
          </div>
        </div>

        {/* Message Bubble */}
        <div
          className={`relative px-4 py-3 rounded-2xl backdrop-blur-sm ${
            isUser
              ? 'bg-gradient-to-br from-blue-500 to-cyan-500 text-white shadow-lg shadow-blue-500/20'
              : 'bg-slate-700/50 text-slate-100 shadow-lg border border-slate-600/50'
          }`}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
            {message}
            {isStreaming && !isUser && message && (
              <span className="inline-block w-1 h-4 ml-1 bg-cyan-400 animate-pulse"></span>
            )}
          </p>

          {/* Typing indicator for empty streaming message */}
          {isStreaming && !isUser && !message && (
            <div className="flex space-x-1 py-1">
              <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
