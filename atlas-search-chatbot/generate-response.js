import { getQueryResults } from './retrieve-documents.js';
import { Anthropic } from "@anthropic-ai/sdk";
import { GoogleGenAI } from '@google/genai';

// Configuration constants
const NUM_CANDIDATES = 40;
const EXACT = false;
const LIMIT = 5;

// Environment variables
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;

/**
 * Generate answer using Google's Gemini API
 * @param {string} prompt - The prompt to send to Gemini
 * @returns {Promise<string>} - The generated response
 */
async function generateWithGemini(prompt) {
  if (!GEMINI_API_KEY) {
    throw new Error('GEMINI_API_KEY environment variable is required');
  }

  const ai = new GoogleGenAI({ apiKey: GEMINI_API_KEY });
  
  try {
    const result = await ai.models.generateContent({
      model: 'gemini-2.5-pro', // or 'gemini-2.5-flash' for faster responses
      contents: prompt
    });
    
    return result.text || 'No response generated';
  } catch (error) {
    throw new Error(`Gemini API error: ${error.message}`);
  }
}

/**
 * Generate answer using Anthropic's Claude API
 * @param {string} prompt - The prompt to send to Claude
 * @returns {Promise<string>} - The generated response
 */
async function generateWithClaude(prompt) {
  if (!ANTHROPIC_API_KEY) {
    throw new Error('ANTHROPIC_API_KEY environment variable is required');
  }

  const anthropic = new Anthropic({
    apiKey: ANTHROPIC_API_KEY
  });

  try {
    const response = await anthropic.messages.create({
      model: "claude-sonnet-4-20250514", // or "claude-opus-4-20250514" for more advanced reasoning
      max_tokens: 1024,
      messages: [
        {
          role: 'user',
          content: [{ type: 'text', text: prompt }],
        },
      ],
    });

    return response.content[0].text || 'No response generated';
  } catch (error) {
    throw new Error(`Claude API error: ${error.message}`);
  }
}

/**
 * Create a well-structured prompt for RAG
 * @param {string} question - The user's question
 * @param {Array} documents - Retrieved documents for context
 * @returns {string} - Formatted prompt
 */
function createPrompt(question, documents) {
  const context = documents
    .map((doc, index) => `Document ${index + 1}: ${doc.text}`)
    .join('\n\n');

  return `You are provided with several document chunks as context to answer the question below.

Instructions:
- Use the provided context to answer the question as accurately as possible
- If the context is insufficient to fully answer the question, acknowledge this limitation
- If you need to supplement with general knowledge, clearly indicate what information comes from outside the provided context
- Be concise but comprehensive in your response

Context:
${context}

Question: ${question}

Answer:`;
}

/**
 * Main function to process question with specified AI provider
 * @param {string} question - The question to ask
 * @param {string} provider - Either 'gemini' or 'claude'
 */
async function processQuestion(question, provider = 'gemini') {
  console.log(`Processing question: "${question}"`);
  console.log(`Using provider: ${provider.toUpperCase()}\n`);

  try {
    // Retrieve relevant documents
    console.log('Retrieving relevant documents...');
    const documents = await getQueryResults(question, NUM_CANDIDATES, EXACT, LIMIT);
    
    console.log(`Retrieved ${documents.length} documents\n`);
    
    // Uncomment to see retrieved documents
    // console.log('Retrieved documents:', documents);

    // Create the prompt
    const prompt = createPrompt(question, documents);

    // Generate response based on provider
    let answer;
    switch (provider.toLowerCase()) {
      case 'gemini':
        answer = await generateWithGemini(prompt);
        break;
      case 'claude':
        answer = await generateWithClaude(prompt);
        break;
      default:
        throw new Error(`Unsupported provider: ${provider}. Use 'gemini' or 'claude'`);
    }

    console.log('Answer:');
    console.log('=' .repeat(50));
    console.log(answer);
    console.log('=' .repeat(50));

  } catch (error) {
    console.error('Error:', error.message);
    console.error('Stack trace:', error.stack);
  }
}

/**
 * Parse command line arguments
 * @returns {Object} - Parsed arguments
 */
function parseArgs() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.log(`
Usage: node script.js "<question>" [provider]

Arguments:
  question   - The question to ask (required, wrap in quotes)
  provider   - AI provider to use: 'gemini' or 'claude' (optional, default: 'gemini')

Examples:
  node script.js "What is SETI?"
  node script.js "What is machine learning?" claude
  node script.js "Explain quantum computing" gemini

Environment variables required:
  GEMINI_API_KEY     - For using Gemini
  ANTHROPIC_API_KEY  - For using Claude
    `);
    process.exit(1);
  }

  return {
    question: args[0],
    provider: args[1] || 'gemini'
  };
}

/**
 * Main execution function
 */
async function main() {
  const { question, provider } = parseArgs();
  
  // Validate environment variables based on provider
  if (provider.toLowerCase() === 'gemini' && !GEMINI_API_KEY) {
    console.error('Error: GEMINI_API_KEY environment variable is required for Gemini');
    process.exit(1);
  }
  
  if (provider.toLowerCase() === 'claude' && !ANTHROPIC_API_KEY) {
    console.error('Error: ANTHROPIC_API_KEY environment variable is required for Claude');
    process.exit(1);
  }

  await processQuestion(question, provider);
}

// Export functions for testing or module usage
export {
  generateWithGemini,
  generateWithClaude,
  processQuestion,
  createPrompt
};

// Run if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}