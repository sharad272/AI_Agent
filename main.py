import os
import logging
from services.query_service import QueryService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("\n=== AI Code Assistant ===")
    
    tracking_dir = os.path.join(os.getcwd(), "tracking-folder")
    if not os.path.exists(tracking_dir):
        os.makedirs(tracking_dir)
    
    try:
        query_service = QueryService(tracking_dir)
        files = os.listdir(tracking_dir)
        print(f"\nTracking folder contains: {len(files)} files")
        print("Ready for queries! (Type 'quit' to exit)")
        
        while True:
            query = input("\n> ").strip()
            if query.lower() == 'quit':
                break
                
            response = query_service.process_query(query)
            print(f"\nAnswer: {response.answer}")

    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()
