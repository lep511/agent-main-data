import { useEffect, useRef } from "react";
import { Message } from "@shared/schema";
import { MessageBubble } from "./MessageBubble";
import { cn } from "@/lib/utils";

interface ChatMessagesProps {
  messages: Message[];
  isLoading: boolean;
  error?: string;
  className?: string;
}

export function ChatMessages({ messages, isLoading, error, className }: ChatMessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  return (
    <main className={cn("flex-1 overflow-y-auto p-4 space-y-4", className)}>
      {/* Welcome Message */}
      {messages.length === 0 && !isLoading && (
        <div className="flex items-start space-x-3 animate-fade-in">
          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
            </svg>
          </div>
          <div className="flex-1">
            <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-200 max-w-md">
              <p className="text-gray-900">
                Hello! I'm your AI assistant powered by MCP (Model Context Protocol). I can help you with various tasks and questions. How can I assist you today?
              </p>
            </div>
            <div className="flex items-center space-x-2 mt-1">
              <span className="text-xs text-gray-500">AI Assistant</span>
              <span className="text-xs text-gray-400">•</span>
              <span className="text-xs text-gray-400">Ready to help</span>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-start space-x-3 animate-fade-in">
          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
            </svg>
          </div>
          <div className="flex-1">
            <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-200 max-w-md">
              <div className="flex items-center space-x-2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                </div>
                <span className="text-sm text-gray-500">AI is thinking...</span>
              </div>
            </div>
            <div className="flex items-center space-x-2 mt-1">
              <span className="text-xs text-gray-500">AI Assistant</span>
              <span className="text-xs text-gray-400">•</span>
              <span className="text-xs text-gray-400">Processing with MCP</span>
            </div>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="flex items-start space-x-3 animate-fade-in">
          <div className="w-8 h-8 bg-red-600 rounded-full flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
          </div>
          <div className="flex-1">
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 max-w-md">
              <p className="text-red-800 text-sm font-medium">Connection Error</p>
              <p className="text-red-700 text-sm mt-1">{error}</p>
            </div>
            <div className="flex items-center space-x-2 mt-1">
              <span className="text-xs text-gray-500">System</span>
              <span className="text-xs text-gray-400">•</span>
              <span className="text-xs text-gray-400">Error occurred</span>
            </div>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </main>
  );
}
