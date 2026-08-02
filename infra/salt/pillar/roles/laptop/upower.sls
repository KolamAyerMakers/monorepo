upower:
  config:
    UPower:
      EnableWattsUpPro: false
      NoPollBatteries: false
      IgnoreLid: false
    BatteryLevel:
      UsePercentageForPolicy: true
      PercentageLow: 15
      PercentageCritical: 5
      PercentageAction: 2
      CriticalPowerAction: HybridSleep
