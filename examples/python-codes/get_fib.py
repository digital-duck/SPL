import click

def fibonacci_up_to(m):
    """Generate Fibonacci numbers less than or equal to m."""
    a, b = 0, 1
    while a <= m:
        yield a
        a, b = b, a + b

@click.command()
@click.argument('M', type=int)
def fibonacci(m):
    """Calculate and display all Fibonacci numbers less than M."""
    if m < 0:
        click.echo("Error: M must be a non-negative integer.")
        return

    if m == 0:
        click.echo("No Fibonacci numbers to display for M = 0.")
        return

    fib_numbers = list(fibonacci_up_to(m))
    click.echo(f"Fibonacci numbers less than {m}: {', '.join(map(str, fib_numbers))}")

if __name__ == '__main__':
    fibonacci()