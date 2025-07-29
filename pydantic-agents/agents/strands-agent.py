#!/usr/bin/env python3
"""
Structured Output Example with Comprehensive Error Handling

This example demonstrates how to use structured output with Strands Agents to
get type-safe, validated responses using Pydantic models with robust error handling.
"""
import asyncio
import logging
import tempfile
from typing import List, Optional
from pydantic import BaseModel, Field, ValidationError
from strands import Agent
from strands.models import BedrockModel
from botocore.config import Config as BotocoreConfig
from botocore.exceptions import ClientError, BotoCoreError, NoCredentialsError
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MODEL_ID = "us.amazon.nova-premier-v1:0"
REGION = "us-east-1"

class StructuredOutputError(Exception):
    """Custom exception for structured output operations."""
    pass

class ModelConfigurationError(Exception):
    """Custom exception for model configuration issues."""
    pass

def create_bedrock_model() -> BedrockModel:
    """
    Create a configured Bedrock model with error handling.
    
    Returns:
        BedrockModel: Configured Bedrock model instance
        
    Raises:
        ModelConfigurationError: If model configuration fails
        NoCredentialsError: If AWS credentials are not available
    """
    try:
        # Check for required environment variables or AWS credentials
        if not any([
            os.getenv('AWS_ACCESS_KEY_ID'),
            os.getenv('AWS_PROFILE'),
            # Add other credential sources as needed
        ]):
            logger.warning("No AWS credentials found in environment variables")
        
        # Create a boto client config with custom settings
        boto_config = BotocoreConfig(
            retries={"max_attempts": 3, "mode": "adaptive"},
            connect_timeout=10,  # Increased timeout
            read_timeout=120,    # Increased timeout
            max_pool_connections=10
        )

        # Create a configured Bedrock model
        bedrock_model = BedrockModel(
            model_id=MODEL_ID,
            region_name=REGION,
            boto_client_config=boto_config,
        )
        
        logger.info(f"Successfully configured Bedrock model: {MODEL_ID}")
        return bedrock_model
        
    except NoCredentialsError as e:
        logger.error(f"AWS credentials not found: {e}")
        raise ModelConfigurationError(f"AWS credentials not configured: {e}")
    except ClientError as e:
        logger.error(f"AWS client error during model configuration: {e}")
        raise ModelConfigurationError(f"Failed to configure AWS client: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during model configuration: {e}")
        raise ModelConfigurationError(f"Unexpected configuration error: {e}")

def safe_structured_output(agent: Agent, model_class, prompt: str, max_retries: int = 3):
    """
    Safely execute structured output with retry logic and error handling.
    
    Args:
        agent: The Strands agent instance
        model_class: Pydantic model class for structured output
        prompt: Input prompt string
        max_retries: Maximum number of retry attempts
        
    Returns:
        Structured output instance or None if failed
        
    Raises:
        StructuredOutputError: If all retry attempts fail
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting structured output (attempt {attempt + 1}/{max_retries})")
            result = agent.structured_output(model_class, prompt)
            logger.info("Structured output successful")
            return result
            
        except ValidationError as e:
            logger.error(f"Pydantic validation error on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                raise StructuredOutputError(f"Validation failed after {max_retries} attempts: {e}")
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"AWS client error on attempt {attempt + 1}: {error_code} - {e}")
            
            # Don't retry on certain error types
            if error_code in ['InvalidRequestException', 'AccessDeniedException']:
                raise StructuredOutputError(f"Non-retryable AWS error: {e}")
                
            if attempt == max_retries - 1:
                raise StructuredOutputError(f"AWS client error after {max_retries} attempts: {e}")
                
        except BotoCoreError as e:
            logger.error(f"Boto core error on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                raise StructuredOutputError(f"Boto core error after {max_retries} attempts: {e}")
                
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                raise StructuredOutputError(f"Unexpected error after {max_retries} attempts: {e}")
        
        # Wait before retry (exponential backoff)
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt
            logger.info(f"Waiting {wait_time} seconds before retry")
            import time
            time.sleep(wait_time)

def basic_example():
    """Basic example extracting structured information from text with error handling."""
    print("\n--- Basic Example ---")
    
    class PersonInfo(BaseModel):
        name: str
        age: int
        occupation: str

    try:
        bedrock_model = create_bedrock_model()
        agent = Agent(model=bedrock_model)
        
        result = safe_structured_output(
            agent,
            PersonInfo,
            "John Smith is a 30-year-old software engineer"
        )
        
        if result:
            print(f"Name: {result.name}")
            print(f"Age: {result.age}")
            print(f"Job: {result.occupation}")
        else:
            print("Failed to extract structured information")
            
    except (ModelConfigurationError, StructuredOutputError) as e:
        logger.error(f"Basic example failed: {e}")
        print(f"Error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in basic example: {e}")
        print(f"Unexpected error: {e}")

def multimodal_example():
    """Multi-modal example with comprehensive error handling."""
    print("\n--- Multi-Modal Example ---")

    class PersonInfo(BaseModel):
        name: str
        age: int
        occupation: str

    try:
        # Create temporary file with error handling
        with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as person_file:
            try:
                content = b"John Smith is a 30-year old software engineer"
                person_file.write(content)
                person_file.flush()
                temp_file_path = person_file.name
                
            except IOError as e:
                logger.error(f"Failed to write temporary file: {e}")
                raise StructuredOutputError(f"Temporary file creation failed: {e}")

        try:
            # Read file with error handling
            with open(temp_file_path, "rb") as fp:
                document_bytes = fp.read()
                
            if not document_bytes:
                raise StructuredOutputError("Document file is empty")
                
        except IOError as e:
            logger.error(f"Failed to read temporary file: {e}")
            raise StructuredOutputError(f"File reading failed: {e}")
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except OSError as e:
                logger.warning(f"Failed to delete temporary file: {e}")

        bedrock_model = create_bedrock_model()
        agent = Agent(model=bedrock_model)

        # Validate document structure before sending
        message_content = [
            {"text": "Please process this application."},
            {
                "document": {
                    "format": "txt",
                    "name": "application",
                    "source": {
                        "bytes": document_bytes,
                    },
                },
            },
        ]

        result = safe_structured_output(agent, PersonInfo, message_content)
        
        if result:
            print(f"Name: {result.name}")
            print(f"Age: {result.age}")
            print(f"Job: {result.occupation}")
        else:
            print("Failed to extract structured information from document")
            
    except (ModelConfigurationError, StructuredOutputError) as e:
        logger.error(f"Multimodal example failed: {e}")
        print(f"Error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in multimodal example: {e}")
        print(f"Unexpected error: {e}")

def conversation_history_example():
    """Example using conversation history with structured output and error handling."""
    print("\n--- Conversation History Example ---")

    class CityInfo(BaseModel):
        city: str
        country: str
        population: Optional[int] = None
        climate: str

    try:
        bedrock_model = create_bedrock_model()
        agent = Agent(model=bedrock_model)

        # Build up conversation context with error handling
        print("Building conversation context...")
        conversation_prompts = [
            "What do you know about Paris, France?",
            "Tell me about the weather there in spring.",
            "What is the population of Paris?"
        ]
        
        for i, prompt in enumerate(conversation_prompts):
            try:
                logger.info(f"Conversation step {i+1}: {prompt}")
                response = agent(prompt)
                if not response:
                    logger.warning(f"Empty response for prompt: {prompt}")
            except Exception as e:
                logger.error(f"Failed conversation step {i+1}: {e}")
                # Continue with remaining conversation steps
                continue

        # Extract structured information with error handling
        print("Extracting structured information from conversation context...")
        result = safe_structured_output(
            agent, 
            CityInfo, 
            "Extract structured information about Paris based on our conversation"
        )

        if result:
            print(f"City: {result.city}")
            print(f"Country: {result.country}")
            print(f"Population: {result.population}")
            print(f"Climate: {result.climate}")
        else:
            print("Failed to extract structured city information")
            
    except (ModelConfigurationError, StructuredOutputError) as e:
        logger.error(f"Conversation history example failed: {e}")
        print(f"Error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in conversation history example: {e}")
        print(f"Unexpected error: {e}")

def complex_nested_model_example():
    """Example handling complex nested data structures with comprehensive validation."""
    print("\n--- Complex Nested Model Example ---")

    class Address(BaseModel):
        street: str
        city: str
        country: str
        postal_code: Optional[str] = None

    class Contact(BaseModel):
        email: Optional[str] = None
        phone: Optional[str] = None

    class Person(BaseModel):
        """Complete person information with validation."""
        name: str = Field(description="Full name of the person", min_length=1)
        age: int = Field(description="Age in years", ge=0, le=150)
        address: Address = Field(description="Home address")
        contacts: List[Contact] = Field(default_factory=list, description="Contact methods")
        skills: List[str] = Field(default_factory=list, description="Professional skills")

    try:
        bedrock_model = create_bedrock_model()
        agent = Agent(model=bedrock_model)

        result = safe_structured_output(
            agent,
            Person,
            "Extract info: Jane Doe, a systems admin, 28, lives at 123 Main St, New York, USA. Email: jane@example.com"
        )

        if result:
            print(f"Name: {result.name}")
            print(f"Age: {result.age}")
            print(f"Street: {result.address.street}")
            print(f"City: {result.address.city}")
            print(f"Country: {result.address.country}")
            
            if result.contacts:
                print(f"Email: {result.contacts[0].email if result.contacts[0].email else 'N/A'}")
            else:
                print("Email: No contacts found")
                
            print(f"Skills: {result.skills}")
        else:
            print("Failed to extract complex structured information")
            
    except (ModelConfigurationError, StructuredOutputError) as e:
        logger.error(f"Complex nested model example failed: {e}")
        print(f"Error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in complex nested model example: {e}")
        print(f"Unexpected error: {e}")

async def async_example():
    """Async example with comprehensive error handling."""
    print("\n--- Async Example ---")

    class PersonInfo(BaseModel):
        name: str
        age: int
        occupation: str

    try:
        bedrock_model = create_bedrock_model()
        agent = Agent(model=bedrock_model)

        # Async version of safe structured output
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Async attempt {attempt + 1}/{max_retries}")
                result = await agent.structured_output_async(
                    PersonInfo,
                    "John Smith is a 30-year-old software engineer"
                )
                
                if result:
                    print(f"Name: {result.name}")
                    print(f"Age: {result.age}")
                    print(f"Job: {result.occupation}")
                break
                
            except ValidationError as e:
                logger.error(f"Async validation error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise StructuredOutputError(f"Async validation failed: {e}")
                    
            except (ClientError, BotoCoreError) as e:
                logger.error(f"Async AWS error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise StructuredOutputError(f"Async AWS error: {e}")
                    
            except Exception as e:
                logger.error(f"Unexpected async error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise StructuredOutputError(f"Unexpected async error: {e}")
            
            # Exponential backoff for async retries
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Async waiting {wait_time} seconds before retry")
                await asyncio.sleep(wait_time)
                
    except (ModelConfigurationError, StructuredOutputError) as e:
        logger.error(f"Async example failed: {e}")
        print(f"Error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in async example: {e}")
        print(f"Unexpected error: {e}")

def run_examples_safely():
    """Run all examples with comprehensive error handling."""
    examples = [
        ("Basic Example", basic_example),
        ("Multimodal Example", multimodal_example),
        ("Conversation History Example", conversation_history_example),
        ("Complex Nested Model Example", complex_nested_model_example),
    ]
    
    successful_examples = 0
    
    for name, example_func in examples:
        try:
            logger.info(f"Running {name}")
            example_func()
            successful_examples += 1
            logger.info(f"{name} completed successfully")
        except Exception as e:
            logger.error(f"{name} failed with error: {e}")
            print(f"\n{name} failed: {e}")
    
    print(f"\nCompleted {successful_examples}/{len(examples)} examples successfully")
    
    # Run async example separately
    try:
        logger.info("Running Async Example")
        asyncio.run(async_example())
        successful_examples += 1
        logger.info("Async Example completed successfully")
    except Exception as e:
        logger.error(f"Async Example failed with error: {e}")
        print(f"\nAsync Example failed: {e}")
    
    print(f"Total: {successful_examples}/{len(examples) + 1} examples completed successfully")

if __name__ == "__main__":
    print("Structured Output Examples with Error Handling\n")
    
    try:
        run_examples_safely()
    except KeyboardInterrupt:
        logger.info("Examples interrupted by user")
        print("\nExecution interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\nFatal error: {e}")
    finally:
        print("\nExecution completed.")