---
title: 【Python】Clickのパラメータにでコールバックを設定する
tags:
  - 'Python'
  - 'Click'
private: false
updated_at: ''
id: null
organization_url_name: null
slide: false
ignorePublish: false
---


# 目次

- 1.はじめに
- 2.コールバックのユースケース
    - 入力値の検証と変換
    - 動的なデフォルト値の設定
    - 相互依存するパラメータの処理
- 3.コールバック関数の引数・返り値
    - コールバック関数に何が渡されるか
    - コールバック関数から何を返せばよいか
- 4.その他
    - `type`を使って入力値の検証と変換を行う
    - `default`に関数を設定する
- 5.まとめ

# 1.はじめに

Clickは少ないコードできれいなCLIツールを作れるPythonパッケージです。
CLIツールはPython標準モジュールのargparseでも作れますが、Clickのほうが簡単に作れます。

Clickの公式ドキュメントは[こちら](https://click.palletsprojects.com/en/8.1.x/)です。
このドキュメントを読んでいて、パラメータにコールバックを設定できることに気付きました。
しかし、少しドキュメントを読んだだけでは具体的な実装方法が分からなかったので、この記事で理解していこうと思います。

この記事では、「パラメータのコールバックで何ができるのか」、「コールバックをどのように実装するのか」が理解できることをゴールにします。

この記事で書くこと:

- Clickのコールバックのユースケース
    - 入力値の検証と変換
    - 動的なデフォルト値の設定
    - 相互依存するパラメータの処理
- Clickのコールバック関数の引数・返り値
    - 何が渡されるのか
        - Contextオブジェクト
        - Parameterオブジェクト
        - value
    - 何を返せばよいのか

この記事を読むことで、Clickのコールバックで何ができるのかがイメージでき、実際に自分のCLIツールに応用できるようになると思います。

この記事では[公式ドキュメント](https://click.palletsprojects.com/en/8.1.x/)を参考にしています。
記事の中で示すコードは以下のバージョンで実行しました。

```shell
$ python -V
Python 3.10.14

$ pip list | grep click
click             8.1.7
```

# 2.コールバックのユースケース

3つのユースケースを紹介します。

- 入力値の検証と変換
- 動的なデフォルト値の設定
- 相互依存するパラメータの処理


## 入力値の検証と変換

コールバック関数を使用して、ユーザーが入力したパラメータ値を検証したり、必要に応じて変換したりできます。
例えば、日付文字列を`datetime`オブジェクトに変換したり、特定の範囲内にある数値かどうかを確認したりするのに役立ちます。

実際にどのような挙動のCLIツールを作れるか見てみましょう。

関数`process_date`は

1. コマンドラインから文字列を受け取る
2. 日付の形式が合っているか検証する (**コールバック関数**)
3. 合っていたら`datetime`オブジェクトに変換する (**コールバック関数**)
4. 変換した`datetime`オブジェクトを出力する

ということをします。
このうち2.と3.がコールバック関数`validate_date`で実施する部分です。

```python:validate_input.py
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
```
日付形式が正常な時の実行例

`datetime`型に変換されていることが分かります。

```shell:日付形式が正常な時
$ python validate_input.py --date  2024-12-31
処理する日付: 2024-12-31 00:00:00
dateの型   : <class 'datetime.datetime'>
```

日付形式が不正な時の実行例

検証が行われていることがわかります。


```shell:日付形式が不正な時
$ python validate_input.py --date  2024/12/31
Usage: validate_input.py [OPTIONS]
Try 'validate_input.py --help' for help.

Error: Invalid value for '--date': 日付は YYYY-MM-DD 形式で入力してください。
```

### パラメータに値が指定されなかったとき

上記の例では、パラメータに値が指定されなかったとき、 `value=None` となり、 `datetime.strptime(value, "%Y-%m-%d")` の部分で`TypeError`となります。

```
TypeError: strptime() argument 1 must be str, not None
```

これのエラーハンドリングを追加する、もしくは`None`のまま値を受け取って関数`process_date`の中で何かしら処理したいということもあると思います。
その簡単な方法は[`type`を使って入力値の検証と変換を行う](#typeを使って入力値の検証と変換を行う)で説明します。


## 動的なデフォルト値の設定

コールバック関数を使用して、実行時に動的にデフォルト値を設定できます。
例えば、現在の日付や時刻、環境変数の値に基づいてデフォルト値を決定する場合に便利です。(よりシンプルな方法は[defaultに関数を設定する](#defaultに関数を設定する)を参照してください。)


実際にどのような挙動のCLIツールを作れるか見てみましょう。

関数`process_files`は

1. コマンドラインから文字列を受け取る
2. パラメータに値が指定されているかを確かめる (**コールバック関数**)
3. 指定されていなかったらカレントディレクトリ下のoutputというディレクトリを指定する (**コールバック関数**)
4. 指定されたディレクトリを出力する

ということをします。
このうち2.と3.がコールバック関数`get_default_output_dir`で実施する部分です。

```python:dynamic_default_value.py
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
```

パラメータに値を指定したときの実行例

指定した値が出力されていることがわかります。

```shell:パラメータに値を指定したとき
$ python dynamic_default_value.py --output-dir some_directory/output
ファイルを some_directory/output に出力します
```

パラメータに値を指定しなかったときの実行例

カレントディレクトリ下のoutputディレクトリが出力されていることがわかります。

```shell:パラメータに値を指定しなかったとき
$ pwd 
/workspaces

$ python dynamic_default_value.py 
ファイルを /workspaces/output に出力します
```


## 相互依存するパラメータの処理

複数のパラメータ間に依存関係がある場合、コールバック関数を使用してそれらの関係を管理できます。
例えば、あるパラメータの値に基づいて別のパラメータの振る舞いを変更したり、特定の組み合わせのパラメータが与えられた場合にのみ特定の処理を行ったりすることができます。


実際にどのような挙動のCLIツールを作れるか見てみましょう。

関数`process_payment`は

1. コマンドラインから文字列を受け取る
2. `payment_method=credit_card`のときにカード番号が与えられているかを確かめる (**コールバック関数**)
3. 与えられていなかったらエラーを送出する (**コールバック関数**)
4. 問題なければ与えられた値を出力する

ということをします。
このうち2.と3.がコールバック関数`validate_payment_info`で実施する部分です。

```python:interdependent_parameters.py
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
```

支払い方法を`cash`にしたときの実行例

問題なく実行できています。

```shell:支払い方法をcashにしたとき
$ python interdependent_parameters.py --payment-method cash
支払い方法: cash
```

支払い方法を`credit_card`にしてカード番号を与えないときの実行例

カード番号を与えなかったため、エラーとなっていることがわかります。

```shell:支払い方法をcredit_cardにしてカード番号を与えないとき
$ python interdependent_parameters.py --payment-method credit_card
Usage: interdependent_parameters.py [OPTIONS]
Try 'interdependent_parameters.py --help' for help.

Error: Invalid value for '--card-number': クレジットカード支払いの場合、カード番号は必須です。
```

支払い方法を`credit_card`にしてカード番号を与えたときの実行例

問題なく実行できました。

```shell:支払い方法をcredit_cardにしてカード番号を与えたとき
$ python interdependent_parameters.py --payment-method credit_card --card-number 1122334455667788
支払い方法: credit_card
カード番号: 1122334455667788
```

# 3.コールバック関数の引数・返り値 

ここまで具体的なユースケースを見てきて、以下のような疑問が出てきたかもしれません。
これらの疑問を解決していきましょう。

- コールバック関数には何が渡されるの?
    - `ctx` ってなに?
    - `param` ってなに?
    - `value` ってなに?
- コールバック関数からは何を返せばいいの?

## コールバック関数に何が渡されるか

コールバック関数に渡されるものには3つあります。

|変数名 | オブジェクトの型 | 説明 |
| --- | --- | --- |
| `ctx` | `click.Context` | `Context`はコマンド実行時の状態を保持しているオブジェクトです。大抵の場合は内部的に使われるものです。 [ドキュメント](https://click.palletsprojects.com/en/8.1.x/api/#context) |
| `param` | `click.Parameter` | コールバック関数を設定したパラメータに対応するオブジェクトです。パラメータのメタ情報(デフォルト値、必須かなど)を保持しています。  実際にはこのサブクラスの`click.Option`または`click.Argument` を使うことになります。 [ドキュメント](https://click.palletsprojects.com/en/8.1.x/api/#parameters)|
| `value` | `Any` | コマンドラインから渡された値です。(実際には`type`で指定したクラスによって変換された後の値です。) |


それぞれもう少し詳しく見ていきましょう。

### `click.Context`

以下の `peak_ctx` というコールバック関数をパラメータ`name`に設定して `ctx` がどのようなものなのか見てみましょう。

```python:what_is_context.py
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

```

`count`だけ値を指定して実行してみます。


```shell
$ python what_is_context.py --count 3
===== (1) type of ctx =====
<class 'click.core.Context'>

===== (2) vars(ctx) =====
{'_close_callbacks': [],
 '_depth': 2,
 '_exit_stack': <contextlib.ExitStack object at 0x7f02ac053c70>,
 '_meta': {},
 '_opt_prefixes': set(),
 '_parameter_source': {'count': <ParameterSource.COMMANDLINE: 1>,
                       'help': <ParameterSource.DEFAULT: 3>,
                       'name': <ParameterSource.DEFAULT: 3>},
 'allow_extra_args': False,
 'allow_interspersed_args': True,
 'args': [],
 'auto_envvar_prefix': None,
 'color': None,
 'command': <Command hello>,
 'default_map': None,
 'help_option_names': ['--help'],
 'ignore_unknown_options': False,
 'info_name': 'what_is_context.py',
 'invoked_subcommand': None,
 'max_content_width': None,
 'obj': None,
 'params': {'count': 3},
 'parent': None,
 'protected_args': [],
 'resilient_parsing': False,
 'show_default': None,
 'terminal_width': None,
 'token_normalize_func': None}

===== outputs of hello() =====
Hello World!
Hello World!
Hello World!
```


まず、`(1) type of ctx` から、`ctx` の型が `Context` だと確認できました。

次に、`(2) vars(ctx)` から、`ctx`はコマンド実行時の様々な状態を保持していることがわかります。たとえば、 

```
'params': {'count': 3}
```

という部分にコマンドラインから指定した`count`の値である3が入っていることがわかります。また、

```
'_parameter_source': {'count': <ParameterSource.COMMANDLINE: 1>,
                    'help': <ParameterSource.DEFAULT: 3>,
                    'name': <ParameterSource.DEFAULT: 3>},
```

という部分に、各パラメータのソースの情報が保持されています。例えば、`count` はコマンドラインから入力したので`COMMANDLINE`、`name`は与えられていないのでデフォルト値が使われており`DEFAULT`となっています。
このパラメータのソースは取得するためのメソッドが`Context`に用意されています。
(ドキュメント: [get_parameter_source(name)](https://click.palletsprojects.com/en/8.1.x/api/#click.Context.get_parameter_source) )

### `click.Parameter`


今度は以下の `peak_param` というコールバック関数をパラメータ`name`に設定して `param` がどのようなものなのか見てみましょう。

```python:what_is_parameter.py
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

```

`name`だけ値を指定して実行してみます。

```shell
$ python what_is_parameter.py --name John
===== (1) type of param =====
<class 'click.core.Option'>
is subclass?: True

===== (2) vars(param) =====
{'_custom_shell_complete': None,
 '_flag_needs_value': False,
 'allow_from_autoenv': True,
 'callback': <function peak_param at 0x7f00e5b4fd90>,
 'confirmation_prompt': False,
 'count': False,
 'default': 'World',
 'envvar': None,
 'expose_value': True,
 'flag_value': False,
 'help': 'The person to greet.',
 'hidden': False,
 'hide_input': False,
 'is_bool_flag': False,
 'is_eager': False,
 'is_flag': False,
 'metavar': None,
 'multiple': False,
 'name': 'name',
 'nargs': 1,
 'opts': ['--name'],
 'prompt': None,
 'prompt_required': True,
 'required': False,
 'secondary_opts': [],
 'show_choices': True,
 'show_default': None,
 'show_envvar': False,
 'type': STRING}

===== outputs of hello() =====
Hello John!
```

まず、`(1) type of param` から、`param` の型が `Option` だとわかります。
また、`Option` は `Parameter` のサブクラスであることも確認できました。

次に、`(2) vars(param)` から、`param`はパラメータの様々なメタデータを保持していることがわかります。たとえば、

```
'default': 'World'
```

という部分から、デフォルト値が `'World'` であることがわかります。

### `value`

`value`はコマンドラインから渡された値ですが、これも確認しておきましょう。
(実際には`type`で指定したクラスによって変換された後の値です。)

```python:what_is_value.py
from pprint import pprint
from typing import Any

import click


def peak_value(
    ctx: click.Context,
    param: click.Parameter,
    value: Any,
):
    print("=" * 5, "(1)", "type of value", "=" * 5)
    print(type(value))
    print()

    print("=" * 5, "(2)", "print value", "=" * 5)
    pprint(value)
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
    callback=peak_value,
)
def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    print("=" * 5, "outputs of hello()", "=" * 5)
    for _ in range(count):
        click.echo(f"Hello {name}!")


if __name__ == "__main__":
    hello()

```

`name`に値を指定して実行してみます。

```shell
$ python what_is_value.py --name John
===== (1) type of value =====
<class 'str'>

===== (2) print value =====
'John'

===== outputs of hello() =====
Hello John!
```

`value`が コマンドラインから渡された値であることが確認できました。


## コールバック関数から何を返せばよいか

コールバック関数の返り値は最終的にCLIの関数に渡したい値にすれば大丈夫です。

上の例で言えば、`hello`関数の`name`に渡したい値を返せばよいです。

# 4.その他

ここまでコールバック関数について解説してきましたが、実は上で説明したユースケースの中に、コールバック関数以外の方法で実装したほうがよい場合があります。
それに関係する話題を紹介します。

## `type`を使って入力値の検証と変換を行う

Clickには、入力値の検証と変換を行うための強力なtypeオプションが用意されています。
特に`click.DateTime`を使用することで、日付と時刻の検証と型変換を簡単に行うことができます。
この方法は、以下の理由でコールバック関数を使用するよりも優れていることが多いです。

- 簡潔なコード: `click.DateTime`を`type`に指定するだけで、日付の検証と`datetime`オブジェクトへの変換が自動的に行われます。
- デフォルト値の扱いが容易: [入力値の検証と変換](#入力値の検証と変換)で紹介した例では、値を何も指定しなかった場合にエラーが発生してしまい、それを避けるための追加のコードが必要でした。一方、`click.DateTime`を使用すれば、デフォルト値の設定も含めてより少ないコードで実装できます。
- カスタマイズ性: `click.DateTime`のサブクラスを作成することで、検証ロジックを簡単にカスタマイズできます。こちらのほうがコールバック関数を使用するよりも自然で明確な方法だと思います。

`click.DateTime` を使った例を見てみましょう。

```python:validate_input_with_type.py
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
```

パラメータに値を指定しないで実行してみます。

```shell
$ python validate_input_with_type.py 
処理する日付: None
dateの型   : <class 'NoneType'>
```

関数`process_date`に`None`が渡されていることがわかります。

パラメータに値を指定したときはどうでしょうか。

```shell:日付形式が正常な時
$ python validate_input_with_type.py --date 2024-12-31
処理する日付: 2024-12-31 00:00:00
dateの型   : <class 'datetime.datetime'>
```

```shell:日付形式が不正な時
$ python validate_input_with_type.py --date 2024/12/31
Usage: validate_input_with_type.py [OPTIONS]
Try 'validate_input_with_type.py --help' for help.

Error: Invalid value for '--date': '2024/12/31' does not match the format '%Y-%m-%d'.
```

しっかり検証してくれていることがわかりますね。

以上から、単純な検証と型変換は`type`に適切な型を設定するほうが簡単そうだと言えると思います。

次にカスタム検証ロジックを実装してみましょう。

この例では、入力された日付が現在よりも未来であることを確認するカスタム型FutureDateTimeを定義しています。

```python:validate_custom_logic.py
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

```

実行してみましょう。

```shell:過去の日付
$ python validate_custom_logic.py --future-date 2000-01-01
Usage: validate_custom_logic.py [OPTIONS]
Try 'validate_custom_logic.py --help' for help.

Error: Invalid value for '--future-date': future_date must be in the future
```

```shell:未来の日付
$ python validate_custom_logic.py --future-date 2050-01-01
処理する未来の日付: 2050-01-01 00:00:00
```

うまく検証できていますね。


### `type`の変換とcallbackはどちらが先に実行されるのか

上の例をみてさらに「`type`の変換とcallbackはどちらが先に実行されるんだ？」と疑問に思った人もいると思います。
結論から言うと、 `type`の変換 → callback の順で実行されます。
それを確かめましょう。

```python:which_comes_first.py
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

```

このコードでは、カスタム `ParamType` と `callback` 関数の両方を定義し、それぞれが呼び出されたときにメッセージを出力するようにしています。
実行結果は以下のようになります：

```shell
$ python which_comes_first.py 
From MyParamType!
From my_callback!
Hello World!
```

この結果から、以下のことが分かりました。

- `type` による変換（この場合は `MyParamType` の `convert` メソッド）が最初に実行されます。
- その後、callback 関数が実行されます。
- 最後に、変換・処理された値が CLI 関数（この場合は `cli`）に渡されます。

このことから、`type` による変換とcallbackの使い分けは以下の方針で考えれば良いと思いました。

- type による変換で基本的な型変換や簡単な検証を行い、その結果を callback 関数で利用する
- callback 関数では、既に型変換された値を受け取るため、より複雑な検証や変換を行うことができる


## `default`に関数を設定する

[動的なデフォルト値の設定](#動的なデフォルト値の設定)ではcallback関数を使って動的なデフォルト値を設定しましたが、Clickでは`default`パラメータに関数を設定することで、動的なデフォルト値を簡単に実装できます。

```python:dynamic_default_with_func.py
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

```

この例では、`--date`オプションが指定されなかった場合、`get_today`関数が呼び出され、現在の日付がデフォルト値として使用されます。

実行してみましょう。

```shell
$ date
Sun Jul 14 08:46:27 UTC 2024

$ python dynamic_default_with_func.py 
処理する日付: 2024-07-14
```

うまくいっていますね。

# 5.まとめ

この記事では、PythonのClickパッケージを使ってCLIツールにパラメータのコールバックを設定する方法を解説しました。以下の内容をカバーしました。

1. **コールバックのユースケース**  
   - 入力値の検証と変換
   - 動的なデフォルト値の設定
   - 相互依存するパラメータの処理

2. **コールバック関数の詳細**  
   - 引数と返り値
   - Contextオブジェクト、Parameterオブジェクト、valueの使い方

3. **その他の便利な機能**  
   - `type`パラメータを使った入力値の検証と変換
   - `default`に関数を設定して動的なデフォルト値を指定する方法

これらを学ぶことで、Clickを使ったCLIツールの作成がより柔軟で強力になります。公式ドキュメントも参考にしながら、自分のプロジェクトに適用してみてください。

# 参考文献

- Click公式ドキュメント: [Click Documentation](https://click.palletsprojects.com/en/8.1.x/)
