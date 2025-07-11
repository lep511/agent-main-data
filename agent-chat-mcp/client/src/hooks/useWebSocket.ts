import { useState, useEffect, useCallback, useRef } from 'react';
import { Message } from '@shared/schema';

interface WebSocketMessage {
  type: string;
  message?: Message;
  error?: string;
}

export function useWebSocket() {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLLMThinking, setIsLLMThinking] = useState(false);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    console.log('Attempting WebSocket connection to:', wsUrl);
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setSocket(ws);
    };

    ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        console.log('WebSocket message received:', data);
        
        if (data.type === 'new_message' && data.message) {
          console.log('Adding message:', data.message);
          console.log('Message sender:', data.message.sender);
          
          setMessages(prev => [...prev, data.message!]);
          setIsLoading(false);
          
          // Stop typing indicator when we receive an assistant message
          // Try multiple possible field names for the sender
          if (data.message.sender === 'assistant' || 
              data.message.sender === 'ai' || 
              data.message.role === 'assistant' ||
              data.message.type === 'assistant') {
            console.log('Stopping typing indicator for assistant message');
            setIsLLMThinking(false);
          }
          
          // Alternative: Stop typing indicator for any non-user message
          // Uncomment this if the above doesn't work:
          // if (data.message.sender !== 'user') {
          //   console.log('Stopping typing indicator for non-user message');
          //   setIsLLMThinking(false);
          // }
        } else if (data.type === 'error') {
          console.error('WebSocket error:', data.error);
          setIsLoading(false);
          setIsLLMThinking(false);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
        setIsLoading(false);
        setIsLLMThinking(false);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      setSocket(null);
      setIsLLMThinking(false);
      
      // Attempt to reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
      setIsLLMThinking(false);
    };

    return ws;
  }, []);

  const sendMessage = useCallback((conversationId: number, content: string) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      console.log('Sending message, starting typing indicator');
      setIsLoading(true);
      setIsLLMThinking(true);
      
      socket.send(JSON.stringify({
        type: 'chat_message',
        conversationId,
        content
      }));
    }
  }, [socket]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (socket) {
      socket.close();
    }
    setIsLLMThinking(false);
  }, [socket]);

  useEffect(() => {
    const ws = connect();
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      ws.close();
    };
  }, [connect]);

  return {
    isConnected,
    messages,
    isLoading,
    isLLMThinking,
    sendMessage,
    disconnect,
    setMessages
  };
}