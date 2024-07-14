import click


@click.command()
@click.option(
    "--date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
)
def process_date(date):
    click.echo(f"処理する日付: {date}")
    click.echo(f"dateの型   : {type(date)}")


if __name__ == "__main__":
    process_date()
