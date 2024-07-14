import click


def validate_payment_info(ctx, param, value):
    if ctx.params.get("payment_method") == "credit_card" and not value:
        raise click.BadParameter("クレジットカード支払いの場合、カード番号は必須です。")
    return value


@click.command()
@click.option(
    "--payment-method",
    type=click.Choice(
        ["cash", "credit_card"],
    ),
    required=True,
)
@click.option(
    "--card-number",
    callback=validate_payment_info,
)
def process_payment(payment_method, card_number):
    click.echo(f"支払い方法: {payment_method}")
    if payment_method == "credit_card":
        click.echo(f"カード番号: {card_number}")


if __name__ == "__main__":
    process_payment()
