/etc/profile.d/uv_tools.sh:
  file.managed:
    - user: root
    - group: root
    - mode: '0644'
    - contents: |
        # Add uv-managed Python tools to PATH
        export PATH="/opt/uv_tools/bin:$PATH"
