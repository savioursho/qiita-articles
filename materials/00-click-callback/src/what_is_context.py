from pprint import pprint
from typing import Any

import click


def peak_ctx(
    ctx: click.Context,
    param: click.Parameter,
    value: Any,
):
    print("=" * 5, "(1)", "type of ctx", "=" * 5)
    print(type(ctx))
    print()

    print("=" * 5, "(2)", "vars(ctx)", "=" * 5)
    pprint(vars(ctx))
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
    callback=peak_ctx,
)
def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    print("=" * 5, "outputs of hello()", "=" * 5)
    for _ in range(count):
        click.echo(f"Hello {name}!")


if __name__ == "__main__":
    hello()
