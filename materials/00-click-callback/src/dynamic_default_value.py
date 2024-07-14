import os

import click


def get_default_output_dir(ctx, param, value):
    if value is None:
        return os.path.join(os.getcwd(), "output")
    return value


@click.command()
@click.option(
    "--output-dir",
    callback=get_default_output_dir,
    help="出力ディレクトリ",
)
def process_files(output_dir):
    click.echo(f"ファイルを {output_dir} に出力します")


if __name__ == "__main__":
    process_files()
