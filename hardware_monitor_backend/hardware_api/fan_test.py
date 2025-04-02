import platform
import os
import sys
import json
import subprocess

def check_dll_exists():
    """Check if the OpenHardwareMonitor DLL exists."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dll_path = os.path.join(script_dir, "lib", "OpenHardwareMonitorLib.dll")
    exists = os.path.isfile(dll_path)
    print(f"Checking if DLL exists at: {dll_path}")
    print(f"File exists: {exists}")
    return exists, dll_path

def get_fan_info_windows():
    """Get cooling fan information on Windows systems using OpenHardwareMonitor."""
    try:
        import clr  # Python for .NET
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dll_path = os.path.join(script_dir, "lib", "OpenHardwareMonitorLib.dll")
        
        if not os.path.isfile(dll_path):
            print(f"Error: OpenHardwareMonitor DLL not found at {dll_path}")
            return []
        
        # Add the DLL to the Python path
        clr.AddReference(dll_path)
        
        # Import classes from the DLL
        from OpenHardwareMonitor import Hardware
        computer = Hardware.Computer()
        computer.CPUEnabled = True
        computer.MainboardEnabled = True
        computer.GPUEnabled = True
        computer.FanControllerEnabled = True
        
        # Start monitoring
        computer.Open()
        
        fans = []
        
        # Function to recursively get fan sensors
        def get_fans(hardware):
            for sensor in hardware.Sensors:
                if sensor.SensorType == 3:  # SensorType.Fan = 3
                    fans.append({
                        "name": sensor.Name,
                        "hardware": hardware.Name,
                        "type": "Fan",
                        "value": sensor.Value,
                        "speed": f"{sensor.Value:.0f} RPM" if sensor.Value else "0 RPM",
                        "status": "Active" if sensor.Value > 0 else "Inactive"
                    })
            
            for subhardware in hardware.SubHardware:
                get_fans(subhardware)
        
        # Process each hardware component
        for hardware in computer.Hardware:
            hardware.Update()
            get_fans(hardware)
            
            for subhardware in hardware.SubHardware:
                subhardware.Update()
                get_fans(subhardware)
        
        return fans
    
    except Exception as e:
        print(f"Error getting fan information: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def get_fan_info_windows_wmi():
    """Get cooling fan information on Windows using WMI (fallback method)."""
    try:
        import wmi
        
        c = wmi.WMI(namespace="root\wmi")
        fans = []
        
        # Try MSAcpi_ThermalZoneTemperature
        try:
            for thermal_zone in c.MSAcpi_ThermalZoneTemperature():
                print(f"Thermal Zone: {thermal_zone.InstanceName}, Temp: {thermal_zone.CurrentTemperature/10.0-273.15:.1f}°C")
        except Exception as e:
            print(f"Error getting thermal zones: {str(e)}")
        
        # Try using Win32_Fan class (not always available)
        try:
            for fan in c.Win32_Fan():
                fans.append({
                    "name": fan.Name or f"Fan {fan.DeviceID}",
                    "status": "Active" if fan.StatusInfo == 3 else "Inactive",
                    "speed": f"{fan.DesiredSpeed} RPM" if hasattr(fan, 'DesiredSpeed') and fan.DesiredSpeed else "Unknown"
                })
        except Exception as e:
            print(f"Win32_Fan not available: {str(e)}")
        
        # Try using Win32_TemperatureProbe for related info
        try:
            for temp in c.Win32_TemperatureProbe():
                print(f"Temperature probe: {temp.Name or 'Unknown'}, Value: {temp.CurrentReading}")
        except Exception as e:
            print(f"Win32_TemperatureProbe not available: {str(e)}")
            
        # Try using Win32_CoolingDevice
        try:
            for device in c.Win32_CoolingDevice():
                fans.append({
                    "name": device.Name or f"Cooling Device {device.DeviceID}",
                    "status": "Active" if device.StatusInfo == 3 else "Inactive",
                    "speed": "Unknown"
                })
        except Exception as e:
            print(f"Win32_CoolingDevice not available: {str(e)}")
        
        # Try MSAcpi_Cooling class
        try:
            for cooling in c.MSAcpi_Cooling():
                fans.append({
                    "name": f"ACPI Cooling Device {cooling.InstanceName}",
                    "status": "Active" if cooling.Active else "Inactive",
                    "speed": "Unknown"
                })
        except Exception as e:
            print(f"MSAcpi_Cooling not available: {str(e)}")
        
        return fans
    
    except Exception as e:
        print(f"Error using WMI for fan information: {str(e)}")
        return []

def get_fan_info_hwinfo():
    """Try to get fan information using external tools like HWiNFO."""
    try:
        hwinfo_path = "C:\\Program Files\\HWiNFO64\\HWiNFO64.exe"
        if os.path.exists(hwinfo_path):
            print(f"Found HWiNFO at {hwinfo_path}")
            print("You can configure HWiNFO to log sensor data to a CSV file.")
            return []
        
        return []
    except Exception as e:
        print(f"Error checking for HWiNFO: {str(e)}")
        return []

def get_fan_info_from_powershell():
    """Try to get fan information using PowerShell."""
    try:
        ps_script = """
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
        """
        
        ps_file = "fan_check.ps1"
        with open(ps_file, "w") as f:
            f.write(ps_script)
        
        print("\nRunning PowerShell hardware detection...")
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_file],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return []
    
    except Exception as e:
        print(f"Error running PowerShell fan detection: {str(e)}")
        return []

def simulate_fan_info():
    """Provide simulated fan data for development purposes."""
    if platform.system() == "Windows":
        try:
            import wmi
            c = wmi.WMI()
            chassis_types = [chassis.ChassisTypes for chassis in c.Win32_SystemEnclosure()]
            chassis_types = [item for sublist in chassis_types for item in sublist]
            
            is_laptop = any(t in [8, 9, 10, 11, 12, 13, 14, 18, 21] for t in chassis_types)
            
            if is_laptop:
                return [
                    {
                        "name": "CPU Fan",
                        "hardware": "CPU",
                        "type": "Fan",
                        "value": 2400,
                        "speed": "2400 RPM",
                        "status": "Active"
                    }
                ]
            else:
                return [
                    {
                        "name": "CPU Fan",
                        "hardware": "CPU",
                        "type": "Fan",
                        "value": 1200,
                        "speed": "1200 RPM",
                        "status": "Active"
                    },
                    {
                        "name": "Chassis Fan #1",
                        "hardware": "Motherboard",
                        "type": "Fan",
                        "value": 900,
                        "speed": "900 RPM",
                        "status": "Active"
                    },
                    {
                        "name": "Chassis Fan #2",
                        "hardware": "Motherboard",
                        "type": "Fan",
                        "value": 850,
                        "speed": "850 RPM",
                        "status": "Active"
                    }
                ]
        except Exception as e:
            print(f"Error determining chassis type: {str(e)}")
            return [
                {
                    "name": "CPU Fan",
                    "hardware": "CPU",
                    "type": "Fan",
                    "value": 1200,
                    "speed": "1200 RPM",
                    "status": "Active"
                }
            ]
    else:
        return [
            {
                "name": "CPU Fan",
                "hardware": "CPU",
                "type": "Fan",
                "value": 1200,
                "speed": "1200 RPM",
                "status": "Active"
            }
        ]

if __name__ == "__main__":
    print(f"Running on {platform.system()} {platform.version()} ({platform.machine()})")
    
    fans = []
    
    if platform.system() == "Windows":
        exists, dll_path = check_dll_exists()
        
        try:
            import clr
            print("Python for .NET (pythonnet) package is installed.")
            
            print("\nTrying alternate methods to load the DLL...")
            
            try:
                # Import System.Reflection through clr
                clr.AddReference("System.Reflection")
                clr.AddReference("System")
                
                # Now import after referencing the assemblies
                from System import Reflection
                assembly = Reflection.Assembly.LoadFile(dll_path)
                print(f"Successfully loaded assembly: {assembly.FullName}")
            except Exception as e:
                print(f"Error loading assembly with LoadFile: {str(e)}")
            
        except ImportError:
            print("Python for .NET (pythonnet) package is NOT installed.")
        
        if not fans:
            print("\nTrying WMI approach...")
            fans = get_fan_info_windows_wmi()
        
        if not fans:
            print("\nTrying PowerShell approach...")
            powershell_fans = get_fan_info_from_powershell()
            if powershell_fans:
                fans = powershell_fans
        
        if not fans:
            print("\nChecking for HWiNFO...")
            hwinfo_fans = get_fan_info_hwinfo()
            if hwinfo_fans:
                fans = hwinfo_fans
        
        if not fans:
            print("\nUsing simulated fan data for display purposes...")
            fans = simulate_fan_info()
        
        if fans:
            print(f"\nDetected {len(fans)} fans:")
            for i, fan in enumerate(fans, 1):
                print(f"\nFan {i}:")
                for key, value in fan.items():
                    print(f"  {key}: {value}")
        else:
            print("\nNo fans detected or unable to retrieve fan information.")
            
        with open("fan_info.json", "w") as f:
            json.dump(fans, f, indent=2)
        print("\nFan information saved to fan_info.json")
    else:
        print("This test is primarily designed for Windows systems.")