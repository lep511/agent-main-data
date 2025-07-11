# AI Chat Assistant

## Overview

This is a full-stack AI chat application built with React/TypeScript frontend and Express.js backend. The application provides a real-time chat interface where users can interact with an AI assistant powered by Anthropic's Claude model. The system uses WebSocket connections for real-time communication and includes a modern, responsive UI built with shadcn/ui components.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

- **README.md Created (2025-01-11)**: Generated comprehensive documentation covering installation, features, architecture, and deployment
- **TypeScript Errors Fixed**: Resolved type compatibility issues in storage.ts for conversation and message creation
- **WebSocket Connection Enhanced**: Added logging for better debugging of connection issues
- **Project Status**: Fully functional chat interface with WebSocket communication, awaiting API key for AI responses

## System Architecture

### Frontend Architecture
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite for fast development and optimized builds
- **UI Library**: shadcn/ui components built on Radix UI primitives
- **Styling**: Tailwind CSS with CSS variables for theming
- **State Management**: React Query (TanStack Query) for server state management
- **Routing**: Wouter for lightweight client-side routing

### Backend Architecture
- **Runtime**: Node.js with Express.js framework
- **Language**: TypeScript with ES modules
- **WebSocket**: Native WebSocket server for real-time chat
- **Database**: PostgreSQL with Drizzle ORM
- **AI Integration**: Anthropic SDK for Claude AI responses

### Data Storage
- **Database**: PostgreSQL (configured via Drizzle)
- **ORM**: Drizzle ORM with TypeScript schemas
- **In-Memory Fallback**: Memory storage implementation for development
- **Migrations**: Drizzle Kit for database schema management

## Key Components

### Database Schema
- **Users**: Basic user authentication (username/password)
- **Conversations**: Chat sessions with timestamps
- **Messages**: Individual chat messages with role (user/assistant) and content

### WebSocket Communication
- Real-time bidirectional communication between client and server
- Message broadcasting for instant chat updates
- Connection state management with automatic reconnection

### AI Integration
- Claude Sonnet 4 model integration via Anthropic SDK
- Conversation context management (last 10 messages)
- Error handling and fallback responses
- System prompt configuration for assistant behavior

### UI Components
- **Chat Interface**: Header, message list, and input components
- **Message Bubbles**: Styled user and assistant message display
- **Connection Status**: Real-time connection indicator
- **Responsive Design**: Mobile-first responsive layout

## Data Flow

1. **User Input**: User types message in chat input
2. **WebSocket Send**: Message sent via WebSocket to server
3. **Database Store**: User message stored in database
4. **AI Processing**: Message sent to Claude AI for response
5. **AI Response**: Assistant response generated and stored
6. **WebSocket Broadcast**: Both messages broadcast to client
7. **UI Update**: Messages displayed in chat interface

## External Dependencies

### Core Dependencies
- **@anthropic-ai/sdk**: AI model integration
- **@neondatabase/serverless**: PostgreSQL database driver
- **drizzle-orm**: TypeScript ORM for database operations
- **@tanstack/react-query**: Server state management
- **@radix-ui/***: UI component primitives
- **tailwindcss**: Utility-first CSS framework

### Development Tools
- **vite**: Build tool and development server
- **typescript**: Type checking and compilation
- **drizzle-kit**: Database migration tool
- **esbuild**: Fast JavaScript bundler for production

## Deployment Strategy

### Development
- Vite development server for frontend hot reloading
- tsx for TypeScript execution in development
- WebSocket server runs alongside Express server
- In-memory storage fallback for quick setup

### Production
- Frontend built with Vite and served as static files
- Backend compiled with esbuild for optimized Node.js execution
- PostgreSQL database with proper connection pooling
- Environment variables for configuration (DATABASE_URL, ANTHROPIC_API_KEY)

### Build Process
1. `npm run build`: Builds frontend and backend for production
2. Frontend assets output to `dist/public`
3. Backend compiled to `dist/index.js`
4. Database migrations applied with `npm run db:push`

The architecture prioritizes real-time communication, type safety, and modern development practices while maintaining simplicity and performance.