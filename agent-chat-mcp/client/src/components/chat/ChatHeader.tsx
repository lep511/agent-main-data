import { cn } from "@/lib/utils";

interface ChatHeaderProps {
  isConnected: boolean;
  className?: string;
}

export function ChatHeader({ isConnected, className }: ChatHeaderProps) {
  return (
    <header className={cn("bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between shadow-sm", className)}>
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
          </svg>
        </div>
        <div>
          <h1 className="text-lg font-semibold text-gray-900">AI Assistant</h1>
          <p className="text-sm text-gray-500">Powered by MCP</p>
        </div>
      </div>
      <div className="flex items-center space-x-2">
        <div className="flex items-center space-x-2">
          <div className={cn(
            "w-2 h-2 rounded-full",
            isConnected ? "bg-green-500 animate-pulse" : "bg-red-500"
          )}></div>
          <span className="text-sm font-medium text-gray-700">
            {isConnected ? "Connected" : "Disconnected"}
          </span>
        </div>
        <button className="p-2 hover:bg-gray-100 rounded-full transition-colors">
          <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"></path>
          </svg>
        </button>
      </div>
    </header>
  );
}
