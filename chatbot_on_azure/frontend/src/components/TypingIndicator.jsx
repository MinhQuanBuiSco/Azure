const TypingIndicator = () => {
  return (
    <div className="flex w-full mb-4 justify-start">
      <div className="flex items-start">
        {/* AI Avatar */}
        <div className="flex-shrink-0 mr-3">
          <div className="w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm bg-gradient-to-br from-blue-500 to-cyan-500 text-white shadow-lg shadow-blue-500/50">
            AI
          </div>
        </div>

        {/* Typing bubble */}
        <div className="relative px-5 py-4 rounded-2xl bg-white/80 backdrop-blur-sm shadow-lg border border-white/50">
          <div className="flex space-x-2">
            <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>

          {/* Message tail */}
          <div className="absolute left-[-8px] top-3 w-0 h-0 border-r-[12px] border-r-white/80 border-t-[8px] border-t-transparent border-b-[8px] border-b-transparent" />
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator;
