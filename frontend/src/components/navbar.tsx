import {
  Navbar as NextUINavbar,
  NavbarBrand,
  NavbarContent,
  NavbarItem,
  NavbarMenu,
  NavbarMenuItem,
  NavbarMenuToggle,
} from "@nextui-org/navbar";
import { Spinner } from "@nextui-org/react";
import { AgentIcon } from "@/components/icons";
import { Logo } from "@/components/icons";
import { useEffect, useState } from "react";
import { getEnv } from "@/utils/getEnv";

export const Navbar = () => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);

  // Get the status of the agents
  useEffect(() => {
    fetch(`${getEnv()["backend_url"]}/api/agents`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((response) => response.json())
      .then((result) => {
        console.log(result);
        setAgents(result);
        setLoading(false);
      })
      .catch((error) => {
        setLoading(false);
        console.error(error);
      });
  }, []);

  return (
    <NextUINavbar maxWidth="xl" position="sticky">
      <NavbarContent className="basis-1/5 sm:basis-full" justify="start">
        <NavbarBrand className="gap-3 max-w-fit">
          <Logo />
        </NavbarBrand>
      </NavbarContent>

      <NavbarContent
        className="hidden sm:flex basis-1/5 sm:basis-full"
        justify="end"
      >
        <NavbarItem className="hidden sm:flex gap-2">
          {loading && <Spinner size="sm" color="primary" />}
          {agents.map((agent) => (
            <AgentIcon
              key={agent["agent"]}
              name={agent["agent"]}
              status={agent["healthy"]}
              tooltip={true}
            />
          ))}
        </NavbarItem>
      </NavbarContent>

      <NavbarContent className="sm:hidden basis-1 pl-4" justify="end">
        <NavbarMenuToggle />
      </NavbarContent>

      <NavbarMenu className="bg-gray-50">
        <div className="mx-4 mt-2 flex flex-col gap-2">
          {agents.map((item) => (
            <NavbarMenuItem
              key={item["agent"]}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "20px",
              }}
            >
              <AgentIcon name={item["agent"]} status={item["healthy"]} />
              <span>{item["agent"]}</span>
            </NavbarMenuItem>
          ))}
        </div>
      </NavbarMenu>
    </NextUINavbar>
  );
};
