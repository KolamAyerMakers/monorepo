kam_classroom:
  weather_egress:
    nftables_file: /etc/nftables.d/49-classroom-weather-egress.nft
    header: "# Classroom weather API egress policy"
    destination: classroom-weather
    set_v4: classroom_weather_v4
    set_v6: classroom_weather_v6
    destination_position: '29'
    domain_position: '69'
    tcp_port: 443
    domains:
      - api.open-meteo.com
      - air-quality-api.open-meteo.com
