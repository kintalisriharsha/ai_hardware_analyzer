
        $computer = $env:COMPUTERNAME
        
        # Try to get fan information
        Write-Host "--- Attempting to get fan information ---"
        
        # Check if notebook
        $isNotebook = (Get-WmiObject -Class win32_systemenclosure).ChassisTypes | ForEach-Object { $_ -in @(8, 9, 10, 11, 12, 14, 18, 21, 30, 31, 32) }
        
        if ($isNotebook) {
            Write-Host "System is a notebook/laptop"
            
            # Try to get fan information through WMI
            try {
                $fans = Get-WmiObject -Namespace "root\wmi" -Class "MSAcpi_ThermalZoneTemperature" -ErrorAction Stop
                foreach ($fan in $fans) {
                    $temp = [math]::Round(($fan.CurrentTemperature / 10) - 273.15, 1)
                    Write-Host "Thermal Zone: $($fan.InstanceName), Temperature: $temp C"
                }
            } catch {
                Write-Host "Could not get thermal zone information: $_"
            }
            
            # Get CPU temperature through hardware monitoring
            Write-Host "Checking for CPU and fan sensors..."
            
            # Battery information might help infer fan activity
            $battery = Get-WmiObject -Class Win32_Battery
            if ($battery) {
                Write-Host "Battery Information:"
                Write-Host "  Status: $($battery.Status)"
                Write-Host "  Health: $($battery.BatteryStatus)"
                Write-Host "  Charge remaining: $($battery.EstimatedChargeRemaining)%"
            }
        } else {
            Write-Host "System is a desktop"
        }
        
        # Additional CPU information that might help infer fan activity
        $cpu = Get-WmiObject -Class Win32_Processor
        foreach ($proc in $cpu) {
            Write-Host "CPU: $($proc.Name)"
            Write-Host "  Load: $($proc.LoadPercentage)%"
            if ($proc.CurrentVoltage) {
                Write-Host "  Voltage: $($proc.CurrentVoltage / 10.0) V"
            }
            if ($proc.CurrentClockSpeed) {
                Write-Host "  Clock: $($proc.CurrentClockSpeed) MHz"
            }
        }
        
        # Try to get motherboard info
        try {
            $baseboard = Get-WmiObject -Class Win32_BaseBoard
            Write-Host "Motherboard: $($baseboard.Manufacturer) $($baseboard.Product)"
        } catch {
            Write-Host "Could not get motherboard information"
        }
        