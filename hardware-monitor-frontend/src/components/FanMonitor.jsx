/* eslint-disable no-unused-vars */
import React, { useState, useEffect } from "react";
import {
  Card,
  Group,
  Title,
  Text,
  Stack,
  RingProgress,
  Badge,
  Skeleton,
  Alert,
  Button,
  useMantineTheme
} from "@mantine/core";
import {
  IconWind,
  IconAlertTriangle,
  IconCircleCheck,
  IconRefresh,
  IconTemperature
} from "@tabler/icons-react";

const FanMonitor = () => {
  const [fans, setFans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [anomalyDetected, setAnomalyDetected] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const theme = useMantineTheme();

  // Function to fetch fan data
  const fetchFanData = async () => {
    try {
      setRefreshing(true);
      
      // Add cache-busting timestamp
      const timestamp = new Date().getTime();
      const response = await fetch(`/api/fans/?t=${timestamp}`);
      
      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }
      
      const data = await response.json();
      console.log("Fan data:", data);
      
      if (Array.isArray(data)) {
        setFans(data);
        
        // Check for anomalies
        const hasAnomaly = data.some(
          (fan) =>
            fan.status === "Inactive" ||
            (fan.value && fan.value < 500 && fan.name.includes("CPU"))
        );
        setAnomalyDetected(hasAnomaly);
        setLastUpdated(new Date());
        setError(null);
      } else {
        throw new Error("Invalid data format received");
      }
    } catch (err) {
      console.error("Failed to fetch fan information:", err);
      setError(`Failed to load fan information: ${err.message}`);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Load fan data when component mounts
  useEffect(() => {
    fetchFanData();

    // Set up polling for updated fan data every 5 seconds
    const interval = setInterval(fetchFanData, 5000);
    return () => clearInterval(interval);
  }, []);

  // Handle manual refresh
  const handleRefresh = () => {
    fetchFanData();
  };

  // Function to get fan speed color based on RPM
  const getFanSpeedColor = (speed) => {
    if (!speed) return "gray";
    const rpm =
      typeof speed === "number" ? speed : parseInt(speed.replace(/[^\d]/g, ""));

    if (rpm === 0) return "red";
    if (rpm < 800) return "orange";
    if (rpm > 2500) return "yellow";
    return "green";
  };

  // Function to calculate progress percentage based on fan speed
  const calculateFanProgress = (speed) => {
    if (!speed) return 0;
    const rpm =
      typeof speed === "number" ? speed : parseInt(speed.replace(/[^\d]/g, ""));

    // Assuming max RPM is 3000
    const maxRpm = 3000;
    return Math.min(100, (rpm / maxRpm) * 100);
  };

  // Function to get anomaly message
  const getAnomalyMessage = () => {
    if (!fans.length) return "";

    const inactiveFans = fans.filter((fan) => fan.status === "Inactive");
    if (inactiveFans.length > 0) {
      return `${inactiveFans.length} cooling fan(s) are not spinning. This may lead to overheating issues.`;
    }

    const lowSpeedFans = fans.filter(
      (fan) =>
        fan.status === "Active" &&
        fan.value &&
        fan.value < 500 &&
        fan.name.includes("CPU")
    );

    if (lowSpeedFans.length > 0) {
      return "CPU fan is running at a very low speed. Check for obstructions or hardware issues.";
    }

    return "Abnormal fan behavior detected. Monitor system temperatures.";
  };

  return (
    <Card shadow="sm" withBorder>
      <Group position="apart" mb="md">
        <Group>
          <IconWind size={24} stroke={1.5} />
          <Title order={4}>Cooling System</Title>
        </Group>
        <Group>
          {lastUpdated && (
            <Text size="xs" color="dimmed">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </Text>
          )}
          <Button
            variant="light"
            size="xs"
            onClick={handleRefresh}
            loading={refreshing}
            leftIcon={<IconRefresh size={16} />}
          >
            Refresh
          </Button>
        </Group>
      </Group>

      {error && (
        <Alert
          icon={<IconAlertTriangle size={16} />}
          title="Error"
          color="red"
          mb="md"
          withCloseButton
          onClose={() => setError(null)}
        >
          {error}
        </Alert>
      )}

      {anomalyDetected && (
        <Alert
          icon={<IconAlertTriangle size={16} />}
          title="Cooling Anomaly Detected"
          color="red"
          mb="md"
        >
          {getAnomalyMessage()}
        </Alert>
      )}

      {loading ? (
        <Stack spacing="md">
          <Skeleton height={80} circle />
          <Skeleton height={20} width="60%" mx="auto" />
          <Skeleton height={15} width="40%" mx="auto" />
        </Stack>
      ) : fans.length > 0 ? (
        <>
          {fans.map((fan, index) => (
            <Group
              key={index}
              position="apart"
              mb={index < fans.length - 1 ? "md" : 0}
            >
              <Stack spacing={4}>
                <Text weight={500}>{fan.name}</Text>
                <Text size="sm" color="dimmed">
                  {fan.hardware || "System"}
                </Text>
                {fan.temperature && (
                  <Group spacing={4}>
                    <IconTemperature size={14} />
                    <Text size="xs" color="dimmed">
                      {fan.temperature}°C
                    </Text>
                  </Group>
                )}
              </Stack>

              <Group spacing="md">
                <Badge
                  color={fan.status === "Active" ? "green" : "red"}
                  variant="light"
                >
                  {fan.status}
                </Badge>

                <RingProgress
                  size={80}
                  thickness={8}
                  roundCaps
                  sections={[
                    {
                      value: calculateFanProgress(fan.value),
                      color: getFanSpeedColor(fan.value),
                    },
                  ]}
                  label={
                    <Text size="xs" align="center" weight={700}>
                      {fan.speed}
                    </Text>
                  }
                />
              </Group>
            </Group>
          ))}

          {!anomalyDetected && fans.every((fan) => fan.status === "Active") && (
            <Alert
              icon={<IconCircleCheck size={16} />}
              title="All Fans Operational"
              color="green"
              variant="light"
              mt="md"
            >
              All cooling fans are functioning properly.
            </Alert>
          )}
        </>
      ) : (
        <Stack align="center" spacing="sm" my="md">
          <IconWind size={40} color="gray" />
          <Text align="center" color="dimmed">
            No cooling fan information available
          </Text>
          <Text size="xs" color="dimmed" align="center">
            Your system may not expose fan sensor data
          </Text>
        </Stack>
      )}
    </Card>
  );
};

export default FanMonitor;