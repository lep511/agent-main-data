# AI Chat Assistant with MCP Integration

A modern, real-time AI chat application powered by Anthropic's Claude AI and built with the Model Context Protocol (MCP). Features a React frontend with TypeScript and an Express.js backend, providing seamless WebSocket communication for instant messaging.

## Features

- **Real-time Chat**: WebSocket-powered instant messaging
- **AI Assistant**: Integration with Anthropic's Claude Sonnet 4 model
- **MCP Protocol**: Built with Model Context Protocol for enhanced AI capabilities
- **Modern UI**: Clean, responsive interface with message bubbles and typing indicators
- **Connection Management**: Automatic reconnection and connection status indicators
- **Message History**: Persistent conversation storage with in-memory database
- **TypeScript**: Full type safety across frontend and backend
- **Mobile Responsive**: Works seamlessly on desktop and mobile devices

## Tech Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development and optimized builds
- **Tailwind CSS** for modern styling
- **shadcn/ui** components built on Radix UI
- **TanStack Query** for server state management
- **Wouter** for lightweight routing

### Backend
- **Node.js** with Express.js
- **WebSocket** for real-time communication
- **Anthropic SDK** for AI integration
- **Drizzle ORM** with PostgreSQL schema
- **In-memory storage** for development

## Getting Started

### Prerequisites

- Node.js 20 or later
- npm or yarn package manager
- Anthropic API key (get one at [console.anthropic.com](https://console.anthropic.com))

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ai-chat-assistant
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up environment variables:
   ```bash
   # Create .env file
   echo "ANTHROPIC_API_KEY=your_anthropic_api_key_here" > .env
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```

5. Open your browser and navigate to `http://localhost:5000`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key for Claude AI | Yes |
| `PORT` | Server port (default: 5000) | No |
| `NODE_ENV` | Environment mode (development/production) | No |

## API Endpoints

### REST API
- `POST /api/conversations` - Create a new conversation
- `GET /api/conversations/:id/messages` - Get messages for a conversation

### WebSocket
- `ws://localhost:5000/ws` - Real-time chat connection
- Message format: `{ type: 'chat_message', conversationId: number, content: string }`

## Architecture

### Database Schema
```sql
-- Users table
users (id, username, password)

-- Conversations table
conversations (id, user_id, title, created_at)

-- Messages table
messages (id, conversation_id, role, content, timestamp)
```

### Data Flow
1. User sends message via WebSocket
2. Message stored in database
3. Message sent to Claude AI for processing
4. AI response generated and stored
5. Both messages broadcast to all connected clients
6. UI updates with new messages

## Development

### File Structure
```
├── client/                 # React frontend
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── pages/         # Page components
│   │   └── lib/           # Utility functions
├── server/                # Express backend
│   ├── services/          # Business logic
│   ├── index.ts           # Server entry point
│   ├── routes.ts          # API routes
│   └── storage.ts         # Database interface
├── shared/                # Shared types and schemas
└── package.json
```

### Key Components

#### Frontend
- `useWebSocket` - Custom hook for WebSocket connection management
- `ChatHeader` - Connection status and branding
- `ChatMessages` - Message display with loading states
- `ChatInput` - Message input with validation
- `MessageBubble` - Individual message styling

#### Backend
- `registerRoutes` - API endpoints and WebSocket setup
- `generateAIResponse` - Claude AI integration
- `MemStorage` - In-memory database implementation

### Scripts

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Database operations
npm run db:generate    # Generate database migrations
npm run db:migrate     # Run migrations
npm run db:push        # Push schema to database
```

## Deployment

### Production Build
```bash
npm run build
npm start
```

### Environment Setup
Ensure these environment variables are set in production:
- `ANTHROPIC_API_KEY` - Your Anthropic API key
- `PORT` - Server port (usually provided by hosting platform)
- `NODE_ENV=production`

### Hosting Recommendations
- **Replit** - Easy deployment with built-in environment management
- **Vercel** - Serverless deployment for frontend + API
- **Railway** - Simple full-stack deployment
- **Heroku** - Traditional cloud hosting

## Features in Detail

### Real-time Communication
- WebSocket connection with automatic reconnection
- Message broadcasting to all connected clients
- Connection status indicators
- Typing indicators and loading states

### AI Integration
- Claude Sonnet 4 model for intelligent responses
- Conversation context management (last 10 messages)
- Error handling and fallback responses
- System prompts for assistant behavior

### User Experience
- Mobile-responsive design
- Message timestamps and read indicators
- Smooth animations and transitions
- Keyboard shortcuts (Enter to send, Shift+Enter for new line)

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/new-feature`
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Check the [Issues](../../issues) section
- Review the documentation above
- Ensure your API key is properly configured

---

Built with ❤️ using modern web technologies and powered by Anthropic's Claude AI.