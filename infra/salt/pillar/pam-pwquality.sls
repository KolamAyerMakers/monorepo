pam_pwquality:
  packages:
    - libpam-pwquality
    - libpwquality-tools
    - cracklib-runtime
    - wamerican-large
    - wbritish-large
  configuration_directory: /etc/security/pwquality.conf.d
  configuration_file: /etc/security/pwquality.conf.d/50-defaults.conf
  cracklib_dictionary_path: /var/cache/cracklib/cracklib_dict.pwd
  cracklib_update_command: update-cracklib
  pam_profile_command: pam-auth-update --package --enable pwquality
  pam_profile_check_command: grep -q 'pam_pwquality.so' /etc/pam.d/common-password
  options:
    minlen: 18
    dcredit: 0
    ucredit: 0
    lcredit: 0
    ocredit: 0
    minclass: 0
    maxrepeat: 4
    maxsequence: 4
    gecoscheck: 1
    dictcheck: 1
    usercheck: 1
    enforcing: 1
    retry: 3
  flags:
    - enforce_for_root
