import os
import argparse
from dotenv import load_dotenv
from typing import Optional
from google_mb_lib import (
    create_agent_engine,
    create_memory_bank,
    get_memory_bank,
    semantic_memory_search
)
import vertexai

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Google Cloud Agent Memory Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run memory/google_mb.py --create-agent
  uv run memory/google_mb.py --create-memory --user-id user123 --fact "User lives in New York" --engine-id $ENGINE_ID
  uv run memory/google_mb.py --get-memory --user-id user123 --engine-id $ENGINE_ID
  uv run memory/google_mb.py --search --user-id user123 --query "What is my city?" --engine-id $ENGINE_ID
"""
    )
    
    # Main actions (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        '--create-agent',
        action='store_true',
        help='Create a new agent engine'
    )
    action_group.add_argument(
        '--create-memory',
        action='store_true',
        help='Create a memory bank for a user'
    )
    action_group.add_argument(
        '--get-memory',
        action='store_true',
        help='Retrieve all memories for a user'
    )
    action_group.add_argument(
        '--search',
        action='store_true',
        help='Perform semantic search on user memories'
    )
    
    # Optional arguments
    parser.add_argument(
        '--user-id',
        type=str,
        help='User ID for memory operations'
    )
    parser.add_argument(
        '--engine-id',
        type=str,
        help='Agent engine ID (required for memory operations)',
    )
    parser.add_argument(
        '--query',
        type=str,
        help='Search query for semantic memory search'
    )
    parser.add_argument(
        '--fact',
        type=str,
        help='Custom fact to store in memory (optional for --create-memory)'
    )
    
    return parser.parse_args()

def main():
    """Main function that handles command line arguments"""
    args = parse_arguments()

    try:
        if args.create_agent:
            print("Creating new agent engine...")
            agent_engine_id = create_agent_engine()
            if agent_engine_id:
                print(f"✅ Agent Engine created successfully!")
                print(f"✅ Agent Engine ID: {agent_engine_id}")
            else:
                print("❌ Failed to create agent engine")
                return 1
        
        elif args.create_memory:
            if not args.user_id:
                print("❌ Error: --user-id is required for --create-memory")
                return 1

            if not args.engine_id:
                print("❌ Error: No agent engine ID provided. Use --engine-id")
                return 1
            
            if not args.fact:
                print("❌ Error: --fact is required for --create-memory")
                return 1
            
            print(f"Creating memory for user: {args.user_id}")
            memory_name = create_memory_bank(args.engine_id, args.user_id, args.fact)

            if memory_name:
                print(f"✅ Memory created successfully!")
                print(f"Memory name: {memory_name}")
            else:
                print("❌ Failed to create memory")
                return 1
        
        elif args.get_memory:
            if not args.user_id:
                print("❌ Error: --user-id is required for --get-memory")
                return 1

            if not args.engine_id:
                print("❌ Error: No agent engine ID provided. Use --engine-id")
                return 1
            
            print(f"Retrieving memories for user: {args.user_id}")
            memory = get_memory_bank(args.engine_id, args.user_id)
            
            if memory:
                print(f"✅ Memories found:")
                print(f"\nMemory Bank for {args.user_id}:")
                print(memory)
            else:
                print("📭 No memories found for this user")
        
        elif args.search:
            if not args.user_id:
                print("❌ Error: --user-id is required for --search")
                return 1
            if not args.query:
                print("❌ Error: --query is required for --search")
                return 1

            if not args.engine_id:
                print("❌ Error: No agent engine ID provided. Use --engine-id")
                return 1
            
            print(f"Searching memories for user: {args.user_id}")
            print(f"Query: {args.query}")
            relevant_memories = semantic_memory_search(args.engine_id, args.user_id, args.query)

            if relevant_memories:
                print(f"✅ Relevant memories found:")
                print(f"\nRelevant Memories for query '{args.query}':")
                print(relevant_memories)
            else:
                print("📭 No relevant memories found for this query")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)

    # agent_engine_id = create_agent_engine()
    # print(f"\nAgent Engine ID: {agent_engine_id}")

    user_id = "user_3002b2a1-9e05-481c-a6a9-c12326cbc718"
    agent_engine_id = GOOGLE_AGENT_MEMORY

    fact = f"The user's name is {user_id} and they have a passion for learning new things."
    memory_name = create_memory_bank(agent_engine_id, fact, user_id)

    if not memory_name:
        raise Exception("Failed to create memory bank.")
    
    print(f"Memory created with name: {memory_name}")
    
    memory = get_memory_bank(agent_engine_id, user_id)
    print(f"\nMemory Bank for {user_id}:\n{memory if memory else 'No memories found.'}")
    
    # query = "What is my city of born?"
    # relevant_memories = semantic_memory_search(agent_engine_id, user_id, query)
    # print(f"\nRelevant Memories for query '{query}':\n{relevant_memories if relevant_memories else 'No relevant memories found.'}")

