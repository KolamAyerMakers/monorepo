apt:
  sources:
    debian-main:
      Types: deb
      URIs: https://deb.debian.org/debian
      Suites: "{{ grains.oscodename }}"
      Components: main
      Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
    debian-updates:
      Types: deb
      URIs: https://deb.debian.org/debian
      Suites: "{{ grains.oscodename }}-updates"
      Components: main
      Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
    debian-security:
      Types: deb
      URIs: https://deb.debian.org/debian-security
      Suites: "{{ grains.oscodename }}-security"
      Components: main
      Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
