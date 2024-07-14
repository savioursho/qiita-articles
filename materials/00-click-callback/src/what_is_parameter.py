from pprint import pprint
from typing import Any

import click


def peak_param(
    ctx: click.Context,
    param: click.Parameter,
    value: Any,
):
    print("=" * 5, "(1)", "type of param", "=" * 5)
    print(type(param))
    print("is subclass?:", issubclass(type(param), click.Parameter))
    print()

    print("=" * 5, "(2)", "vars(param)", "=" * 5)
    pprint(vars(param))
    print()
    return value


import click


@click.command()
@click.option(
    "--count",
    default=1,
    help="Number of greetings.",
)
@click.option(
    "--name",
    default="World",
    help="The person to greet.",
    callback=peak_param,
)
def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    print("=" * 5, "outputs of hello()", "=" * 5)
    for _ in range(count):
        click.echo(f"Hello {name}!")


if __name__ == "__main__":
    hello()
