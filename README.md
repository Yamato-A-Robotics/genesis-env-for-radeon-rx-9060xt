# genesis-uv-env

git clone https://github.com/YamatoAme-robotics/genesis-uv-env/edit/main

cd /path/to/コピー先

1. 仮想環境を作り直す（uv.lock のとおりのバージョンが入る）
rm -rf .venv
uv sync --frozen

2. .env の絶対パスをコピー先に合わせて書き換える
sed -i "s#/home/yamato/RML_project/genesis-sim#$PWD#g" .env
cat .env    # ROCM_PATH と PYTORCH_TUNABLEOP_FILENAME がコピー先を指しているか確認する

3. lld へのリンクを作り直す
mkdir -p .rocm-shim/llvm/bin
ln -sf "$(command -v ld.lld)" .rocm-shim/llvm/bin/ld.lld
