// src/pages/Dashboard.jsx
import { useState, useEffect } from 'react';
import { 
  Container, 
  Grid, 
  Card, 
  Title, 
  Text, 
  Group, 
  Badge, 
  Button, 
  Divider,
  RingProgress,
  useMantineTheme,
  Stack,
} from '@mantine/core';
import { 
  IconCpu, 
  IconDatabase, 
  IconTemperature, 
  IconAlertTriangle,
  IconDeviceLaptop,
  IconRefresh
} from '@tabler/icons-react';
import { LineChart } from '@mantine/charts';
import { getLatestMetrics, getSystemSummary, collectMetrics, getUnresolvedIssues } from '../api';
import FanMonitor from '../components/FanMonitor';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState(null);
  const [summary, setSummary] = useState(null);
  const [issues, setIssues] = useState([]);
  const theme = useMantineTheme();

  const fetchData = async () => {
    setLoading(true);
    try {
      const [metricsRes, summaryRes, issuesRes] = await Promise.all([
        getLatestMetrics(),
        getSystemSummary(),
        getUnresolvedIssues()
      ]);
      setMetrics(metricsRes.data);
      setSummary(summaryRes.data);
      setIssues(issuesRes.data.results || issuesRes.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    try {
      await collectMetrics();
      fetchData();
    } catch (error) {
      console.error('Error collecting metrics:', error);
    }
  };

  useEffect(() => {
    fetchData();
    // Refresh data every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const cpuColor = metrics?.cpu_percent > 80 ? 'red' : metrics?.cpu_percent > 60 ? 'orange' : 'green';
  const memoryColor = metrics?.memory_percent > 80 ? 'red' : metrics?.memory_percent > 60 ? 'orange' : 'green';
  const diskColor = metrics?.disk_usage_percent > 80 ? 'red' : metrics?.disk_usage_percent > 60 ? 'orange' : 'green';

  const chartData = summary?.trends?.cpu?.map((value, index) => ({
    date: `T-${summary.trends.cpu.length - index}`,
    CPU: value,
    Memory: summary.trends.memory[index],
    Disk: summary.trends.disk[index],
  })).reverse() || [];

  return (
    <Container fluid>
      <Group position="apart" mb="md">
        <Title order={2}>System Dashboard</Title>
        <Button 
          leftIcon={<IconRefresh size={18} />} 
          onClick={handleRefresh} 
          loading={loading}
        >
          Refresh
        </Button>
      </Group>

      <Grid>
        {/* System Resource Cards */}
        <Grid.Col span={12} lg={4}>
          <Card shadow="sm" withBorder>
            <Group position="apart">
              <Text weight={500}>CPU Usage</Text>
              <IconCpu size={24} stroke={1.5} />
            </Group>
            <RingProgress
              sections={[{ value: metrics?.cpu_percent || 0, color: cpuColor }]}
              label={
                <Text size="xl" align="center" weight={700}>
                  {metrics?.cpu_percent?.toFixed(1) || 0}%
                </Text>
              }
              size={140}
              thickness={14}
              roundCaps
              my="md"
              mx="auto"
            />
          </Card>
        </Grid.Col>

        <Grid.Col span={12} lg={4}>
          <Card shadow="sm" withBorder>
            <Group position="apart">
              <Text weight={500}>Memory Usage</Text>
              <IconDatabase size={24} stroke={1.5} />
            </Group>
            <RingProgress
              sections={[{ value: metrics?.memory_percent || 0, color: memoryColor }]}
              label={
                <Text size="xl" align="center" weight={700}>
                  {metrics?.memory_percent?.toFixed(1) || 0}%
                </Text>
              }
              size={140}
              thickness={14}
              roundCaps
              my="md"
              mx="auto"
            />
          </Card>
        </Grid.Col>

        <Grid.Col span={12} lg={4}>
          <Card shadow="sm" withBorder>
            <Group position="apart">
              <Text weight={500}>Disk Usage</Text>
              <IconDatabase size={24} stroke={1.5} />
            </Group>
            <RingProgress
              sections={[{ value: metrics?.disk_usage_percent || 0, color: diskColor }]}
              label={
                <Text size="xl" align="center" weight={700}>
                  {metrics?.disk_usage_percent?.toFixed(1) || 0}%
                </Text>
              }
              size={140}
              thickness={14}
              roundCaps
              my="md"
              mx="auto"
            />
          </Card>
        </Grid.Col>

        {/* System Status Chart */}
        <Grid.Col span={12}>
          <Card shadow="sm" withBorder>
            <Title order={4} mb="md">System Resource History</Title>
            <LineChart
              h={300}
              data={chartData}
              dataKey="date"
              series={[
                { name: 'CPU', color: theme.colors.blue[6] },
                { name: 'Memory', color: theme.colors.green[6] },
                { name: 'Disk', color: theme.colors.orange[6] },
              ]}
              withLegend
              yAxisProps={{ domain: [0, 100] }}
            />
          </Card>
        </Grid.Col>

        {/* Hardware Issues */}
        <Grid.Col span={12}>
          <Card shadow="sm" withBorder>
            <Group position="apart" mb="md">
              <Title order={4}>Hardware Issues</Title>
              <Badge size="lg" color={issues.length > 0 ? 'red' : 'green'}>
                {issues.length > 0 ? `${issues.length} Issues` : 'No Issues'}
              </Badge>
            </Group>

            {issues.length > 0 ? (
              <Stack spacing="xs">
                {issues.map((issue) => (
                  <Card key={issue.id} shadow="xs" withBorder>
                    <Group position="apart">
                      <Group>
                        <IconAlertTriangle color={theme.colors.red[6]} />
                        <Text weight={500}>{issue.issue_type}</Text>
                      </Group>
                      <Badge>{new Date(issue.timestamp).toLocaleString()}</Badge>
                    </Group>
                    <Text size="sm" color="dimmed" mt="xs">{issue.description}</Text>
                    <Divider my="xs" />
                    <Text size="sm" weight={500}>Recommendation:</Text>
                    <Text size="sm">{issue.recommendation}</Text>
                  </Card>
                ))}
              </Stack>
            ) : (
              <Group position="center" my="lg">
                <IconDeviceLaptop size={40} stroke={1.5} color={theme.colors.green[6]} />
                <Text>Your system is running smoothly. No hardware issues detected.</Text>
              </Group>
            )}
          </Card>
        </Grid.Col>
        <Grid.Col span={12} lg={4}>
          <FanMonitor />
        </Grid.Col>
      </Grid>
    </Container>
  );
};

export default Dashboard;