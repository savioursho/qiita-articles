from datetime import datetime

import click


def validate_date(ctx, param, value):
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise click.BadParameter("日付は YYYY-MM-DD 形式で入力してください。")


@click.command()
@click.option(
    "--date",
    callback=validate_date,
    help="日付 (YYYY-MM-DD)",
)
def process_date(date):
    click.echo(f"処理する日付: {date}")
    click.echo(f"dateの型   : {type(date)}")


if __name__ == "__main__":
    process_date()
