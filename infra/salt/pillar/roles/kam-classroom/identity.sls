#!jinja|yaml|age
kam_classroom:
  identity:
    registration_user:
      user: new
      group: new
      uid: 986
      gid: 980
    registration_administrator: pmuller
    default_group: humans
    groups:
      humans:
        gid_number: 1001
      makers:
        gid_number: 1002
      architects:
        gid_number: 1003
      speakers:
        gid_number: 1004
      lf2607:
        gid_number: 1007
      admins:
        gid_number: 1008
      mentors:
        gid_number: 1009
      pa:
        gid_number: 1010
      volunteers:
        gid_number: 1011
      linux-foundations:
        gid_number: 1012
      students:
        gid_number: 1013
      guide:
        gid_number: 9000
      irc-bots:
        gid_number: 9001
    managed_users:
      pmuller:
        uid_number: 10000
        display_name: Philippe Muller
        email: ENC[age-identity,YWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IFgyNTUxOSBxRndIS0thd2xGK1lhZlFJVERPY092T1lPa09aL2xQOFQ1MFBQMzVmL0NFCi9UR3ZmczEwdDdNcVJzN2VNQjBNTkdYNk1IMDdKUTI4b3QrYUhFc29CcmMKLS0tIHJxWUh6czRjT25UYy9kaDZCVlpPTzhBc1VheDBJV0V4WnpCNGNweVNrOFUKWFhbMzLlATXxCTtrVVGQ5bzJgf5SUnMgr1H0GF5L+/RIYzzVNwmtBbe8y+xGtH7vKJGE3NoSFL1H]
        home_directory: /home/pmuller
        shell: /bin/bash
        primary_group: humans
        secondary_groups:
          - mentors
          - admins
          - linux-foundations
        ssh_public_keys:
          - ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDvgDgAu4i3Og5u4/M6qzOYWtdHy6jOcH0XJ6f7hTS3UqlgpuEe96FvFhOdRzG42KsyhM7mN+AcmaW5ANxq6rezc7Hl+mgw0tiEF90SzdKEuMkMJ3hazQ48GD+exk995Sni2/4UvLrdir7jIdRkaEp+eM5EOTBm+z5ism68cNgN/6Ff5XLT3I3QoFLwn2ip8LvCxMDSoy+zPn2WAsnLpnELyP3IxsQjAqGrADKjrIgro4ZatKbUVXriAXb6aXveujk9SP1JIaZB+TUtvCBIiXyEwvUMz5uHuN9+/LuEhGn9fWIuDB35pWkH5dbIeKE5J20bBShWkjXvy5pq1ESMrbKUwfVkJ7updwIVceA2L0Z7scfvLjybdT0xaO02MPWzsApbO8FvTB69XVTNHwdkQNr1QxUDqCSBsRq7ANcO4quUNA5qhS6bVeBvFJ/PoyX0JYOe4/rB9+Yg0xkEofE7d9TO+S5wWNi2W0NjvgObzyIgBQiXD0xgu0ACOd8kPQB/ybmpAKp2+XlZ/tDOsjY2FPhpZuGhR13IOZjybswG9nE5uLb43UtQ+ULccSWzcIB35/U9ilX0UnDXO/l2rLDRt95aB5pH1V9h/HNau6il5ZueE2043HXhXx/8jqP8WKqeOt76BG4sKnb7yKfU3FAsGMlUg/58cXKDHMA4tBUc08IMnQ== cardno:25_939_134
      wanlong:
        uid_number: 10001
        display_name: Wanlong
        email: ENC[age-identity,YWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IFgyNTUxOSBYQmY5Q2U0VmJFSGxDdlFtQUJKWHgzY2UrbnpPdVpJK1l4T1NuZWFEemxrCkFGZjE2VHhQYVBjTzFPSTI1MkZ4V0xhamtvci9UaVVQNjF0KzNqci9BWm8KLS0tIGdBaGpMdGdrbVFMcmxjMEtsSlhNN1YxZFpWekdGU29iSWF1eEdDbkJaRVUK7OX+EeYQ63e2kb087D5THFS8w03rQNLoGegwtYsrlUx6cerW9Ct5h3F4KT9RwzhNI0C3a1LgmCg=]
        home_directory: /home/wanlong
        shell: /bin/bash
        primary_group: humans
        secondary_groups:
          - mentors
          - linux-foundations
        ssh_public_keys:
          - ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDpWXTVSWxIiXtOWSp7UT0KG1ZmFjtuNxRrn4HX5x9QPuvQpyhGPRu4dcV0f9dv99P61mVrr1UVszhYMcgP/9MVq1u0bPGiqiaGNzfUU1QAKtrCoAoDz7UXpeW8JclQIZT37UtUJfPYJepFda6byaFkoxTNJyGZMMC0iITbuzEOL3QVI0Ii8HdqPTyCB3nl1eVgSzLeJPAPQV5ZDYFKhl/XjVjGSKlCpd9e7qvEczQoEKrFQYPrlwFg9mftTLuu9P86x0uSTbQdbOMLw8sPPAnZxhDfsoU4h9/OpkJideui65jrjxRnJXlZTZEWbyeGh7DPbfncUvpgwihHjn+MLPQJilM0aeYK0k1l7Pf/+qLudVLEFC/UExdnoQhO2fq9QjaIUcjqh+ExUXpn0wZHAvXUPdUrcrEvX8ZMMQOmIyF2K2y+1MvTjOwxJte+SAjwpPZfdEonMzYNC7ehNyiNRyXVNTK/DG9cHkrL0lkvUhGdGpkgEaNAKsn+lE9Tyq+WmOc= wanlong@home
      guide:
        uid_number: 9000
        display_name: The Guide
        email: ENC[age-identity,YWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IFgyNTUxOSBtUTgvekEzSFdVMjYyK1dnTG9Ldmc3NmNMMFQrY1VDRXVmeFJuaWYxY1FNCmQrT2ZmVTJ4R3F0L2txQUdNUkxDbXY4L0xHWFVtOWNOSFFTdUgzaXNvd1UKLS0tIFQ2a0pkeGsyeCt4K3g2MmtrZ2ZMMjF1VGRXU0JqM0NEbzl3MjYrVnpWZ1UK54Wme+HauuGZRjueceJRs7+hmaZ/mF7UYFpwik9L+bRmFOIpLqppNi1M/Efckuh62GeTMYKF1Q==]
        home_directory: /var/lib/guide
        shell: /usr/sbin/nologin
        primary_group: guide
        secondary_groups:
          - irc-bots
      pradeep:
        uid_number: 10002
        display_name: Pradeep
        email: ENC[age-identity,YWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IFgyNTUxOSBrcFlYeWdkcTNsYU5CSDlxeDZnb3RQNlVMU0JmUjVkRE9KWDlOTk4yWVc4CnhGQmRzbkROOUcwVWNmVzZWbDNab2dKYVZXNi9YNmdRZ3hFSko0SForU1kKLS0tIFdIVUgrNzVVZnBLM0JhbHh6NGF3bUVoVGFZNUNNd3Y1N0NjUDlVN2haeGMK2RFtl0PkgsbrkAdbRiqZZJRJwG/DBJGslHhKjZsyVvIX24XIiwG9fIWHOsh2t8lk2uzX]
        home_directory: /home/pradeep
        shell: /bin/bash
        primary_group: humans
        secondary_groups:
          - volunteers
          - linux-foundations
      ben:
        uid_number: 10003
        display_name: Ben
        email: ENC[age-identity,YWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IFgyNTUxOSBwaUI4dml5ZllIWFJGZ2ZXVVdxSnQxaVAweCt6bTZ4YnEvUVQ1WHdSeHhZClg5RFZvQWE1QUJHelF0aEZ6N09jWUxESzJ5YkptNFE0dVYreTdGU0pidWsKLS0tIHdWV2txTC9hdUE1UUNQV2hCYm5yTTZHOTFoWHFYTmRYeFBtT28vOENBcU0KWckgbuSmBG+5kWKnve6yXJ5GtlazR1TKaXiFMNNh0xUIFap+ZvGPGABXmF4DGrVyxT2plPI=]
        home_directory: /home/ben
        shell: /bin/bash
        primary_group: humans
        secondary_groups:
          - volunteers
          - linux-foundations
      tess:
        uid_number: 10004
        display_name: ENC[age-identity,YWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IFgyNTUxOSBHNC8zNS9FTEFEanU5bXhYaFdBOVFMd2UzcHRmVFhpL1NOS3FhbitiSzBNCkhaQ3diOWhLUDdWVDkrdURwUUhjWHV6MVJWVkpiWWZrRUdCSXZGODIwbGcKLS0tIGNWcHVnNnB6VUgvazluc2ZIYzFSbk53ditrZ1lKV2dtY3NpYmxDNm1oblEKY9eKpz9n7neYcZn1iSCwVDpFdov6CuOBdwoudx9Jizyv2U/u3Jp8ktmhvj4whQ==]
        email: ENC[age-identity,YWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IFgyNTUxOSBTQVBramhuMkpxV0VZMTk3UEhjV3FZSDRuNzdPWDFjNDIwS2JueW5YL0dJCjNRVTdyek1ZSXJYbkZnTzNrMFdJS0t1TW84dE1MOVNrNU1PUlZDY2xua1EKLS0tIFpqNVdScThBYytFWGsrRXZJcTNDSHVRcThqWVVRNlZlbVpsck9RYy9ES0kKnTYTMF1QpyG62W8jEGcM5/DfMKH/6QUSyhdwxlPrjS0nesPEMt/zhD6KWiPgk14kkPiODP17Gs4=]
        home_directory: /home/tess
        shell: /bin/bash
        primary_group: humans
        secondary_groups:
          - pa
