# genesis-uv-env

mkdir -p .rocm-shim/llvm/bin
ln -sf "$(command -v ld.lld)" .rocm-shim/llvm/bin/ld.lld

echo "ROCM_PATH=$PWD/.rocm-shim" > .env
echo ".rocm-shim/" >> .gitignore
uv run --env-file .env check_gs.py
