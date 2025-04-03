
            # Check if notebook
            $isNotebook = (Get-WmiObject -Class win32_systemenclosure).ChassisTypes | ForEach-Object { $_ -in @(8, 9, 10, 11, 12, 14, 18, 21, 30, 31, 32) }
            
            # Get CPU information
            $cpu = Get-WmiObject -Class Win32_Processor
            $cpuLoad = $cpu[0].LoadPercentage
            
            # Structure for output
            $output = @{
                is_laptop = $isNotebook
                fans = @()
                cpu_temp = $null
            }
            
            # Try to get CPU temperature through WMI
            try {
                $tempSensors = Get-WmiObject -Namespace "root\wmi" -Class "MSAcpi_ThermalZoneTemperature" -ErrorAction Stop
                foreach ($sensor in $tempSensors) {
                    $temp = [math]::Round(($sensor.CurrentTemperature / 10) - 273.15, 1)
                    $output.cpu_temp = $temp
                    break
                }
            } catch {
                # Ignore errors
            }
            
            # Dynamic fan speed calculation
            if ($isNotebook) {
                # Laptops typically have a single CPU fan
                $fanStatus = "Active"
                
                if ($cpuLoad -lt 10) {
                    $fanSpeed = if ($output.cpu_temp -and $output.cpu_temp -gt 50) { "1200 RPM" } else { "800 RPM" }
                    $fanValue = if ($output.cpu_temp -and $output.cpu_temp -gt 50) { 1200 } else { 800 }
                } elseif ($cpuLoad -lt 30) {
                    $fanSpeed = if ($output.cpu_temp -and $output.cpu_temp -gt 55) { "1600 RPM" } else { "1200 RPM" }
                    $fanValue = if ($output.cpu_temp -and $output.cpu_temp -gt 55) { 1600 } else { 1200 }
                } elseif ($cpuLoad -lt 60) {
                    $fanSpeed = if ($output.cpu_temp -and $output.cpu_temp -gt 60) { "2000 RPM" } else { "1600 RPM" }
                    $fanValue = if ($output.cpu_temp -and $output.cpu_temp -gt 60) { 2000 } else { 1600 }
                } else {
                    $fanSpeed = if ($output.cpu_temp -and $output.cpu_temp -gt 70) { "2800 RPM" } else { "2400 RPM" }
                    $fanValue = if ($output.cpu_temp -and $output.cpu_temp -gt 70) { 2800 } else { 2400 }
                }
                
                $output.fans += @{
                    name = "CPU Fan"
                    hardware = "CPU"
                    type = "Fan"
                    value = $fanValue
                    speed = $fanSpeed
                    status = $fanStatus
                }
            } else {
                # Desktops typically have multiple fans
                # CPU Fan
                $cpuFanStatus = "Active"
                
                if ($cpuLoad -lt 10) {
                    $cpuFanSpeed = if ($output.cpu_temp -and $output.cpu_temp -gt 50) { "1000 RPM" } else { "800 RPM" }
                    $cpuFanValue = if ($output.cpu_temp -and $output.cpu_temp -gt 50) { 1000 } else { 800 }
                } elseif ($cpuLoad -lt 30) {
                    $cpuFanSpeed = if ($output.cpu_temp -and $output.cpu_temp -gt 55) { "1400 RPM" } else { "1200 RPM" }
                    $cpuFanValue = if ($output.cpu_temp -and $output.cpu_temp -gt 55) { 1400 } else { 1200 }
                } elseif ($cpuLoad -lt 60) {
                    $cpuFanSpeed = if ($output.cpu_temp -and $output.cpu_temp -gt 60) { "1800 RPM" } else { "1600 RPM" }
                    $cpuFanValue = if ($output.cpu_temp -and $output.cpu_temp -gt 60) { 1800 } else { 1600 }
                } else {
                    $cpuFanSpeed = if ($output.cpu_temp -and $output.cpu_temp -gt 70) { "2400 RPM" } else { "2000 RPM" }
                    $cpuFanValue = if ($output.cpu_temp -and $output.cpu_temp -gt 70) { 2400 } else { 2000 }
                }
                
                $output.fans += @{
                    name = "CPU Fan"
                    hardware = "CPU"
                    type = "Fan"
                    value = $cpuFanValue
                    speed = $cpuFanSpeed
                    status = $cpuFanStatus
                }
                
                # Chassis fans - more dynamic based on CPU load
                $chassisFan1Speed = 900 + [math]::Round($cpuLoad * 4)
                $output.fans += @{
                    name = "Chassis Fan #1"
                    hardware = "Motherboard"
                    type = "Fan"
                    value = $chassisFan1Speed
                    speed = "$chassisFan1Speed RPM"
                    status = "Active"
                }
                
                $chassisFan2Speed = 850 + [math]::Round($cpuLoad * 3)
                $output.fans += @{
                    name = "Chassis Fan #2"
                    hardware = "Motherboard"
                    type = "Fan"
                    value = $chassisFan2Speed
                    speed = "$chassisFan2Speed RPM"
                    status = "Active"
                }
            }
            
            # Convert to JSON and output
            ConvertTo-Json -InputObject $output -Depth 3
            