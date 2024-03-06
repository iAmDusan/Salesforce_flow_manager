import numpy as np
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display, clear_output

# Functions to represent
def constant(n: int) -> int:
    return [1 for _ in range(n)]

def logarithmic(n: int) -> list:
    return [np.log(i) if i > 0 else 0 for i in range(n)]

def linear(n: int) -> list:
    return [i for i in range(n)]

def linear_log(n: int) -> list:
    return [i * np.log(i) if i > 0 else 0 for i in range(n)]

def quadratic(n: int) -> list:
    return [i ** 2 for i in range(n)]

def cubic(n: int) -> list:
    return [i ** 3 for i in range(n)]

def exponential(n: int) -> list:
    return [2 ** i for i in range(n)]

def factorial(n: int) -> list:
    if n == 0:
        return [1]
    values = [1]
    val = 1
    for i in range(1, n):
        val *= i
        values.append(val)
    return values

# Fibonacci using recursive method (exponential time)
def fibonacci_recursive(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)

# Fibonacci using iterative method (linear time)
def fibonacci_iterative(n: int) -> int:
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n+1):
        a, b = b, a + b
    return b


# Updated plotting function without the recursive Fibonacci curve
def plot_functions_without_recursive_fib(n: int):
    x = list(range(n))
    
    plt.figure(figsize=(12, 8))

    plt.plot(x, constant(n), label="O(1) - Constant")
    plt.plot(x, logarithmic(n), label="O(log n) - Logarithmic")
    plt.plot(x, linear(n), label="O(n) - Linear")
    plt.plot(x, linear_log(n), label="O(n log n) - Linear Logarithmic")
    plt.plot(x, quadratic(n), label="O(n^2) - Quadratic")
    plt.plot(x, cubic(n), label="O(n^3) - Cubic")
    
    # Only include the iterative Fibonacci sequence
    fib_iterative = [fibonacci_iterative(i) for i in x]
    plt.plot(x, fib_iterative, label="Fibonacci Iterative (O(n))", linestyle='dashdot')

    # The factorial growth is too fast, so we'll plot it separately for smaller n values
    if n <= 20:
        plt.plot(x, factorial(n), label="O(n!) - Factorial")

    plt.xlabel('Input Size (n)')
    plt.ylabel('Operations (time or space)')
    plt.title('Big O Notation (Without Recursive Fibonacci)')
    plt.legend()
    plt.grid(True)
    plt.show()


def interactive_plot(n: int):
    plot_functions_without_recursive_fib(n)
    plt.show()

widgets.interactive(interactive_plot, n=widgets.IntSlider(min=5, max=100, step=5, value=30, description='Input Size:'))