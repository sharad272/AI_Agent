import os
import logging

# Configure logging once at program start
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    print("\n=== AI Code Assistant (Optimized) ===")
    
    tracking_dir = os.path.join(os.getcwd(), "tracking-folder")
    if not os.path.exists(tracking_dir):
        os.makedirs(tracking_dir)
    
    try:
        print("Initializing (this might take a moment)...")
        from services.query_service import QueryService
        query_service = QueryService(tracking_dir)
        files = os.listdir(tracking_dir)
        print(f"Ready! Tracking folder contains: {len(files)} files")
        
        while True:
            query = input("\n> ").strip()
            if query.lower() == 'quit':
                break
            
            response = query_service.process_query(query)
            print(f"\nAnswer: {response.answer}")
            if response.relevant_files:
                print(f"Referenced files: {', '.join(response.relevant_files)}")

    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()