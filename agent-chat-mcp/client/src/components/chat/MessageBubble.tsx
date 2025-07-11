import { Message } from "@shared/schema";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";

interface MessageBubbleProps {
  message: Message;
  className?: string;
}

export function MessageBubble({ message, className }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

  return (
    <div className={cn(
      "flex items-start space-x-3 animate-fade-in",
      isUser && "flex-row-reverse",
      className
    )}>
      {/* Avatar */}
      <div className={cn(
        "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
        isUser ? "bg-gray-300" : "bg-blue-600"
      )}>
        {isUser ? (
          <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
          </svg>
        ) : (
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
          </svg>
        )}
      </div>

      {/* Message Content */}
      <div className={cn(
        "flex-1 flex flex-col",
        isUser && "items-end"
      )}>
        <div className={cn(
          "rounded-lg p-3 shadow-sm max-w-2xl",
          isUser 
            ? "bg-blue-600 text-white" 
            : "bg-white border border-gray-200"
        )}>
          <p className={cn(
            "whitespace-pre-wrap",
            isUser ? "text-white" : "text-gray-900"
          )}>
            {message.content}
          </p>
        </div>
        
        {/* Message metadata */}
        <div className={cn(
          "flex items-center space-x-2 mt-1",
          isUser && "flex-row-reverse"
        )}>
          <span className="text-xs text-gray-500">
            {isUser ? "You" : "AI Assistant"}
          </span>
          <span className="text-xs text-gray-400">•</span>
          <span className="text-xs text-gray-400">
            {formatDistanceToNow(new Date(message.timestamp), { addSuffix: true })}
          </span>
          {isAssistant && (
            <>
              <div className="flex items-center space-x-1">
                <svg className="w-3 h-3 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                </svg>
                <span className="text-xs text-green-600">MCP Enabled</span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
