import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ChatHeader } from "@/components/chat/ChatHeader";
import { ChatMessages } from "@/components/chat/ChatMessages";
import { ChatInput } from "@/components/chat/ChatInput";
import { TypingIndicator } from "@/components/chat/TypingIndicator";
import { useWebSocket } from "@/hooks/useWebSocket";
import { apiRequest } from "@/lib/queryClient";
import { Message, Conversation } from "@shared/schema";

export default function Chat() {
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  
  const { isConnected, messages, isLoading, isLLMThinking, sendMessage, setMessages } = useWebSocket();

  // Create conversation mutation
  const createConversationMutation = useMutation({
    mutationFn: async (title: string) => {
      const response = await apiRequest("POST", "/api/conversations", { title });
      return response.json();
    },
    onSuccess: (conversation: Conversation) => {
      setConversationId(conversation.id);
    },
    onError: (error: Error) => {
      setError(`Failed to create conversation: ${error.message}`);
    },
  });

  // Load messages query
  const { data: existingMessages } = useQuery({
    queryKey: ["/api/conversations", conversationId, "messages"],
    enabled: conversationId !== null,
    onSuccess: (messages: Message[]) => {
      setMessages(messages);
    },
  });

  // Initialize conversation on mount
  useEffect(() => {
    if (!conversationId && isConnected) {
      createConversationMutation.mutate("Chat Session");
    }
  }, [isConnected, conversationId]);

  // Handle sending messages
  const handleSendMessage = (content: string) => {
    if (conversationId && isConnected) {
      sendMessage(conversationId, content);
      setError(null);
    } else {
      setError("Not connected to chat service");
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <ChatHeader isConnected={isConnected} />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto">
          <ChatMessages 
            messages={messages} 
            isLoading={isLoading}
            error={error}
          />
        </div>
        
        {/* Typing indicator */}
        {isLLMThinking && (
          <div className="px-4 py-2 border-t bg-white">
            <TypingIndicator />
          </div>
        )}
      </div>
      
      <ChatInput 
        onSendMessage={handleSendMessage}
        isLoading={isLoading || createConversationMutation.isPending}
        isConnected={isConnected && conversationId !== null}
      />
    </div>
  );
}