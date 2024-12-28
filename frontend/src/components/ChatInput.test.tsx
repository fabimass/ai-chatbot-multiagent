import { render, screen, fireEvent } from "@testing-library/react";
import { ChatInput } from "./ChatInput";

jest.mock("@nextui-org/react", () => ({
  ...jest.requireActual("@nextui-org/react"),
  Spinner: jest.fn(() => <div data-testid="spinner" />),
}));

jest.mock("@fluentui/react-icons", () => ({
  ...jest.requireActual("@fluentui/react-icons"),
  Send28Filled: jest.fn(() => <div data-testid="send" />),
}));

describe("ChatInput component", () => {
  it("renders Textarea and send button", () => {
    render(<ChatInput onSend={jest.fn()} loading={false} />);

    // Check if Textarea is rendered
    expect(
      screen.getByPlaceholderText("Ask me something...")
    ).toBeInTheDocument();

    // Check if send button is rendered
    expect(screen.getByTestId("send")).toBeInTheDocument();
  });

  it("renders Spinner when loading is true", () => {
    render(<ChatInput onSend={jest.fn()} loading={true} />);

    // Check if Spinner is rendered
    expect(screen.getByTestId("spinner")).toBeInTheDocument();
  });

  it("calls onSend with the correct value when send button is clicked", () => {
    const onSendMock = jest.fn();
    render(<ChatInput onSend={onSendMock} loading={false} />);

    const textarea = screen.getByPlaceholderText("Ask me something...");
    const sendButton = screen.getByTestId("send");

    // Type a question
    fireEvent.change(textarea, { target: { value: "What is AI?" } });
    expect(textarea).toHaveValue("What is AI?");

    // Click send button
    fireEvent.click(sendButton);

    // Check if onSend was called
    expect(onSendMock).toHaveBeenCalledWith("What is AI?");

    // Check if input is cleared
    expect(textarea).toHaveValue("");
  });

  it("calls onSend with the correct value when Enter key is pressed", () => {
    const onSendMock = jest.fn();
    render(<ChatInput onSend={onSendMock} loading={false} />);

    const textarea = screen.getByPlaceholderText("Ask me something...");

    // Type a question
    fireEvent.change(textarea, { target: { value: "What is AI?" } });
    expect(textarea).toHaveValue("What is AI?");

    // Press Enter key
    fireEvent.keyUp(textarea, { key: "Enter", code: "Enter", charCode: 13 });

    // Check if onSend was called
    expect(onSendMock).toHaveBeenCalledWith("What is AI?");

    // Check if input is cleared
    expect(textarea).toHaveValue("");
  });

  it("does not call onSend when input is empty", () => {
    const onSendMock = jest.fn();
    render(<ChatInput onSend={onSendMock} loading={false} />);

    const sendButton = screen.getByTestId("send");

    // Click send button without typing
    fireEvent.click(sendButton);

    // Press Enter key
    fireEvent.keyUp(screen.getByPlaceholderText("Ask me something..."), {
      key: "Enter",
      code: "Enter",
      charCode: 13,
    });

    // Check if onSend was not called
    expect(onSendMock).not.toHaveBeenCalled();
  });
});
