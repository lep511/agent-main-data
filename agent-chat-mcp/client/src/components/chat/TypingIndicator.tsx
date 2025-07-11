import React from 'react';

export function TypingIndicator() {
  return (
    <div className="flex items-start space-x-3 p-4 bg-white rounded-lg shadow-sm max-w-xs">
      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
        <div className="w-4 h-4 bg-blue-500 rounded-full"></div>
      </div>
      <div className="flex flex-col space-y-2">
        <div className="flex items-center space-x-1">
          <div 
            className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"
            style={{ animationDelay: '0ms', animationDuration: '1.4s' }}
          ></div>
          <div 
            className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"
            style={{ animationDelay: '200ms', animationDuration: '1.4s' }}
          ></div>
          <div 
            className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"
            style={{ animationDelay: '400ms', animationDuration: '1.4s' }}
          ></div>
        </div>
        <span className="text-xs text-gray-500">AI is thinking...</span>
      </div>
    </div>
  );
}