import { render, screen } from "@testing-library/react";
import { ChatHistory } from "./ChatHistory";
import { ChatMessageProps } from "./ChatMessage";

// Mocking the ScrollShadow component
jest.mock("@nextui-org/react", () => ({
  ScrollShadow: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div> // Simplified mock, you can make it more sophisticated if needed
  ),
}));

// Mocking the ChatMessage component
jest.mock("./ChatMessage", () => ({
  ChatMessage: ({ text, sender }: { text: string; sender: string }) => (
    <div data-testid={`chat-message-${sender}`}>{text}</div>
  ),
}));

describe("ChatHistory", () => {
  it("renders messages correctly", () => {
    const messages: ChatMessageProps[] = [
      { text: "Hello, how are you?", sender: "human" },
      { text: "I'm doing well, thank you!", sender: "bot" },
    ];

    render(<ChatHistory messages={messages} />);

    // Ensure that the messages are rendered correctly
    expect(screen.getByText("Hello, how are you?")).toBeInTheDocument();
    expect(screen.getByText("I'm doing well, thank you!")).toBeInTheDocument();
  });
});
