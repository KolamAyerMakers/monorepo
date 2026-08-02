tmpsh() {
    local TMP_DIR=$(mktemp -d)
    local TMP_INIT=$(mktemp)
    pushd "$TMP_DIR" >/dev/null
    cat <<EOF >"$TMP_INIT"
trap 'rm -rf "$TMP_DIR" "$TMP_INIT"' EXIT
source ~/.bashrc
EOF
    bash --init-file "$TMP_INIT"
    popd >/dev/null
}
