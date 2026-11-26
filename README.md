# genesis-env-for-radeon-rx-9060xt

AMD Radeon RX 9060 XT（RDNA4 / `gfx1200`）で [Genesis](https://github.com/Genesis-Embodied-AI/Genesis)（`genesis-world`）を GPU で動かすための、[uv](https://docs.astral.sh/uv/) 用の設定ファイル一式です。

Genesis リポジトリをクローンしたあと、その `pyproject.toml` をこのリポジトリのものに**置き換えて**使います。置き換えると、ROCm 7.2 版の PyTorch と、Genesis のサンプル（`examples/`）を動かすのに必要なパッケージがまとめて入ります。

## このリポジトリに含まれるファイル

| ファイル | 役割 |
| --- | --- |
| `genesis-sim/pyproject.toml` | Genesis 本家の `pyproject.toml` と置き換える設定ファイル。PyTorch / torchvision / triton-rocm を ROCm 7.2 用のインデックスから取得し、`genesis-world` と `rsl-rl-lib>=5.0.0` も依存に含めています |
| `genesis-sim/uv.lock` | 依存関係のロックファイル（`genesis-world` 1.5.0 で固定） |
| `genesis-sim/check_gs.py` | `amdgpu` バックエンドの動作確認スクリプト |
| `genesis-sim/tunableop_results0.csv` | PyTorch TunableOp のチューニング結果（`gfx1200`） |

## 動作確認済み環境

| 項目 | バージョン |
| --- | --- |
| GPU | Radeon RX 9060 XT (`gfx1200`) |
| OS | Linux x86_64 |
| Python | 3.12 |
| Genesis (`genesis-world`) | 1.5.0 |
| PyTorch | 2.14.1（ROCm 7.2 ビルド） |

## 前提条件

- AMD GPU ドライバ（amdgpu）が導入済みで、ユーザーが `render` / `video` グループに所属していること
- [uv](https://docs.astral.sh/uv/getting-started/installation/) がインストール済みであること
- `ld.lld`（LLVM リンカ）がインストール済みであること

```bash
# 例: Ubuntu / Debian
sudo apt install lld
command -v ld.lld   # パスが表示されればOK
```

## セットアップ

### 1. 2 つのリポジトリをクローンする

`uv.lock` が `genesis-world` 1.5.0 で固定されているため、Genesis も同じバージョンのタグ `v1.5.0` をチェックアウトします。サンプルコードとライブラリのバージョンがずれないようにするためです。

```bash
git clone --branch v1.5.0 https://github.com/Genesis-Embodied-AI/Genesis.git
git clone https://github.com/YamatoAme-robotics/genesis-env-for-radeon-rx-9060xt.git
```

### 2. 設定ファイルを置き換える

```bash
cd Genesis

# 元の pyproject.toml を退避（git restore でも戻せます）
mv pyproject.toml pyproject.toml.orig

# このリポジトリの設定ファイルをコピー
cp ../genesis-env-for-radeon-rx-9060xt/genesis-sim/pyproject.toml .
cp ../genesis-env-for-radeon-rx-9060xt/genesis-sim/uv.lock .

# 動作確認スクリプトは examples/ に置く（理由は後述）
cp ../genesis-env-for-radeon-rx-9060xt/genesis-sim/check_gs.py examples/

# TunableOp の結果を使う場合のみ
cp ../genesis-env-for-radeon-rx-9060xt/genesis-sim/tunableop_results0.csv .
```

### 3. `ld.lld` の shim を作る

```bash
mkdir -p .rocm-shim/llvm/bin
ln -sf "$(command -v ld.lld)" .rocm-shim/llvm/bin/ld.lld

echo "ROCM_PATH=$PWD/.rocm-shim" > .env

# Genesis 本家の .gitignore は書き換えず、ローカルの除外設定に追加する
echo ".rocm-shim/" >> .git/info/exclude
```

`.env` と `uv.lock` は、Genesis 本家の `.gitignore` ですでに除外されています。

**shim が必要な理由**：Genesis の `amdgpu` バックエンドは、GPU カーネルのリンクに `$ROCM_PATH/llvm/bin/ld.lld` を使います。ROCm 一式をシステムに入れずに uv 経由の ROCm 版 PyTorch だけで動かす場合、このファイルが存在しません。そこで、システムの `ld.lld` へのシンボリックリンクを置いて代用します。

### 4. 依存関係をインストールする

```bash
uv sync
```

## 動作確認

```bash
uv run --env-file .env examples/check_gs.py
```

`amdgpu` バックエンドで、床と Franka Panda アームのシーンを 100 ステップ実行します。最後に `OK` と表示されれば成功です。初回はカーネルのコンパイルに時間がかかることがあります。

> **`check_gs.py` を Genesis のルートに置かない理由**：ルートで実行すると、スクリプトのディレクトリにある `genesis/`（ソースコード）が、`uv sync` で入れた `genesis-world` より優先して import されてしまいます。`examples/` 以下に置けばこの問題は起きません。

## サンプルを動かす（例：Go2 の歩行学習）

`rsl-rl-lib` が入っているので、Genesis の強化学習サンプルもそのまま動かせます。

```bash
# ディレクトリの移動
cd examples/locomotion

# 学習（環境数は VRAM に合わせて調整）
uv run go2_train.py -e go2-walking -B 512 --max_iterations 101

# 学習済みモデルの評価
uv run go2_eval.py -e go2-walking --ckpt 100
```

サンプルは `gs.init(backend=gs.gpu)` で初期化されます。AMD GPU が選ばれない場合は、スクリプト内の `gs.gpu` を `gs.amdgpu` に変更してください。

### TunableOp を使う場合

```bash
PYTORCH_TUNABLEOP_ENABLED=1 \
PYTORCH_TUNABLEOP_FILENAME=tunableop_results%d.csv \
uv run --env-file .env examples/locomotion/go2_train.py
```

同梱の `tunableop_results0.csv` は、同じ GPU・同じ PyTorch / ROCm のバージョンでのみ再利用できます。

## 元に戻す

```bash
mv pyproject.toml.orig pyproject.toml   # または git restore pyproject.toml
rm -rf .venv .rocm-shim .env uv.lock examples/check_gs.py
```

## 注意点

- 置き換え後の `pyproject.toml` は、PyPI 版の `genesis-world` 1.5.0 をインストールします。クローンした Genesis のソースコード（`genesis/`）はライブラリとしては使われず、サンプルコードの置き場として使う形になります。Genesis 本体を改造したい場合は、この構成では反映されません。
- `.env` には絶対パスが書かれています。ディレクトリを移動したら、手順 3 をやり直してください。

## トラブルシューティング

| 症状 | 確認すること |
| --- | --- |
| `ld.lld` が見つからない / リンクエラー | `command -v ld.lld` の結果と、`.rocm-shim/llvm/bin/ld.lld` のリンク先 |
| `amdgpu` バックエンドの初期化に失敗する | `--env-file .env` を付けて実行しているか |
| GPU が認識されない | `uv run python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"` の結果、`render` / `video` グループへの所属 |
| import エラーやバージョン不一致 | Genesis のチェックアウトが `v1.5.0` になっているか（`git describe --tags`） |
