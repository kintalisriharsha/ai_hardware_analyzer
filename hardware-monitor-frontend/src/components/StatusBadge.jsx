// File: src/components/StatusBadge.jsx
import { Badge, Group, Tooltip } from '@mantine/core';

/**
 * A reusable badge component for displaying status information
 * 
 * @param {Object} props
 * @param {boolean} props.status - The status (true for OK/good, false for warning/error)
 * @param {string} props.label - The badge label text
 * @param {string} props.okColor - The color to use for "OK" status (default: green)
 * @param {string} props.warningColor - The color to use for "warning" status (default: red)
 * @param {string} props.tooltip - Optional tooltip text
 * @param {string} props.size - Badge size (xs, sm, md, lg, xl)
 */
const StatusBadge = ({ 
  status, 
  label, 
  okColor = 'green', 
  warningColor = 'red',
  tooltip,
  size = 'md'
}) => {
  const badge = (
    <Badge 
      color={status ? okColor : warningColor}
      size={size}
    >
      {label}
    </Badge>
  );

  if (tooltip) {
    return (
      <Tooltip label={tooltip}>
        <Group spacing={0}>{badge}</Group>
      </Tooltip>
    );
  }

  return badge;
};

export default StatusBadge;