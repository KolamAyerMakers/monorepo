printing:
  packages:
    - cups
    - cups-client
    - sane-airscan
    - sane-utils
    - simple-scan
  cups:
    service: cups
    socket: cups.socket
    path: cups.path
    listen:
      - localhost:631
      - /run/cups/cups.sock
    browsing: false
    browse_local_protocols: none
    default_shared: false
    web_interface: false
    preserve_job_files: false
    preserve_job_history: false
    default_auth_type: Basic
    cups_browsed:
      package: cups-browsed
      service: cups-browsed
  printer:
    name: epson-ecotank-l4260
    uri: ipp://epson-ecotank-l4260.printers.h.hxd/ipp/print
    model: everywhere
    default: true
  scanner:
    name: Epson EcoTank L4260
    url: https://epson-ecotank-l4260.printers.h.hxd/eSCL
    protocol: eSCL
