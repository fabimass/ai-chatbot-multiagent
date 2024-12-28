import * as React from "react";
import CustomLogo from "@/assets/logo-fiuba.png";
import { IconSvgProps } from "@/types";
import { RiRobot3Fill } from "react-icons/ri";
import { Badge, Tooltip, Button } from "@nextui-org/react";

export const Logo: React.FC<IconSvgProps> = () => (
  <img src={CustomLogo} style={{ width: "auto", height: 50 }} />
);

interface AgentIconProps {
  status: boolean;
  name: string;
  tooltip?: boolean;
}

export const AgentIcon = ({
  status,
  name,
  tooltip = false,
}: AgentIconProps) => {
  return (
    <Badge
      color={status ? "success" : "danger"}
      content={status ? "✓" : "!"}
      shape="circle"
      placement="top-right"
    >
      {tooltip ? (
        <Tooltip content={name}>
          <Button
            isIconOnly
            aria-label="agent status"
            radius="full"
            variant="light"
            className="text-3xl"
          >
            <RiRobot3Fill />
          </Button>
        </Tooltip>
      ) : (
        <Button
          isIconOnly
          aria-label="agent status"
          radius="full"
          variant="light"
          className="text-3xl"
        >
          <RiRobot3Fill />
        </Button>
      )}
    </Badge>
  );
};
