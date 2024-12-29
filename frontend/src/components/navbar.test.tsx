import { render, screen, waitFor } from "@testing-library/react";
import { Navbar } from "./navbar";
import { NavbarMenuItem, NavbarItem } from "@nextui-org/navbar";

global.fetch = jest.fn();

jest.mock("@/utils/getEnv", () => ({
  getEnv: () => ({
    backend_url: "http://mocked-backend",
  }),
}));

jest.mock("@nextui-org/react", () => ({
  ...jest.requireActual("@nextui-org/react"),
  Spinner: jest.fn(() => <div data-testid="spinner" />),
}));

jest.mock("@nextui-org/navbar", () => ({
  Navbar: jest.fn(({ children }) => <div>{children}</div>),
  NavbarContent: jest.fn(({ children }) => <div>{children}</div>),
  NavbarBrand: jest.fn(({ children }) => <div>{children}</div>),
  NavbarItem: jest.fn(({ children }) => <div>{children}</div>),
  NavbarMenu: jest.fn(({ children }) => <div>{children}</div>),
  NavbarMenuItem: jest.fn(({ children }) => <div>{children}</div>),
  NavbarMenuToggle: jest.fn(() => <div data-testid="menu-toggle" />),
}));

jest.mock("@/components/icons", () => ({
  AgentIcon: jest.fn(({ name, status }) => (
    <div data-testid="agent-icon">
      {name} - {status ? "Healthy" : "Unhealthy"}
    </div>
  )),
  Logo: jest.fn(() => <div data-testid="logo" />),
}));

describe("Navbar component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      json: () => [
        { agent: "Agent1", healthy: true },
        { agent: "Agent2", healthy: false },
      ],
    });
  });

  it("renders the logo", () => {
    render(<Navbar />);
    expect(screen.getByTestId("logo")).toBeInTheDocument();
  });

  it("shows the loading spinner initially", () => {
    render(<Navbar />);
    expect(screen.getAllByTestId("spinner").length).toBe(2);
  });

  it("displays agent icons after fetching data", async () => {
    (NavbarMenuItem as unknown as jest.Mock)
      .mockReturnValueOnce(<div>MenuItem</div>)
      .mockReturnValueOnce(<div>MenuItem</div>);

    render(<Navbar />);

    await waitFor(() => {
      expect(screen.getAllByTestId("agent-icon").length).toBe(2);
    });

    expect(screen.getByText("Agent1 - Healthy")).toBeInTheDocument();
    expect(screen.getByText("Agent2 - Unhealthy")).toBeInTheDocument();
  });

  it("displays agent icons in the menu (for smaller screens)", async () => {
    (NavbarItem as unknown as jest.Mock)
      .mockReturnValueOnce(<div>NavbarItem</div>)
      .mockReturnValueOnce(<div>NavbarItem</div>);

    render(<Navbar />);

    await waitFor(() => {
      expect(screen.getAllByTestId("agent-icon").length).toBe(2);
    });

    expect(screen.getByText("Agent1 - Healthy")).toBeInTheDocument();
    expect(screen.getByText("Agent2 - Unhealthy")).toBeInTheDocument();
  });

  it("renders the menu toggle for small screens", async () => {
    render(<Navbar />);

    await waitFor(() => {
      expect(screen.getByTestId("menu-toggle")).toBeInTheDocument();
    });
  });

  it("handles API errors gracefully", async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error("API Error"));

    render(<Navbar />);

    await waitFor(() => {
      expect(screen.queryByTestId("spinner")).not.toBeInTheDocument();
    });
  });
});
