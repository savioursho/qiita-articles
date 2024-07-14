from typing import Any

import click


class MyParamType(click.ParamType):
    name = "my_param_type"

    def convert(
        self,
        value: Any,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> Any:
        print("From MyParamType!")
        return value


def my_callback(
    ctx: click.Context,
    param: click.Parameter,
    value: Any,
):
    print("From my_callback!")
    return value


@click.command()
@click.option(
    "--name",
    default="World",
    type=MyParamType(),
    callback=my_callback,
)
def cli(name):
    print(f"Hello {name}!")


if __name__ == "__main__":
    cli()
