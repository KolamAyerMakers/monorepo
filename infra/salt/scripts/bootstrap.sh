#!/bin/bash -eu

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
saltstack_dir="$(cd "${script_dir}/.." && pwd)"

cd "${saltstack_dir}"
env UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/uv-cache}" \
    XDG_DATA_HOME="${XDG_DATA_HOME:-/tmp/xdg-data}" \
    uv sync --python 3.12
exec uv run salt-runner local-apply
