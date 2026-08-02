{%- from "bootstrap/macros/packages.sls" import bootstrap_package_installed -%}

include:
  - bootstrap.packages
  - d2
  - glow
  - micro
  - nodejs
  - presenterm
  - ttyd

{{ bootstrap_package_installed('weechat', state_identifier='roles::kam_classroom::weechat') }}

{{ bootstrap_package_installed('sqlite3', state_identifier='roles::kam_classroom::sqlite3') }}

{{ bootstrap_package_installed('pandoc', state_identifier='roles::kam_classroom::pandoc') }}

{{ bootstrap_package_installed('texlive-xetex', state_identifier='roles::kam_classroom::texlive_xetex') }}

{{ bootstrap_package_installed('texlive-latex-extra', state_identifier='roles::kam_classroom::texlive_latex_extra') }}

{{ bootstrap_package_installed('texlive-fonts-recommended', state_identifier='roles::kam_classroom::texlive_fonts_recommended') }}

{{ bootstrap_package_installed('fonts-texgyre', state_identifier='roles::kam_classroom::fonts_texgyre') }}

{{ bootstrap_package_installed('lmodern', state_identifier='roles::kam_classroom::lmodern') }}

{{ bootstrap_package_installed('xxd', state_identifier='roles::kam_classroom::xxd') }}

{{ bootstrap_package_installed('tree', state_identifier='roles::kam_classroom::tree') }}

{{ bootstrap_package_installed('ncdu', state_identifier='roles::kam_classroom::ncdu') }}

{{ bootstrap_package_installed('util-linux', state_identifier='roles::kam_classroom::util-linux') }}
