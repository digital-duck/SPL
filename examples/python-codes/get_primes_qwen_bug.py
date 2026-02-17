import click

def sieve_of_eratosthenes(n):
    """
    Efficiently find all prime numbers less than n using the Sieve of Eratosthenes algorithm.

    :param n: Upper limit (exclusive) to find prime numbers.
    :return: List of prime numbers less than n.
    """
    if n <= 2:
        return []

    # Initialize a boolean array that indicates whether each number is prime
    is_prime = [True] * n
    is_prime[0] = is_prime[1] = False  # 0 and 1 are not prime numbers

    # Start with the first prime number, which is 2
    for start in range(2, int(n**0.5) + 1):
        if is_prime[start]:
            # Mark all multiples of start as non-prime
            for multiple in range(start*start, n, start):
                is_prime[multiple] = False

    # Extract the list of primes
    primes = [num for num, prime in enumerate(is_prime) if prime]
    return primes

@click.command()
@click.argument('n', type=int, required=True, help='The upper limit (exclusive) to find prime numbers.')
@click.option('--format', '-f', type=click.Choice(['list', 'count', 'range'], case_sensitive=False), default='list',
              help='Output format: list of primes, count of primes, or range of primes.')
def find_primes(n, format):
    """
    Find and display all prime numbers less than a given number N.

    \b
    Examples:
    $ python primes.py 10
    [2, 3, 5, 7]

    $ python primes.py 20 --format=count
    8

    $ python primes.py 30 --format=range
    2-29
    """
    # Validate input
    if n < 0:
        click.echo("Error: N must be a non-negative integer.", err=True)
        return

    # Find primes using the Sieve of Eratosthenes
    primes = sieve_of_eratosthenes(n)

    # Handle different output formats
    if format == 'list':
        click.echo(primes)
    elif format == 'count':
        click.echo(len(primes))
    elif format == 'range':
        if primes:
            click.echo(f"{primes[0]}-{primes[-1]}")
        else:
            click.echo("No primes found.")

if __name__ == '__main__':
    find_primes()