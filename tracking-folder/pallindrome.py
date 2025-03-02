def is_palindrome(text):
    # Remove spaces and convert to lowercase
    text = text.lower().replace(" ", "")
    # Compare string with its reverse
    return text == text[::-1]

def main():
    # Get input from user
    text = input("Enter a string to check if it's a palindrome: ")
    
    # Check if it's a palindrome
    if is_palindrome(text):
        print(f"'{text}' is a palindrome!")
    else:
        print(f"'{text}' is not a palindrome.")

if __name__ == "__main__":
    main()