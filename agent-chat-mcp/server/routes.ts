import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer, WebSocket } from "ws";
import { storage } from "./storage";
import { generateAIResponse } from "./services/ai";
import { insertMessageSchema, type Message } from "@shared/schema";

export async function registerRoutes(app: Express): Promise<Server> {
  const httpServer = createServer(app);

  // WebSocket server for real-time chat
  const wss = new WebSocketServer({ server: httpServer, path: '/ws' });

  // API Routes
  app.get("/api/conversations/:id/messages", async (req, res) => {
    try {
      const conversationId = parseInt(req.params.id);
      const messages = await storage.getMessagesByConversationId(conversationId);
      res.json(messages);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch messages" });
    }
  });

  app.post("/api/conversations", async (req, res) => {
    try {
      const conversation = await storage.createConversation({
        userId: null, // For now, we'll use anonymous conversations
        title: req.body.title || "New Conversation"
      });
      res.json(conversation);
    } catch (error) {
      res.status(500).json({ error: "Failed to create conversation" });
    }
  });

  // WebSocket connection handling
  wss.on('connection', (ws: WebSocket) => {
    console.log('New WebSocket connection established');

    ws.on('message', async (data: Buffer) => {
      try {
        const message = JSON.parse(data.toString());
        
        if (message.type === 'chat_message') {
          const { conversationId, content } = message;
          
          // Validate and create user message
          const userMessage = await storage.createMessage({
            conversationId,
            role: 'user',
            content
          });

          // Broadcast user message to all connected clients
          broadcastMessage(wss, {
            type: 'new_message',
            message: userMessage
          });

          // Get conversation history for AI context
          const conversationHistory = await storage.getMessagesByConversationId(conversationId);
          const historyForAI = conversationHistory.map(msg => ({
            role: msg.role,
            content: msg.content
          }));

          // Generate AI response
          const aiResponse = await generateAIResponse(content, historyForAI);
          
          // Create AI message
          const aiMessage = await storage.createMessage({
            conversationId,
            role: 'assistant',
            content: aiResponse.content
          });

          // Broadcast AI response to all connected clients
          broadcastMessage(wss, {
            type: 'new_message',
            message: aiMessage
          });
        }
      } catch (error) {
        console.error('WebSocket message error:', error);
        ws.send(JSON.stringify({
          type: 'error',
          message: 'Failed to process message'
        }));
      }
    });

    ws.on('close', () => {
      console.log('WebSocket connection closed');
    });

    ws.on('error', (error) => {
      console.error('WebSocket error:', error);
    });
  });

  function broadcastMessage(wss: WebSocketServer, message: any) {
    wss.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(JSON.stringify(message));
      }
    });
  }

  return httpServer;
}
