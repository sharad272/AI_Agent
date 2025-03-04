def factorial(n):
    """Calculate factorial using recursion"""
    if n <= 1:
        return 1
    return n * factorial(n-1)

def fibonacci(n):
    """Calculate Fibonacci number using recursion"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def sum_array(arr):
    """Sum array elements using recursion"""
    if len(arr) == 0:
        return 0
    return arr[0] + sum_array(arr[1:])

def reverse_string(s):
    """Reverse a string using recursion"""
    if len(s) <= 1:
        return s
    return reverse_string(s[1:]) + s[0]

# Example usage
if __name__ == "__main__":
    print(f"Factorial of 5: {factorial(5)}")
    print(f"Fibonacci of 6: {fibonacci(6)}")
    print(f"Sum of array [1,2,3,4,5]: {sum_array([1,2,3,4,5])}")
    print(f"Reverse of 'hello': {reverse_string('hello')}")