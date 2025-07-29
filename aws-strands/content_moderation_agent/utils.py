from pydantic import ValidationError
from strands import Agent
from strands.models import BedrockModel
from botocore.config import Config as BotocoreConfig
from botocore.exceptions import ClientError, BotoCoreError, NoCredentialsError
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MODEL_ID = "us.amazon.nova-premier-v1:0"
REGION = "us-east-1"

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