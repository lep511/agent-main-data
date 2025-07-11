import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  isConnected: boolean;
  className?: string;
}

export function ChatInput({ onSendMessage, isLoading, isConnected, className }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading && isConnected) {
      onSendMessage(message.trim());
      setMessage("");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 128) + "px";
    }
  }, [message]);

  return (
    <footer className={cn("bg-white border-t border-gray-200 p-4", className)}>
      <div className="max-w-4xl mx-auto">
        <form onSubmit={handleSubmit} className="flex items-end space-x-3">
          <div className="flex-1">
            <label htmlFor="messageInput" className="sr-only">
              Type your message
            </label>
            <div className="relative">
              <Textarea
                ref={textareaRef}
                id="messageInput"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                className="w-full resize-none max-h-32 pr-16"
                rows={1}
                disabled={!isConnected}
              />
              <div className="absolute right-3 bottom-3 flex items-center space-x-1">
                <span className="text-xs text-gray-400">
                  {message.length}/1000
                </span>
              </div>
            </div>
          </div>
          <Button
            type="submit"
            disabled={!message.trim() || isLoading || !isConnected}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg px-4 py-3 font-medium transition-colors flex items-center space-x-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
            </svg>
            <span className="hidden sm:inline">Send</span>
          </Button>
        </form>
        
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center space-x-4 text-xs text-gray-500">
            <div className="flex items-center space-x-1">
              <svg className="w-3 h-3 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
              </svg>
              <span>MCP Protocol Active</span>
            </div>
            <div className="flex items-center space-x-1">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
              </svg>
              <span>Secure Connection</span>
            </div>
          </div>
          <div className="text-xs text-gray-400">
            Press Enter to send, Shift+Enter for new line
          </div>
        </div>
      </div>
    </footer>
  );
}
