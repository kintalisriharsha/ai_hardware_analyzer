/** @format */

import React from "react";
import { Card, Group, Title, Text, List, ThemeIcon } from "@mantine/core";
import { IconWind, IconCircleCheck } from "@tabler/icons-react";

const FanRecommendations = ({ fans }) => {
  // Generate recommendations based on fan data
  const getRecommendations = () => {
    const recommendations = [];

    // Check for inactive fans
    const inactiveFans = fans.filter((fan) => fan.status === "Inactive");
    if (inactiveFans.length > 0) {
      recommendations.push(
        "Check the connection of inactive fans. Ensure they're properly connected to the motherboard."
      );
      recommendations.push(
        "Clean fans of dust and debris which can prevent proper operation."
      );
      recommendations.push(
        "If fans still don't work after cleaning and checking connections, they may need to be replaced."
      );
    }

    // Check for low speed fans
    const lowSpeedFans = fans.filter(
      (fan) => fan.status === "Active" && fan.value && fan.value < 800
    );

    if (lowSpeedFans.length > 0) {
      recommendations.push(
        "Fans running at low speeds may indicate obstructions or aging bearings."
      );
      recommendations.push(
        "Check BIOS settings for fan speed control and consider adjusting the fan curve."
      );
    }

    // General maintenance recommendations
    if (fans.length > 0) {
      recommendations.push(
        "Clean all fans and heat sinks every 3-6 months to maintain optimal cooling performance."
      );
      recommendations.push(
        "Ensure proper airflow inside the case by managing cable routing and keeping vents clear."
      );
    }

    return recommendations;
  };

  const recommendations = getRecommendations();

  return (
    <Card shadow="sm" withBorder>
      <Group position="apart" mb="md">
        <Title order={4}>Cooling System Recommendations</Title>
        <IconWind size={24} />
      </Group>

      {recommendations.length > 0 ? (
        <List spacing="sm">
          {recommendations.map((rec, index) => (
            <List.Item
              key={index}
              icon={
                <ThemeIcon color="blue" size={22} radius="xl">
                  <IconCircleCheck size={16} />
                </ThemeIcon>
              }
            >
              <Text size="sm">{rec}</Text>
            </List.Item>
          ))}
        </List>
      ) : (
        <Text color="dimmed" align="center">
          No specific recommendations needed for your cooling system at this
          time.
        </Text>
      )}
    </Card>
  );
};

export default FanRecommendations;
