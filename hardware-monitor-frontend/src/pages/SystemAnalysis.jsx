/* eslint-disable no-unused-vars */
/**
 * eslint-disable no-unused-vars
 *
 * @format
 */


// File: src/pages/SystemAnalysis.jsx
import { useState, useEffect } from "react";
import {
  Container,
  Grid,
  Card,
  Title,
  Text,
  Group,
  Button,
  List,
  ThemeIcon,
  Stack,
  Divider,
  Progress,
  Badge,
  Skeleton,
  useMantineTheme,
} from "@mantine/core";
import {
  IconDeviceDesktop,
  IconCpu,
  IconDeviceGamepad,
  IconDeviceLaptop,
  IconCheck,
  IconX,
  IconInfoCircle,
  IconRefresh,
  IconWind,
} from "@tabler/icons-react";
import { getLatestMetrics, getSystemSummary, getSystemInfo } from "../api";

// Gaming requirements based on common standards
const GAMING_REQUIREMENTS = {
  BASIC: {
    cpu_percent_max: 85,
    memory_min_gb: 4,
    disk_free_min_gb: 50,
    gpu_memory_min_gb: 2,
  },
  MEDIUM: {
    cpu_percent_max: 75,
    memory_min_gb: 8,
    disk_free_min_gb: 100,
    gpu_memory_min_gb: 4,
  },
  HIGH: {
    cpu_percent_max: 60,
    memory_min_gb: 16,
    disk_free_min_gb: 200,
    gpu_memory_min_gb: 6,
  },
};

// Development requirements
const DEV_REQUIREMENTS = {
  WEB_DEV: {
    cpu_percent_max: 80,
    memory_min_gb: 8,
    disk_free_min_gb: 50,
  },
  MOBILE_DEV: {
    cpu_percent_max: 70,
    memory_min_gb: 16,
    disk_free_min_gb: 80,
  },
  DATA_SCIENCE: {
    cpu_percent_max: 60,
    memory_min_gb: 16,
    disk_free_min_gb: 100,
  },
};

// Helper function to extract memory size in GB from string like "16.00GB"
const extractMemoryGB = (memoryStr) => {
  if (!memoryStr) return 0;
  const match = memoryStr.match(/(\d+(\.\d+)?)/);
  return match ? parseFloat(match[1]) : 0;
};

// Helper function to extract disk size in GB
const extractDiskGB = (sizeStr) => {
  if (!sizeStr) return 0;
  if (sizeStr.includes("TB")) {
    return parseFloat(sizeStr) * 1024; // Convert TB to GB
  } else if (sizeStr.includes("GB")) {
    return parseFloat(sizeStr);
  } else if (sizeStr.includes("MB")) {
    return parseFloat(sizeStr) / 1024; // Convert MB to GB
  }
  return 0;
};

const SystemAnalysis = () => {
  const [metrics, setMetrics] = useState(null);
  const [systemInfo, setSystemInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const theme = useMantineTheme();

  const fetchData = async () => {
    setLoading(true);
    try {
      const [metricsRes, systemInfoRes] = await Promise.all([
        getLatestMetrics(),
        getSystemInfo(),
      ]);
      setMetrics(metricsRes.data);

      // Process real system information
      if (systemInfoRes.data) {
        // Extract total memory in GB
        const memoryGB = extractMemoryGB(systemInfoRes.data.memory?.total);

        // Get CPU details
        const cpuInfo = {
          model: systemInfoRes.data.cpu?.processor || "Unknown",
          cores: systemInfoRes.data.cpu?.physical_cores || 0,
          threads: systemInfoRes.data.cpu?.total_cores || 0,
          base_clock: systemInfoRes.data.cpu?.min_frequency || "Unknown",
          boost_clock: systemInfoRes.data.cpu?.max_frequency || "Unknown",
        };

        // Get GPU details
        let gpuInfo = {
          model: "Integrated Graphics",
          memory_gb: 1,
        };

        if (systemInfoRes.data.gpu && systemInfoRes.data.gpu.length > 0) {
          const primaryGpu = systemInfoRes.data.gpu[0];
          gpuInfo = {
            model: primaryGpu.name || "Unknown GPU",
            memory_gb: extractMemoryGB(primaryGpu.total_memory) || 1,
          };
        }

        // Get storage details
        let storageInfo = {
          total_gb: 0,
          free_gb: 0,
          type: "Unknown",
        };

        if (systemInfoRes.data.disks && systemInfoRes.data.disks.length > 0) {
          const primaryDisk = systemInfoRes.data.disks[0];
          const total = extractDiskGB(primaryDisk.total_size);
          const free = extractDiskGB(primaryDisk.free);

          storageInfo = {
            total_gb: total,
            free_gb: free,
            type: primaryDisk.file_system_type || "HDD",
          };
        }

        // Get fan details
        let fanInfo = {
          hasFans: false,
          fans: [],
        };

        if (systemInfoRes.data.fans && systemInfoRes.data.fans.length > 0) {
          fanInfo = {
            hasFans: true,
            fans: systemInfoRes.data.fans.map((fan) => ({
              name: fan.name || "Unknown Fan",
              speed: fan.speed || "Unknown",
              status: fan.status || "Unknown",
            })),
          };
        }

        // Build system info object
        setSystemInfo({
          cpu: cpuInfo,
          memory: {
            total_gb: memoryGB,
            type: "RAM",
            speed: systemInfoRes.data.cpu?.current_frequency || "Unknown",
          },
          storage: storageInfo,
          gpu: gpuInfo,
          fans: fanInfo,
        });
      }
    } catch (error) {
      console.error("Error fetching system data:", error);

      // Fallback to demo data if real data can't be fetched
      setSystemInfo({
        cpu: {
          model: "Intel Core i7-10700K",
          cores: 8,
          threads: 16,
          base_clock: "3.8 GHz",
          boost_clock: "5.1 GHz",
        },
        memory: {
          total_gb: 32,
          type: "DDR4",
          speed: "3200 MHz",
        },
        storage: {
          total_gb: 1000,
          free_gb: 450,
          type: "SSD",
        },
        gpu: {
          model: "NVIDIA GeForce RTX 3070",
          memory_gb: 8,
        },
        fans: {
          hasFans: true,
          fans: [
            { name: "CPU Fan", speed: "1200 RPM", status: "Active" },
            { name: "Case Fan", speed: "800 RPM", status: "Active" },
          ],
        },
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  // Analyze system suitability for gaming
  const analyzeGaming = () => {
    if (!systemInfo) return null;

    // Calculate scores for each gaming level
    const basicScore = calculateGamingScore(GAMING_REQUIREMENTS.BASIC);
    const mediumScore = calculateGamingScore(GAMING_REQUIREMENTS.MEDIUM);
    const highScore = calculateGamingScore(GAMING_REQUIREMENTS.HIGH);

    let suitableFor = "Not suitable for gaming";
    let score = 0;
    let color = "red";

    if (highScore >= 80) {
      suitableFor = "High-End Gaming";
      score = highScore;
      color = "green";
    } else if (mediumScore >= 80) {
      suitableFor = "Mid-Range Gaming";
      score = mediumScore;
      color = "blue";
    } else if (basicScore >= 80) {
      suitableFor = "Basic Gaming";
      score = basicScore;
      color = "yellow";
    }

    return {
      suitableFor,
      score,
      color,
      details: {
        basic: basicScore,
        medium: mediumScore,
        high: highScore,
      },
    };
  };

  // Calculate gaming score based on requirements
  const calculateGamingScore = (requirements) => {
    let score = 0;

    // CPU check (lower usage is better)
    const cpuScore =
      metrics?.cpu_percent <= requirements.cpu_percent_max
        ? 100
        : 100 - (metrics.cpu_percent - requirements.cpu_percent_max) * 5;

    // Memory check
    const memoryScore =
      systemInfo.memory.total_gb >= requirements.memory_min_gb
        ? 100
        : (systemInfo.memory.total_gb / requirements.memory_min_gb) * 100;

    // Disk space check
    const diskScore =
      systemInfo.storage.free_gb >= requirements.disk_free_min_gb
        ? 100
        : (systemInfo.storage.free_gb / requirements.disk_free_min_gb) * 100;

    // GPU check
    const gpuScore =
      systemInfo.gpu.memory_gb >= requirements.gpu_memory_min_gb
        ? 100
        : (systemInfo.gpu.memory_gb / requirements.gpu_memory_min_gb) * 100;

    // Calculate total score (weighted average)
    score =
      cpuScore * 0.3 + memoryScore * 0.3 + diskScore * 0.2 + gpuScore * 0.2;

    return Math.min(100, Math.round(score));
  };

  // Analyze system for development tasks
  const analyzeDevelopment = () => {
    if (!systemInfo) return null;

    const webDevScore = calculateDevScore(DEV_REQUIREMENTS.WEB_DEV);
    const mobileDevScore = calculateDevScore(DEV_REQUIREMENTS.MOBILE_DEV);
    const dataScienceScore = calculateDevScore(DEV_REQUIREMENTS.DATA_SCIENCE);

    const results = [
      {
        task: "Web Development",
        score: webDevScore,
        suitable: webDevScore >= 80,
      },
      {
        task: "Mobile Development",
        score: mobileDevScore,
        suitable: mobileDevScore >= 80,
      },
      {
        task: "Data Science/ML",
        score: dataScienceScore,
        suitable: dataScienceScore >= 80,
      },
    ];

    return results;
  };

  // Calculate development score based on requirements
  const calculateDevScore = (requirements) => {
    let score = 0;

    // CPU check (lower usage is better)
    const cpuScore =
      metrics?.cpu_percent <= requirements.cpu_percent_max
        ? 100
        : 100 - (metrics.cpu_percent - requirements.cpu_percent_max) * 5;

    // Memory check
    const memoryScore =
      systemInfo.memory.total_gb >= requirements.memory_min_gb
        ? 100
        : (systemInfo.memory.total_gb / requirements.memory_min_gb) * 100;

    // Disk space check
    const diskScore =
      systemInfo.storage.free_gb >= requirements.disk_free_min_gb
        ? 100
        : (systemInfo.storage.free_gb / requirements.disk_free_min_gb) * 100;

    // Calculate total score (weighted average)
    score = cpuScore * 0.4 + memoryScore * 0.4 + diskScore * 0.2;

    return Math.min(100, Math.round(score));
  };

  const gamingAnalysis = analyzeGaming();
  const devAnalysis = analyzeDevelopment();

  return (
    <Container fluid>
      <Group position="apart" mb="md">
        <Title order={2}>System Analysis</Title>
        <Button
          leftSection={<IconRefresh size={18} />}
          onClick={handleRefresh}
          loading={refreshing}
        >
          Refresh Hardware Info
        </Button>
      </Group>

      <Grid>
        {/* System Specifications */}
        <Grid.Col span={12} lg={6}>
          <Card shadow="sm" withBorder>
            <Group position="apart" mb="md">
              <Title order={4}>Hardware Specifications</Title>
              <IconDeviceLaptop size={24} />
            </Group>

            {loading ? (
              <Stack spacing="md">
                <Skeleton height={20} radius="sm" />
                <Skeleton height={20} radius="sm" />
                <Skeleton height={20} radius="sm" />
                <Divider my="xs" />
                <Skeleton height={20} radius="sm" />
                <Skeleton height={20} radius="sm" />
                <Divider my="xs" />
                <Skeleton height={20} radius="sm" />
                <Skeleton height={20} radius="sm" />
              </Stack>
            ) : (
              systemInfo && (
                <>
                  <Stack spacing="xs">
                    <Group position="apart">
                      <Text weight={500}>CPU</Text>
                      <Text>{systemInfo.cpu.model}</Text>
                    </Group>
                    <Group position="apart">
                      <Text size="sm" color="dimmed">
                        Cores / Threads
                      </Text>
                      <Text>
                        {systemInfo.cpu.cores} / {systemInfo.cpu.threads}
                      </Text>
                    </Group>
                    <Group position="apart">
                      <Text size="sm" color="dimmed">
                        Clock Speed
                      </Text>
                      <Text>
                        {systemInfo.cpu.base_clock} (Boost:{" "}
                        {systemInfo.cpu.boost_clock})
                      </Text>
                    </Group>

                    <Divider my="xs" />

                    <Group position="apart">
                      <Text weight={500}>Memory</Text>
                      <Text>
                        {systemInfo.memory.total_gb.toFixed(1)} GB{" "}
                        {systemInfo.memory.type}
                      </Text>
                    </Group>
                    <Group position="apart">
                      <Text size="sm" color="dimmed">
                        Speed
                      </Text>
                      <Text>{systemInfo.memory.speed}</Text>
                    </Group>

                    <Divider my="xs" />

                    <Group position="apart">
                      <Text weight={500}>Storage</Text>
                      <Text>
                        {systemInfo.storage.type}{" "}
                        {systemInfo.storage.total_gb.toFixed(1)} GB
                      </Text>
                    </Group>
                    <Group position="apart">
                      <Text size="sm" color="dimmed">
                        Free Space
                      </Text>
                      <Text>{systemInfo.storage.free_gb.toFixed(1)} GB</Text>
                    </Group>

                    <Divider my="xs" />

                    <Group position="apart">
                      <Text weight={500}>Graphics</Text>
                      <Text>{systemInfo.gpu.model}</Text>
                    </Group>
                    <Group position="apart">
                      <Text size="sm" color="dimmed">
                        VRAM
                      </Text>
                      <Text>{systemInfo.gpu.memory_gb.toFixed(1)} GB</Text>
                    </Group>

                    {/* Fan Section */}
                    {systemInfo?.fans?.hasFans && (
                      <>
                        <Divider my="xs" />

                        <Group position="apart">
                          <Text weight={500}>Cooling Fans</Text>
                          <IconWind size={20} />
                        </Group>

                        {systemInfo.fans.fans.map((fan, index) => (
                          <Group key={index} position="apart">
                            <Text size="sm" color="dimmed">
                              {fan.name || `Fan ${index + 1}`}
                            </Text>
                            <Badge
                              color={
                                fan.status === "Active"
                                  ? "green"
                                  : fan.status === "Inactive"
                                    ? "orange"
                                    : "gray"
                              }
                              variant="light"
                            >
                              {fan.speed || fan.status}
                            </Badge>
                          </Group>
                        ))}
                      </>
                    )}
                  </Stack>
                </>
              )
            )}
          </Card>
        </Grid.Col>

        {/* Gaming Suitability */}
        <Grid.Col span={12} lg={6}>
          <Card shadow="sm" withBorder>
            <Group position="apart" mb="md">
              <Title order={4}>Gaming Compatibility</Title>
              <IconDeviceGamepad size={24} />
            </Group>

            {loading ? (
              <Stack spacing="md">
                <Skeleton height={40} radius="sm" />
                <Skeleton height={30} radius="lg" />
                <Divider my="xs" />
                <Skeleton height={25} radius="sm" />
                <Skeleton height={25} radius="sm" />
                <Skeleton height={25} radius="sm" />
              </Stack>
            ) : (
              gamingAnalysis && (
                <>
                  <Group position="center" mb="md">
                    <Badge size="xl" color={gamingAnalysis.color} radius="sm">
                      {gamingAnalysis.suitableFor}
                    </Badge>
                  </Group>

                  <Stack spacing="xs" mb="md">
                    <Text weight={500} align="center">
                      Overall Gaming Score
                    </Text>
                    <Progress
                      value={gamingAnalysis.score}
                      color={gamingAnalysis.color}
                      size="xl"
                      radius="xl"
                      label={`${gamingAnalysis.score}%`}
                    />
                  </Stack>

                  <Divider
                    my="md"
                    label="Gaming Capability Breakdown"
                    labelPosition="center"
                  />

                  <Stack spacing="xs">
                    <Group position="apart">
                      <Text>Basic Gaming</Text>
                      <Progress
                        value={gamingAnalysis.details.basic}
                        color={
                          gamingAnalysis.details.basic >= 80
                            ? "green"
                            : "orange"
                        }
                        size="lg"
                        radius="xl"
                        label={`${gamingAnalysis.details.basic}%`}
                        style={{ width: 120 }}
                      />
                    </Group>

                    <Group position="apart">
                      <Text>Mid-Range Gaming</Text>
                      <Progress
                        value={gamingAnalysis.details.medium}
                        color={
                          gamingAnalysis.details.medium >= 80
                            ? "green"
                            : "orange"
                        }
                        size="lg"
                        radius="xl"
                        label={`${gamingAnalysis.details.medium}%`}
                        style={{ width: 120 }}
                      />
                    </Group>

                    <Group position="apart">
                      <Text>High-End Gaming</Text>
                      <Progress
                        value={gamingAnalysis.details.high}
                        color={
                          gamingAnalysis.details.high >= 80 ? "green" : "orange"
                        }
                        size="lg"
                        radius="xl"
                        label={`${gamingAnalysis.details.high}%`}
                        style={{ width: 120 }}
                      />
                    </Group>
                  </Stack>
                </>
              )
            )}
          </Card>
        </Grid.Col>

        {/* Development Suitability */}
        <Grid.Col span={12}>
          <Card shadow="sm" withBorder>
            <Title order={4} mb="md">
              Development Tasks Compatibility
            </Title>

            {loading ? (
              <Grid>
                {[1, 2, 3].map((i) => (
                  <Grid.Col key={i} span={12} md={4}>
                    <Card shadow="xs" withBorder>
                      <Skeleton height={30} width="70%" mb="md" radius="sm" />
                      <Skeleton height={25} radius="lg" mb="md" />
                      <Skeleton height={15} width="90%" radius="sm" />
                      <Skeleton height={15} width="80%" mt="xs" radius="sm" />
                    </Card>
                  </Grid.Col>
                ))}
              </Grid>
            ) : (
              devAnalysis && (
                <Grid>
                  {devAnalysis.map((dev) => (
                    <Grid.Col key={dev.task} span={12} md={4}>
                      <Card shadow="xs" withBorder>
                        <Group position="apart" mb="xs">
                          <Text weight={500}>{dev.task}</Text>
                          <ThemeIcon
                            color={dev.suitable ? "green" : "red"}
                            size={24}
                            radius="xl"
                          >
                            {dev.suitable ? (
                              <IconCheck size={18} />
                            ) : (
                              <IconX size={18} />
                            )}
                          </ThemeIcon>
                        </Group>

                        <Progress
                          value={dev.score}
                          color={
                            dev.score >= 80
                              ? "green"
                              : dev.score >= 60
                                ? "orange"
                                : "red"
                          }
                          size="lg"
                          radius="xl"
                          label={`${dev.score}%`}
                          mb="md"
                        />

                        <Text size="sm">
                          Your system is{" "}
                          {dev.suitable ? "suitable" : "not optimal"} for{" "}
                          {dev.task.toLowerCase()}.
                        </Text>

                        {!dev.suitable && (
                          <Text size="sm" color="dimmed" mt="xs">
                            Consider upgrading your hardware for better
                            performance.
                          </Text>
                        )}
                      </Card>
                    </Grid.Col>
                  ))}
                </Grid>
              )
            )}
          </Card>
        </Grid.Col>

        {/* Recommendations */}
        <Grid.Col span={12}>
          <Card shadow="sm" withBorder>
            <Group position="apart" mb="md">
              <Title order={4}>Recommendations</Title>
              <IconInfoCircle size={24} />
            </Group>

            {loading ? (
              <Stack spacing="sm">
                <Skeleton height={20} radius="sm" />
                <Skeleton height={20} radius="sm" />
                <Skeleton height={20} radius="sm" />
              </Stack>
            ) : (
              <List spacing="sm">
                {metrics?.cpu_percent > 80 && (
                  <List.Item>
                    <Text>
                      Your CPU usage is high. Consider closing unused
                      applications or upgrading your CPU.
                    </Text>
                  </List.Item>
                )}

                {metrics?.memory_percent > 80 && (
                  <List.Item>
                    <Text>
                      Your memory usage is high. Adding more RAM would improve
                      system performance.
                    </Text>
                  </List.Item>
                )}

                {systemInfo?.storage.free_gb < 50 && (
                  <List.Item>
                    <Text>
                      Your storage space is low. Free up disk space or add
                      additional storage.
                    </Text>
                  </List.Item>
                )}

                {/* Game-specific recommendations */}
                {gamingAnalysis?.score < 80 && gamingAnalysis?.score >= 60 && (
                  <List.Item>
                    <Text>
                      For better gaming performance, consider upgrading your GPU
                      or adding more RAM.
                    </Text>
                  </List.Item>
                )}

                {gamingAnalysis?.score < 60 && (
                  <List.Item>
                    <Text>
                      Your system will struggle with modern games. Consider a
                      significant hardware upgrade.
                    </Text>
                  </List.Item>
                )}

                {/* Development-specific recommendations */}
                {devAnalysis && devAnalysis.some((dev) => !dev.suitable) && (
                  <List.Item>
                    <Text>
                      For better development performance, consider upgrading to
                      at least 16GB RAM and an SSD with ample free space.
                    </Text>
                  </List.Item>
                )}

                {/* General recommendations */}
                <List.Item>
                  <Text>
                    Regular system maintenance can help keep your hardware
                    running smoothly.
                  </Text>
                </List.Item>

                <List.Item>
                  <Text>
                    Keep your drivers updated for optimal performance and
                    compatibility.
                  </Text>
                </List.Item>
              </List>
            )}
          </Card>
        </Grid.Col>
      </Grid>
    </Container>
  );
};

export default SystemAnalysis;
