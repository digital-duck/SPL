#!/usr/bin/env python3
"""
Prime Number Finder CLI Tool

A high-performance command-line tool for finding prime numbers using the
Sieve of Eratosthenes algorithm. Supports multiple output formats and
handles edge cases gracefully.

Usage Examples:
    python prime_finder.py 100
    python prime_finder.py 1000 --format count
    python prime_finder.py 50 --format range --verbose
"""

import click
import sys
import time
from typing import List, Tuple


def sieve_of_eratosthenes(n: int) -> List[int]:
    """
    Implement the Sieve of Eratosthenes algorithm to find all prime numbers less than n.

    This is one of the most efficient algorithms for finding all primes up to a given limit.
    Time complexity: O(n log log n)
    Space complexity: O(n)

    Args:
        n (int): Upper limit (exclusive) for finding primes

    Returns:
        List[int]: List of all prime numbers less than n

    Algorithm explanation:
        1. Create a boolean array "prime[0..n-1]" and initialize all entries as True
        2. Start with the first prime number, 2
        3. Mark all multiples of 2 (except 2 itself) as composite
        4. Find the next number that hasn't been marked and repeat
        5. Continue until we've processed all numbers up to √n
    """
    if n <= 2:
        return []

    # Initialize boolean array - True means "potentially prime"
    is_prime = [True] * n
    is_prime[0] = is_prime[1] = False  # 0 and 1 are not prime

    # Sieve algorithm: mark multiples of each prime as composite
    p = 2
    while p * p < n:  # Only need to check up to √n
        if is_prime[p]:
            # Mark all multiples of p starting from p²
            # (smaller multiples already marked by smaller primes)
            for i in range(p * p, n, p):
                is_prime[i] = False
        p += 1

    # Collect all numbers that remain marked as prime
    return [i for i in range(2, n) if is_prime[i]]


def format_primes_list(primes: List[int], verbose: bool = False) -> str:
    """Format primes as a readable list."""
    if not primes:
        return "No prime numbers found in the given range."

    if verbose:
        # Display in columns for better readability
        primes_str = []
        for i, prime in enumerate(primes):
            if i % 10 == 0 and i > 0:
                primes_str.append('\n')
            primes_str.append(f"{prime:>4}")

        result = "Prime numbers found:"
        result += "\n" + "".join(primes_str)
        return result
    else:
        return ", ".join(map(str, primes))


def format_primes_count(primes: List[int]) -> str:
    """Format primes as count only."""
    count = len(primes)
    if count == 0:
        return "No prime numbers found in the given range."
    elif count == 1:
        return f"Found 1 prime number: {primes[0]}"
    else:
        return f"Found {count} prime numbers (largest: {primes[-1]})"


def format_primes_range(primes: List[int]) -> str:
    """Format primes showing range information."""
    if not primes:
        return "No prime numbers found in the given range."

    count = len(primes)
    smallest = primes[0]
    largest = primes[-1]

    result = f"Prime number summary:\n"
    result += f"  Count: {count}\n"
    result += f"  Range: {smallest} to {largest}\n"
    result += f"  Density: {count/largest*100:.2f}% of numbers in range are prime"

    return result


class ClickIntRange(click.ParamType):
    """Custom Click parameter type for positive integers with better error messages."""

    name = "positive_integer"

    def convert(self, value, param, ctx):
        try:
            int_value = int(value)
            if int_value < 0:
                self.fail(f"Number must be non-negative, got {int_value}", param, ctx)
            return int_value
        except ValueError:
            self.fail(f"'{value}' is not a valid integer", param, ctx)


@click.command()
@click.argument('n', type=ClickIntRange(), metavar='N')
@click.option(
    '--format', 'output_format',
    type=click.Choice(['list', 'count', 'range'], case_sensitive=False),
    default='list',
    help='Output format: list (default), count (count only), or range (summary)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output with performance metrics and formatted display'
)
@click.option(
    '--performance', '-p',
    is_flag=True,
    help='Show detailed performance metrics (execution time, memory usage estimates)'
)
@click.version_option(version='1.0.0', prog_name='Prime Finder')
def find_primes(n: int, output_format: str, verbose: bool, performance: bool) -> None:
    """
    Find and display all prime numbers less than N using the Sieve of Eratosthenes.

    This tool efficiently finds prime numbers using one of the most optimal algorithms
    available. It can handle large values of N with good performance characteristics.

    \b
    Arguments:
        N    Upper limit (exclusive) for finding primes. Must be a non-negative integer.

    \b
    Examples:
        python prime_finder.py 30
        python prime_finder.py 1000 --format count --verbose
        python prime_finder.py 100 --format range
        python prime_finder.py 10000 -p

    \b
    Performance Notes:
        - Time complexity: O(N log log N)
        - Space complexity: O(N)
        - Efficient for N up to ~10^7 on typical hardware
        - For N > 10^8, consider using segmented sieve variants
    """

    # Handle edge cases with informative messages
    if n == 0:
        click.echo("N=0: No numbers to check for primality.")
        return
    elif n == 1:
        click.echo("N=1: No prime numbers exist below 1.")
        return
    elif n == 2:
        click.echo("N=2: No prime numbers exist below 2.")
        return

    # Performance tracking
    start_time = time.time()

    # Warn for very large N values
    if n > 10_000_000:  # 10 million
        if not click.confirm(
            f"N={n:,} is quite large and may take significant time/memory. Continue?",
            default=True
        ):
            click.echo("Operation cancelled.")
            return

    try:
        # Find primes using Sieve of Eratosthenes
        if verbose:
            click.echo(f"Finding prime numbers less than {n:,}...")
            click.echo("Using Sieve of Eratosthenes algorithm...")

        primes = sieve_of_eratosthenes(n)

        # Calculate performance metrics
        end_time = time.time()
        execution_time = end_time - start_time

        # Format and display results
        if output_format.lower() == 'list':
            result = format_primes_list(primes, verbose)
        elif output_format.lower() == 'count':
            result = format_primes_count(primes)
        elif output_format.lower() == 'range':
            result = format_primes_range(primes)

        click.echo(result)

        # Show performance metrics if requested
        if performance or verbose:
            click.echo(f"\nPerformance Metrics:")
            click.echo(f"  Execution time: {execution_time:.4f} seconds")
            click.echo(f"  Numbers processed: {n:,}")
            click.echo(f"  Primes found: {len(primes):,}")
            click.echo(f"  Processing rate: {n/execution_time:,.0f} numbers/second")

            # Estimate memory usage (rough approximation)
            memory_mb = (n * 1) / (1024 * 1024)  # 1 byte per boolean in sieve
            click.echo(f"  Estimated peak memory: {memory_mb:.2f} MB")

    except MemoryError:
        click.echo(
            f"Error: Not enough memory to process N={n:,}. "
            f"Try a smaller value or use a segmented sieve implementation.",
            err=True
        )
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nOperation interrupted by user.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    find_primes()