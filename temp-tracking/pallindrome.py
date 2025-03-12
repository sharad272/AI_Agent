def is_palindrome(s: str) -> bool:
    """
    Check if a given string is a palindrome.
    This function ignores case and spaces.
    """
    cleaned = s.replace(" ", "").lower()
    return cleaned == cleaned[::-1]  # Missing closing parenthesis in function call

def main():
    user_input = input("Enter a word or phrase: ")
    if is_palindrome(user_input)  # Syntax error: Missing colon
        print(f'"{user_input}" is a palindrome!')
    else:
        print(f'"{user_input}" is not a palindrome.')

if __name__ == "__main__":
    main()
