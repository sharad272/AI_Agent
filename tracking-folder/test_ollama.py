import ollama

def test_ollama():
    try:
        print("Testing Ollama connection...")
        response = ollama.chat(
            model='deepseek-r1:1.5b',
            messages=[
                {
                    "role": "user",
                    "content": "Write a simple hello world program in Python"
                }
            ],
            stream=True
        )
        
        print("\nResponse from Ollama:")
        full_response = []
        for chunk in response:
            if 'message' in chunk:
                text = chunk['message']['content']
                print(text, end='', flush=True)
                full_response.append(text)
        print()  # Add final newline
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_ollama()  # Removed extra print since function already prints
