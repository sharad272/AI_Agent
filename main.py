import sys
import json
import os
from services.vscode_bridge import VSCodeBridge
from services.query_service import QueryService
from utils.code_processor import CodeProcessor
import logging

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Log to stdout for VSCode console
        logging.FileHandler('ai_assistant.log')  # Also log to file
    ]
)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("=== AI Code Assistant (VSCode) ===")
        logger.info("Initializing...")
        
        # Create temp directory for tracking
        temp_tracking_dir = os.path.join(os.getcwd(), "temp-tracking")
        if not os.path.exists(temp_tracking_dir):
            os.makedirs(temp_tracking_dir)
        logger.info(f"Created temp directory at: {temp_tracking_dir}")

        # Initialize bridge with all components
        bridge = VSCodeBridge()
        logger.info("VSCode bridge initialized")
        
        # Start handling input
        logger.info("Starting input handler...")
        bridge.handle_input()

    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise
    finally:
        if os.path.exists(temp_tracking_dir):
            import shutil
            shutil.rmtree(temp_tracking_dir)
            logger.info(f"Cleaned up temp directory: {temp_tracking_dir}")

if __name__ == "__main__":
    main()