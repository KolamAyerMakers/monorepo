#!/bin/sh
set -eu

temporary_file="$(mktemp /etc/.resolv.conf.XXXXXX)"
cleanup() {
  rm -f "${temporary_file}"
}
trap cleanup EXIT

{
  printf '%s\n' '# Managed by Salt — DNS handled by local Unbound'
  printf '%s\n' 'nameserver 127.0.0.1'
} > "${temporary_file}"

chown root:root "${temporary_file}"
chmod 0644 "${temporary_file}"
mv "${temporary_file}" /etc/resolv.conf
trap - EXIT
