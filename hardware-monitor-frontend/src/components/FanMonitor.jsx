/* eslint-disable no-unused-vars */
/** @format */

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
  ThemeIcon,
} from "@mantine/core";
import {
  IconWind,
  IconAlertTriangle,
  IconCircleCheck,
} from "@tabler/icons-react";
import { getFanInfo } from "../api";

const FanMonitor = () => {
  const [fans, setFans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [anomalyDetected, setAnomalyDetected] = useState(false);

  // Load fan data when component mounts
  useEffect(() => {
    const fetchFanData = async () => {
      try {
        setLoading(true);
        const response = await getFanInfo();
        console.log("Fan data response:", response);
        
        // Make sure you're setting the fans state with the response data
        setFans(response.data);
        
        // Check for anomalies only if there are fans
        if (response.data && response.data.length > 0) {
          const hasAnomaly = response.data.some(
            (fan) =>
              fan.status === "Inactive" ||
              (fan.value && fan.value < 500 && fan.name.includes("CPU"))
          );
          setAnomalyDetected(hasAnomaly);
        }
      } catch (err) {
        console.error("Failed to fetch fan information:", err);
        setError("Failed to load fan information");
      } finally {
        setLoading(false);
      }
    };
    fetchFanData();

    // Set up polling for updated fan data every 30 seconds
    const interval = setInterval(fetchFanData, 30000);

    return () => clearInterval(interval);
  }, []);

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
        <Title order={4}>Cooling System</Title>
        <IconWind size={24} stroke={1.5} />
      </Group>

      {error && (
        <Alert
          icon={<IconAlertTriangle size={16} />}
          title="Error"
          color="red"
          mb="md"
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

          {metrics && metrics.cpu_temp > 0 && (
            <Text size="sm" color="dimmed" align="center" mt="md">
              CPU Temperature: {metrics.cpu_temp.toFixed(1)}°C
            </Text>
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
