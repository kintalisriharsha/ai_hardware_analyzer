import { useState, useEffect } from 'react';
import { 
  Container, 
  Grid, 
  Card, 
  Title, 
  Text, 
  Group, 
  Select,
  Stack,
  Table,
  ScrollArea,
  Badge,
  Pagination
} from '@mantine/core';
import { AreaChart, BarChart } from '@mantine/charts';
import { getMetricsStatistics, getMetricsHistory } from '../api';

const Metrics = () => {
  const [statistics, setStatistics] = useState(null);
  const [metricsHistory, setMetricsHistory] = useState([]);
  const [timeRange, setTimeRange] = useState('7');
  // eslint-disable-next-line no-unused-vars
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const fetchStatistics = async () => {
    try {
      const response = await getMetricsStatistics(timeRange);
      setStatistics(response.data);
    } catch (error) {
      console.error('Error fetching metrics statistics:', error);
    }
  };

  const fetchHistory = async () => {
    try {
      const days = parseInt(timeRange);
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - days);
      
      const response = await getMetricsHistory({
        page,
        start_date: startDate.toISOString(),
      });
      
      setMetricsHistory(response.data.results || response.data);
      
      if (response.data.count) {
        setTotalPages(Math.ceil(response.data.count / 10));
      }
    } catch (error) {
      console.error('Error fetching metrics history:', error);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    await Promise.all([fetchStatistics(), fetchHistory()]);
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, [timeRange, page]);

  // Prepare chart data
  const hourlyData = statistics?.hourly_data || [];
  const cpuData = hourlyData.map(data => ({
    date: new Date(data.hour).toLocaleString(),
    value: data.avg_cpu,
  }));
  
  const memoryData = hourlyData.map(data => ({
    date: new Date(data.hour).toLocaleString(),
    value: data.avg_memory,
  }));
  
  const diskData = hourlyData.map(data => ({
    date: new Date(data.hour).toLocaleString(),
    value: data.avg_disk,
  }));

  const anomalyData = hourlyData.map(data => ({
    date: new Date(data.hour).toLocaleString(),
    'Anomalies': data.anomaly_count,
  }));

  return (
    <Container fluid>
      <Group position="apart" mb="md">
        <Title order={2}>System Metrics</Title>
        <Select
          value={timeRange}
          onChange={setTimeRange}
          data={[
            { value: '1', label: 'Last 24 Hours' },
            { value: '7', label: 'Last 7 Days' },
            { value: '30', label: 'Last 30 Days' },
            { value: '90', label: 'Last 90 Days' },
          ]}
          width={200}
        />
      </Group>

      <Grid>
        {/* Statistics Summary */}
        <Grid.Col span={12}>
          <Card shadow="sm" withBorder mb="md">
            <Title order={4} mb="md">Metrics Summary</Title>
            <Grid>
              <Grid.Col span={6} md={3}>
                <Stack spacing={0} align="center" mb="md">
                  <Text size="xl" weight={700} color="blue">
                    {statistics?.total_metrics || 0}
                  </Text>
                  <Text size="sm" color="dimmed">Total Measurements</Text>
                </Stack>
              </Grid.Col>
              
              <Grid.Col span={6} md={3}>
                <Stack spacing={0} align="center" mb="md">
                  <Text size="xl" weight={700} color="red">
                    {statistics?.anomalies || 0}
                  </Text>
                  <Text size="sm" color="dimmed">Anomalies Detected</Text>
                </Stack>
              </Grid.Col>
              
              <Grid.Col span={6} md={3}>
                <Stack spacing={0} align="center" mb="md">
                  <Text size="xl" weight={700} color="green">
                    {statistics?.cpu?.avg?.toFixed(1) || 0}%
                  </Text>
                  <Text size="sm" color="dimmed">Avg CPU Usage</Text>
                </Stack>
              </Grid.Col>
              
              <Grid.Col span={6} md={3}>
                <Stack spacing={0} align="center" mb="md">
                  <Text size="xl" weight={700} color="orange">
                    {statistics?.memory?.avg?.toFixed(1) || 0}%
                  </Text>
                  <Text size="sm" color="dimmed">Avg Memory Usage</Text>
                </Stack>
              </Grid.Col>
            </Grid>
          </Card>
        </Grid.Col>

        {/* CPU Chart */}
        <Grid.Col span={12} md={6}>
          <Card shadow="sm" withBorder>
            <Title order={4} mb="md">CPU Usage (%)</Title>
            <AreaChart
              h={250}
              data={cpuData}
              dataKey="date"
              series={[
                { name: 'value', color: 'blue' }
              ]}
              yAxisProps={{ domain: [0, 100] }}
              withLegend={false}
              withTooltip
              tooltipProps={{ trigger: 'hover' }}
            />
          </Card>
        </Grid.Col>

        {/* Memory Chart */}
        <Grid.Col span={12} md={6}>
          <Card shadow="sm" withBorder>
            <Title order={4} mb="md">Memory Usage (%)</Title>
            <AreaChart
              h={250}
              data={memoryData}
              dataKey="date"
              series={[
                { name: 'value', color: 'green' }
              ]}
              yAxisProps={{ domain: [0, 100] }}
              withLegend={false}
              withTooltip
              tooltipProps={{ trigger: 'hover' }}
            />
          </Card>
        </Grid.Col>

        {/* Disk Chart */}
        <Grid.Col span={12} md={6}>
          <Card shadow="sm" withBorder>
            <Title order={4} mb="md">Disk Usage (%)</Title>
            <AreaChart
              h={250}
              data={diskData}
              dataKey="date"
              series={[
                { name: 'value', color: 'orange' }
              ]}
              yAxisProps={{ domain: [0, 100] }}
              withLegend={false}
              withTooltip
              tooltipProps={{ trigger: 'hover' }}
            />
          </Card>
        </Grid.Col>

        {/* Anomalies Chart */}
        <Grid.Col span={12} md={6}>
          <Card shadow="sm" withBorder>
            <Title order={4} mb="md">Anomalies Detected</Title>
            <BarChart
              h={250}
              data={anomalyData}
              dataKey="date"
              series={[
                { name: 'Anomalies', color: 'red' }
              ]}
              withLegend={false}
              withTooltip
              tooltipProps={{ trigger: 'hover' }}
            />
          </Card>
        </Grid.Col>

        {/* Metrics History Table */}
        <Grid.Col span={12}>
          <Card shadow="sm" withBorder>
            <Group position="apart" mb="md">
              <Title order={4}>Metrics History</Title>
            </Group>
            
            <ScrollArea>
              <Table striped highlightOnHover>
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>CPU</th>
                    <th>Memory</th>
                    <th>Disk</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {metricsHistory.map((metric) => (
                    <tr key={metric.id}>
                      <td>{new Date(metric.timestamp).toLocaleString()}</td>
                      <td>{metric.cpu_percent.toFixed(1)}%</td>
                      <td>{metric.memory_percent.toFixed(1)}%</td>
                      <td>{metric.disk_usage_percent.toFixed(1)}%</td>
                      <td>
                        <Badge 
                          color={metric.is_anomaly ? 'red' : 'green'}
                        >
                          {metric.is_anomaly ? 'Anomaly' : 'Normal'}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </ScrollArea>
            
            {totalPages > 1 && (
              <Group position="center" mt="md">
                <Pagination 
                  total={totalPages} 
                  page={page} 
                  onChange={setPage} 
                />
              </Group>
            )}
          </Card>
        </Grid.Col>
      </Grid>
    </Container>
  );
};

export default Metrics;