apt:

  sources:
    google-chrome:
      Types: deb
      URIs: http://dl.google.com/linux/chrome/deb/
      Suites: stable
      Components: main
      Signed-By: /etc/apt/keyrings/google-chrome.asc
      Architectures: amd64

    ghostty:
      Types: deb
      URIs: https://ppa.launchpadcontent.net/mkasberg/ghostty-ubuntu/ubuntu/
      Suites: {{ grains.oscodename }}
      Components: main
      Signed-By: /etc/apt/keyrings/ghostty.gpg

  keys:
    ghostty: |
      xsFNBGd0LH8BEAD2aPS7jyRaU8GoZHnOIgKr7znPEZ7x3ujEjBNMIN/sioZvhqcI
      u1DV6w6N9k04TRDHhv7V2hyc4THVaxJE6iQfkQsPGdS4hWx/JKH1tTrVzsIaihIq
      WLxpYV3x4Ve7v73Zg+Frn1Dd0INIsnD4w53k8ZVE+JcCE6oO7DyhBvnnpcrthDWo
      2eGnnsMaRSctbmwT6GIBvQTkxUVtDyZ9RESOBPMIJ/fYAuPhDKwQYYcTcTgGEGh4
      CCR0aKUee92cv6nLDRhkbyGeXDVHO9kj6GM3DPuGXVmCBdltZ1V0QeDhMV+JlkoV
      LA9aj0+aUn1WkgECudC6HqWZlgouyOZfCxMyB4Cz/IEDcyCYjI3icpNJ6dhtMd2s
      MfdBXLiZof2eCt1QO72GCR5LEm9cAztg03LBaTBnm7vSX0nRC4uFFQ2H1AAomUC3
      prU569f4reb9WSZMTFnG+flhFIRv6EHFRQmlhVoPfyLIMKWHwZvFhOBTVO5124f+
      0Mgqkrc57sgphbxOljw2MTIvRCiuHSzBzmZFKFtVfl/wHLXvrCSB69nUJ0ezEcLd
      kG/uONftqJm+BKDEnWFXr558H81SxqV+DTDbwnRr0AoJOUsoEDIUX2uQgp4prfJx
      Q+TW+gaFtWyxJSzvOTyvFpypgfRxZs/MsM9ZltN56lHJB8ptARdcDuRcKwARAQAB
      zR5MYXVuY2hwYWQgUFBBIGZvciBNaWtlIEthc2JlcmfCwY4EEwEKADgWIQQHIf31
      /suI3GkgNhZXyO9FXOrkkQUCZ3QsfwIbAwULCQgHAgYVCgkICwIEFgIDAQIeAQIX
      gAAKCRBXyO9FXOrkkTn7EADowHg70eiJwrSjWrZdxijOapKxblRIkN8zIq0xsRdP
      H8jXuEJwd2k8DQrZpps3XL7bP1XBX4H44LqFWiQQaaMACnaz7YQSM/77XjcbASoR
      HnS9eKUfxo5vqfLwlkMsQaEopJMREwCcpHD2AxPiPtbNa/2RCbf0faA5FsMadYKq
      ctYAmyq6Y+FzVcAIsR26hZglN+XtZeWszA9QYv8DSi4qmL6OsMrq15NP9NTlpKOb
      ntyoUs31/ghMh5HEo1DaI4ETetD5l5vuNQrDr/9yzFILyvEnReB4lmqaQKMCkuXS
      iaosHWmahnw8qhsOlTd7biQEI+uAVe77kR9P7+GMAJitC5gjfkvt0PuaOu40/9pK
      vdTDDC2+Uk86wGY5cuSYM2uBkkUSBFDe6bqV9rJcAXprVAjJwtS5ZUbQ7Hwws0PG
      hio9BIlZHOdEhuQlJ6XGy2+HGjuoMO9KkJNs3mFW6RKp3BH2/Zr5VTdZ0IYsjFjd
      YP6PSDRiFqWpn4UkE+JQJCPdY+do+CgbVicQ7kvmPXMeNr6b6dAAABtiIQlIVVrg
      n8QWhLOXDKLNCUUlDUN2xvAcBP2tVcTwtIRN86lR/wbym7Yx6MApBtAOVXf9WSNy
      Fy7gke85oWlzJCxW/D713HNyV3gR1gGkZoxJ1KGRLYlf+MbzlpmCBSR8h7asFwDD
      hw==

  key_urls:
    google-chrome:
      source: https://dl.google.com/linux/linux_signing_key.pub
      source_hash: sha256=54dea5f6c2a26091578cf52a999cebc6b64df478d37ad4dce96376b711e3b27c
