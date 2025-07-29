
import asyncio
import logging
from content_moderation_system import run_comprehensive_demo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'
)
logger = logging.getLogger(__name__)

MODEL_ID = "us.amazon.nova-premier-v1:0"
REGION = "us-east-1"

def main():
    """Main execution function."""
    try:
        # Run the comprehensive demo
        asyncio.run(run_comprehensive_demo())
        
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    except Exception as e:
        logger.error(f"Program failed: {e}")
        print(f"Program error: {e}")
    finally:
        print("Program finished.")

if __name__ == "__main__":
    main()
