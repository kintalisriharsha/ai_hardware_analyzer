// File: src/components/MetricCard.jsx
import { Card, Text, Group, RingProgress } from '@mantine/core';

/**
 * A reusable card component for displaying system metrics with a ring progress indicator
 * 
 * @param {Object} props
 * @param {string} props.title - The metric title
 * @param {number} props.value - The metric value (0-100)
 * @param {string} props.unit - The unit of measurement (%, GB, etc.)
 * @param {React.ReactNode} props.icon - The icon to display
 * @param {string} props.color - The color for the progress ring (green, orange, red, etc.)
 * @param {string} props.subtitle - Optional subtitle text
 */
const MetricCard = ({ title, value, unit = '%', icon, color = 'blue', subtitle }) => {
  return (
    <Card shadow="sm" withBorder>
      <Group position="apart">
        <Text weight={500}>{title}</Text>
        {icon}
      </Group>
      
      <RingProgress
        sections={[{ value, color }]}
        label={
          <Text size="xl" align="center" weight={700}>
            {value?.toFixed(1) || 0}{unit}
          </Text>
        }
        size={140}
        thickness={14}
        roundCaps
        my="md"
        mx="auto"
      />
      
      {subtitle && (
        <Text size="sm" color="dimmed" align="center">
          {subtitle}
        </Text>
      )}
    </Card>
  );
};

export default MetricCard;