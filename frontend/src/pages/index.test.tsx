import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import IndexPage from "@/pages/index";

global.fetch = jest.fn();
global.crypto.randomUUID = jest.fn();

jest.mock("@/utils/getEnv", () => ({
  getEnv: () => ({
    backend_url: "http://mocked-backend",
  }),
}));

jest.mock("@/components/ChatHistory", () => ({
  ChatHistory: ({ messages }: { messages: any[] }) => (
    <div data-testid="chat-history">
      {messages.map((msg: any, index: any) => (
        <div key={index}>
          <span>
            {msg.sender}: {msg.text}
          </span>
        </div>
      ))}
    </div>
  ),
}));

jest.mock("@/components/navbar", () => ({
  Navbar: () => <div data-testid="navbar">Navbar</div>,
}));

jest.mock("@/components/ChatInput", () => ({
  ChatInput: ({ onSend, loading }: { onSend: any; loading: boolean }) => (
    <button
      onClick={() => onSend("Test message")}
      disabled={loading}
      data-testid="send-button"
    >
      Send
    </button>
  ),
}));

describe("Index page", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      json: () => ({ answer: "Mocked bot response" }),
    });
    (global.crypto.randomUUID as jest.Mock).mockReturnValue("random-id");
  });

  it("renders correctly", async () => {
    render(<IndexPage />);

    expect(screen.getByTestId("navbar")).toBeInTheDocument();
    expect(screen.getByTestId("send-button")).toBeInTheDocument();
    expect(screen.getByTestId("chat-history")).toBeInTheDocument();

    // Expect initial message from the bot
    await waitFor(() =>
      expect(screen.getByText("bot: Mocked bot response")).toBeInTheDocument()
    );
  });

  it("sets and uses a sessionId in localStorage", () => {
    render(<IndexPage />);

    const sessionId = localStorage.getItem("chatbot_session_id");
    expect(sessionId).toBe("random-id");
  });

  it("calls handleSendMessage and fetches a response", async () => {
    render(<IndexPage />);

    // Mock the message
    fireEvent.click(screen.getByTestId("send-button"));

    // Expect the message to appear
    expect(screen.getByText("human: Test message")).toBeInTheDocument();

    // Wait for the API call to complete and check the response
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        "http://mocked-backend/api/ask",
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining("Test message"),
        })
      )
    );

    // Verify that the message has been added to the chat history
    await waitFor(() =>
      expect(screen.getAllByText("bot: Mocked bot response").length).toBe(2)
    );
  });

  it("handles the loading state", async () => {
    render(<IndexPage />);

    // Send the message
    fireEvent.click(screen.getByTestId("send-button"));

    // Check that the button is disabled while loading
    expect(screen.getByTestId("send-button")).toBeDisabled();

    // Wait for the fetch call to complete and enable the button again
    await waitFor(() =>
      expect(screen.getByTestId("send-button")).toBeEnabled()
    );
  });

  it("handles errors gracefully", async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error("API Error"));

    render(<IndexPage />);

    fireEvent.click(screen.getByTestId("send-button"));

    await waitFor(() => {
      // Ensure loading state is handled
      expect(screen.getByTestId("send-button")).toBeEnabled();
    });
  });
});
