// File: src/pages/Settings.jsx
import { useState, useEffect } from 'react';
import { 
  Container, 
  Title, 
  Card, 
  Group, 
  Button, 
  Select, 
  Text,
  NumberInput,
  Switch,
  Stack,
  Divider,
  Alert,
  Progress,
  Badge,
} from '@mantine/core';
import { IconAlertCircle, IconBrandPython, IconDatabase } from '@tabler/icons-react';
import { trainModel, getMetricsStatistics } from '../api';

const Settings = () => {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);
  const [samples, setSamples] = useState(300);
  const [interval, setInterval] = useState('60');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [metricsCount, setMetricsCount] = useState(0);
  const [loadingMetrics, setLoadingMetrics] = useState(true);
  
  // Fetch the current number of metrics
  useEffect(() => {
    const fetchMetricsCount = async () => {
      setLoadingMetrics(true);
      try {
        // Get metrics from the last 90 days to count total measurements
        const response = await getMetricsStatistics(90);
        if (response.data && response.data.total_metrics !== undefined) {
          setMetricsCount(response.data.total_metrics);
        }
      } catch (error) {
        console.error('Error fetching metrics count:', error);
      } finally {
        setLoadingMetrics(false);
      }
    };
    
    fetchMetricsCount();
  }, []);
  
  const handleTrainModel = async () => {
    setLoading(true);
    setSuccess(false);
    setError(null);
    
    try {
      await trainModel(samples);
      setSuccess(true);
    } catch (error) {
      console.error('Error training model:', error);
      setError('Failed to train the model. Not enough data or server error. See console for details.');
    } finally {
      setLoading(false);
    }
  };
  
  // Calculate how many more samples are needed
  const minimumSamples = 50;
  const samplesNeeded = Math.max(0, minimumSamples - metricsCount);
  const hasEnoughData = metricsCount >= minimumSamples;
  
  // Calculate progress percentage
  const dataProgress = Math.min(100, (metricsCount / minimumSamples) * 100);
  
  return (
    <Container fluid>
      <Title order={2} mb="md">Settings</Title>
      
      <Stack spacing="md">
        {/* Model Training */}
        <Card shadow="sm" withBorder>
          <Title order={4} mb="md">ML Model Training</Title>
          
          {/* Data collection status */}
          <Card shadow="xs" withBorder mb="md">
            <Group justify="space-between" mb="xs">
              <Text weight={500}>
                <Group>
                  <IconDatabase size={18} />
                  Data Collection Status
                </Group>
              </Text>
              <Badge color={hasEnoughData ? 'green' : 'orange'}>
                {hasEnoughData ? 'Ready for Training' : 'Collecting Data'}
              </Badge>
            </Group>
            
            <Text size="sm" mb="xs">
              {loadingMetrics 
                ? 'Checking collected measurements...' 
                : `${metricsCount} measurements collected (minimum ${minimumSamples} needed)`
              }
            </Text>
            
            <Progress 
              value={dataProgress} 
              color={hasEnoughData ? 'green' : 'orange'} 
              size="md" 
              radius="xl"
              striped={!hasEnoughData}
              animate={!hasEnoughData}
              mb="xs"
            />
            
            {!hasEnoughData && (
              <Text size="sm" color="orange">
                Need {samplesNeeded} more measurements before training. Continue collecting data.
              </Text>
            )}
          </Card>
          
          {success && (
            <Alert 
              title="Success!" 
              color="green" 
              mb="md" 
              withCloseButton 
              onClose={() => setSuccess(false)}
            >
              Model trained successfully!
            </Alert>
          )}
          
          {error && (
            <Alert 
              title="Error" 
              color="red" 
              mb="md" 
              withCloseButton 
              onClose={() => setError(null)}
              icon={<IconAlertCircle size={16} />}
            >
              {error}
            </Alert>
          )}
          
          <Group align="end" mb="md">
            <NumberInput
              label="Number of samples for training"
              description="More samples provide better training but take longer"
              min={50}
              max={1000}
              value={samples}
              onChange={(val) => setSamples(val)}
              style={{ width: 250 }}
            />
            
            <Button 
              leftSection={<IconBrandPython size={18} />} 
              onClick={handleTrainModel} 
              loading={loading}
              disabled={!hasEnoughData}
            >
              Train Model
            </Button>
          </Group>
          
          <Text size="sm" color="dimmed">
            Training a new model will analyze your system's typical performance patterns to better detect anomalies.
            This process may take a few minutes depending on the number of samples.
          </Text>
        </Card>
        
        {/* Monitoring Settings */}
        <Card shadow="sm" withBorder>
          <Title order={4} mb="md">Monitoring Settings</Title>
          
          <Stack spacing="md">
            <Select
              label="Data collection interval"
              description="How often to collect system metrics"
              value={interval}
              onChange={setInterval}
              data={[
                { value: '30', label: 'Every 30 seconds' },
                { value: '60', label: 'Every minute' },
                { value: '300', label: 'Every 5 minutes' },
                { value: '600', label: 'Every 10 minutes' },
              ]}
              style={{ maxWidth: 300 }}
            />
            
            <Switch
              label="Auto-refresh dashboard"
              description="Automatically update the dashboard with the latest data"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.currentTarget.checked)}
            />
          </Stack>
        </Card>
        
        {/* User Preferences */}
        <Card shadow="sm" withBorder>
          <Title order={4} mb="md">User Preferences</Title>
          
          <Stack spacing="md">
            <Select
              label="Temperature unit"
              defaultValue="celsius"
              data={[
                { value: 'celsius', label: 'Celsius (°C)' },
                { value: 'fahrenheit', label: 'Fahrenheit (°F)' },
              ]}
              style={{ maxWidth: 300 }}
            />
            
            <Select
              label="Default time range"
              defaultValue="7"
              data={[
                { value: '1', label: 'Last 24 Hours' },
                { value: '7', label: 'Last 7 Days' },
                { value: '30', label: 'Last 30 Days' },
              ]}
              style={{ maxWidth: 300 }}
            />
          </Stack>
        </Card>
      </Stack>
    </Container>
  );
};

export default Settings;