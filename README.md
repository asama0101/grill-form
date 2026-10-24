# grill-form marketplace

Claude Code 用プラグイン「grill-form」を配布するマーケットプレイスです。

## プラグイン

| 名前 | 内容 |
| --- | --- |
| [grill-form](plugins/grill-form/README.md) | 計画や設計を、ブラウザのフォームで答えながら詰めて、SPEC にまとめる |

## 導入方法

Claude Code で実行します。詳しい前提条件と使い方は、[プラグインの README](plugins/grill-form/README.md) を見てください。

```
/plugin marketplace add asama0101/grill-form
/plugin install grill-form@grill-form
```

GitHub を使わず、ローカルにコピーして入れる方法は、[プラグインの README](plugins/grill-form/README.md) にあります。

## 開発者向け

仕組みとテストは [docs/development.md](docs/development.md) にあります。ローカルで試すときは、リポジトリの直下で次のように起動します。

```bash
claude --plugin-dir ./plugins/grill-form
```

## ライセンス

[MIT](LICENSE)
