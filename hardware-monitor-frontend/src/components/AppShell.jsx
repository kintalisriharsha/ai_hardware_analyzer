/* eslint-disable no-unused-vars */
// File: src/components/AppShell.jsx
import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  AppShell as MantineAppShell, 
  Title, 
  UnstyledButton,
  Group, 
  Text,
  ThemeIcon,
  useMantineColorScheme,
  ActionIcon
} from '@mantine/core';
import { 
  IconDashboard, 
  IconDeviceDesktop, 
  IconChartBar, 
  IconSettings,
  IconSun,
  IconMoon
} from '@tabler/icons-react';

const MainLinks = ({ active, setActive }) => {
  const navigate = useNavigate();
  const data = [
    { icon: IconDashboard, label: 'Dashboard', route: '/' },
    { icon: IconChartBar, label: 'Metrics', route: '/metrics' },
    { icon: IconDeviceDesktop, label: 'System Analysis', route: '/analysis' },
    { icon: IconSettings, label: 'Settings', route: '/settings' },
  ];

  const links = data.map((item) => (
    <UnstyledButton
      key={item.label}
      onClick={() => {
        setActive(item.label);
        navigate(item.route);
      }}
      style={(theme) => ({
        display: 'block',
        width: '100%',
        padding: '8px', // Use fixed values instead of theme.spacing
        borderRadius: '4px',
        color: 'inherit',
        backgroundColor: active === item.label ? 'rgba(0, 0, 0, 0.05)' : 'transparent',
        '&:hover': {
          backgroundColor: 'rgba(0, 0, 0, 0.05)',
        },
      })}
    >
      <Group>
        <ThemeIcon variant={active === item.label ? "filled" : "light"} size={30}>
          <item.icon size={20} />
        </ThemeIcon>
        <Text size="sm">{item.label}</Text>
      </Group>
    </UnstyledButton>
  ));

  return <>{links}</>;
};

function AppShell({ children, toggleColorScheme }) {
  const location = useLocation();
  const initialActive = () => {
    if (location.pathname === '/') return 'Dashboard';
    if (location.pathname === '/metrics') return 'Metrics';
    if (location.pathname === '/analysis') return 'System Analysis';
    if (location.pathname === '/settings') return 'Settings';
    return 'Dashboard';
  };

  const [active, setActive] = useState(initialActive);
  const { colorScheme } = useMantineColorScheme();

  return (
    <MantineAppShell
      padding="md"
      navbar={{
        width: 250,
        breakpoint: 'sm',
        collapsed: { mobile: false },
      }}
      header={{ height: 60 }}
    >
      <MantineAppShell.Header p="xs">
        <Group justify="space-between" style={{ height: '100%' }}>
          <Title order={3}>Hardware Health Monitor</Title>
          <ActionIcon 
            variant="default" 
            onClick={toggleColorScheme} 
            size={30}
          >
            {colorScheme === 'dark' ? <IconSun size={16} /> : <IconMoon size={16} />}
          </ActionIcon>
        </Group>
      </MantineAppShell.Header>

      <MantineAppShell.Navbar p="xs">
        <MantineAppShell.Section grow mt="xs">
          <MainLinks active={active} setActive={setActive} />
        </MantineAppShell.Section>
      </MantineAppShell.Navbar>

      <MantineAppShell.Main>
        {children}
      </MantineAppShell.Main>
    </MantineAppShell>
  );
}

export default AppShell;