import ollama

def test_ollama():
    try:
        print("Testing Ollama connection...")
        response = ollama.generate(
            model='deepseek-r1:1.5b',
            prompt='Write a simple hello world program in Python',
            options={
                "temperature": 0.7,
                "num_predict": 1000,
            }
           
        )
        print("\nResponse from Ollama:")
        print(response['response'])
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    print(test_ollama())
