# シフト最適化

## 導入

このプロジェクトは、Python と PuLP ライブラリを使用して、指定された条件下でのシフト最適化問題を解くためのツールです。このツールを使用すると、効率的な労働シフトを自動的に生成できます。Docker を使用して環境構築を行い、エクセルファイルをアップロードすることでシフトを自動生成します。

## 目次

- [導入](#導入)
- [インストール](#インストール)
- [使用方法](#使用方法)
- [機能](#機能)
- [依存関係](#依存関係)

## インストール

このプロジェクトを使用するには、まず GitHub からリポジトリをクローンしてください。

```
git clone https://github.com/fijaival/streamlitShiftOpt.git
cd streamlitShiftOpt
```

次に、Docker イメージをビルドし、コンテナを作成します。

```
docker build -t shift-optimization .
docker run -d -p 8501:8501 --name shift-optimization-container shift-optimization
```

## 使用方法

コンテナが起動したら、指定のエクセルファイルをアップロードすることでシフトが自動生成されます。Excel のフォーマット、詳細な使用方法は、[ドキュメント](https://docs.google.com/document/d/1vocseYnQFl_5dQGwur9ExYMgxWMBxQPYyg28EMbcf6E/edit#heading=h.z3pinjp9be6p)を参照してください。

## 機能

- 休み希望、勤務条件を考慮した調理師のシフト最適化

## 依存関係

- Python
- PuLP
- Docker
