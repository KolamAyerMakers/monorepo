# vim: filetype=sh

_preprend_path() {
    export PATH="$1:$PATH"
}

_preprend_path_if_exists() {
    if [ -d "$1" ]
    then
        _preprend_path "$1"
    fi
}

_preprend_path_if_exists ~/go/bin
_preprend_path_if_exists ~/.local/bin
_preprend_path_if_exists ~/.cargo/bin
_preprend_path ./node_modules/.bin
