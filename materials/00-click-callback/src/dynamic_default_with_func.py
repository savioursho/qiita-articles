from datetime import date

import click


def get_today():
    return date.today().isoformat()


@click.command()
@click.option(
    "--date",
    default=get_today,
    help="処理する日付 (デフォルト: 今日)",
)
def process_date(date):
    click.echo(f"処理する日付: {date}")


if __name__ == "__main__":
    process_date()
