import { render, screen } from "@testing-library/react";
import { AgentIcon } from "./icons";

jest.mock("@nextui-org/react", () => ({
  ...jest.requireActual("@nextui-org/react"),
  Tooltip: jest.fn(({ children }) => (
    <div data-testid="tooltip">{children}</div>
  )),
}));

describe("AgentIcon component", () => {
  it("renders with a success status", () => {
    render(<AgentIcon status={true} name="Agent1" tooltip={false} />);
    const badge = screen.getByText("✓");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("bg-success");
  });

  it("renders with a danger status", () => {
    render(<AgentIcon status={false} name="Agent1" tooltip={false} />);
    const badge = screen.getByText("!");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("bg-danger");
  });

  it("renders with a tooltip when tooltip is true", () => {
    render(<AgentIcon status={true} name="Agent1" tooltip={true} />);
    const tooltip = screen.getByTestId("tooltip");
    expect(tooltip).toBeInTheDocument();
  });

  it("does not render a tooltip when tooltip is false", () => {
    render(<AgentIcon status={true} name="Agent1" tooltip={false} />);
    const tooltip = screen.queryByTestId("tooltip");
    expect(tooltip).not.toBeInTheDocument();
  });
});
