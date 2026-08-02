#!/bin/bash

set -euo pipefail

export TERM="${TERM:-xterm-256color}"
export COLUMNS="${COLUMNS:-80}"
export LANG=C.UTF-8
export LC_ALL=C.UTF-8

rail() {
    local corner_left=$1 corner_right=$2
    printf '   \033[38;5;37m%s\033[0m' "${corner_left}─"
    printf '\033[1;38;5;118m%s\033[0m' '◇'
    printf '\033[38;5;37m%s\033[0m' '──────────────────────────────────────'
    printf '\033[1;38;5;118m%s\033[0m' '◇'
    printf '\033[38;5;37m%s\033[0m\n' "─${corner_right}"
}

add_bars() {
    while IFS= read -r line; do
        visible_text=$(printf '%s' "$line" | sed $'s/\e\\[[0-9;]*m//g')
        visible_width=${#visible_text}
        right_pad=$((42 - visible_width))
        [ $right_pad -lt 0 ] && right_pad=0
        printf '   \033[38;5;37m│\033[0m%s%*s\033[38;5;37m│\033[0m\n' "$line" $right_pad ''
    done
}

echo
rail '┌' '┐'
{
    {
        printf '\n'
        /usr/bin/figlet -f pagga -w 80 "Kolam Ayer" | /usr/bin/pr -to 2
        printf '\n'
        /usr/bin/figlet -f pagga -w 80 "Makers" | /usr/bin/pr -to 9
    } | /usr/games/lolcat -p 1 -S 42 -f
    printf '\n'
    printf '         '
    printf '\033[1;38;5;154m%s\033[0m' '>_'
    printf ' '
    printf '\033[1;38;5;208m%s\033[0m' 'Build.'
    printf ' '
    printf '\033[1;38;5;51m%s\033[0m' 'Break.'
    printf ' '
    printf '\033[1;38;5;118m%s\033[0m' 'Repeat.'
    printf '\n'
    printf '\n'
} | add_bars

rail '└' '┘'
echo
