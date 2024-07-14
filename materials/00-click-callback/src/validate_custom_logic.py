from datetime import datetime

import click


class FutureDateTime(click.DateTime):
    def convert(self, value, param, ctx):
        dt = super().convert(value, param, ctx)
        if dt <= datetime.now():
            self.fail(f"{param.name} must be in the future", param, ctx)
        return dt


@click.command()
@click.option("--future-date", type=FutureDateTime(formats=["%Y-%m-%d"]))
def process_future_date(future_date):
    click.echo(f"処理する未来の日付: {future_date}")


if __name__ == "__main__":
    process_future_date()
