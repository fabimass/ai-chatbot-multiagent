import { render, screen } from "@testing-library/react";
import IndexPage from "@/pages/index";

global.fetch = jest.fn();

jest.mock("@/utils/getEnv", () => ({
  getEnv: () => ({
    backend_url: "localhost",
  }),
}));

jest.mock("@/components/ChatHistory", () => ({
  ChatHistory: () => <div>ChatHistory</div>,
}));

jest.mock("@/components/navbar", () => ({
  Navbar: () => <div>Navbar</div>,
}));

jest.mock("@/components/ChatInput", () => ({
  ChatInput: ({ onSend, loading }: { onSend: any; loading: any }) => (
    <button onClick={() => onSend("Test message")} disabled={loading}>
      Send
    </button>
  ),
}));

describe("Index page", () => {
  beforeEach(() => {
    // Reset localStorage and mock the fetch function before each test
    localStorage.clear();
    jest.clearAllMocks();
    localStorage.setItem("chatbot_session_id", "test-session-id");
    (global.fetch as jest.Mock).mockResolvedValue({
      json: () => ({ answer: "Mocked bot response" }),
    });
  });

  it("renders the layout and child components", () => {
    render(<IndexPage />);

    // Check if DefaultLayout, ChatHistory, and ChatInput are rendered
    expect(screen.getByText("Send")).toBeInTheDocument(); // Send button in ChatInput
    expect(screen.getByText("human: Test message")).toBeInTheDocument(); // Mock message
  });

  /*it("sets and uses a sessionId in localStorage", () => {
    render(<IndexPage />);

    const sessionId = localStorage.getItem("chatbot_session_id");
    expect(sessionId).toBeTruthy();
  });

  it("calls handleSendMessage and fetches a response", async () => {
    render(<IndexPage />);

    // Mock the message
    fireEvent.click(screen.getByText("Send"));

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
      expect(screen.getByText("bot: Mocked bot response")).toBeInTheDocument()
    );
  });

  it("handles the loading state", async () => {
    render(<IndexPage />);

    // Send the message
    fireEvent.click(screen.getByText("Send"));

    // Check that the button is disabled while loading
    expect(screen.getByText("Send")).toBeDisabled();

    // Wait for the fetch call to complete and enable the button again
    await waitFor(() => expect(screen.getByText("Send")).toBeEnabled());
  });

  it("handles errors gracefully", async () => {
    global.fetch.mockRejectedValueOnce(new Error("API Error"));

    render(<IndexPage />);

    fireEvent.click(screen.getByText("Send"));

    await waitFor(() => {
      // Ensure loading state is handled
      expect(screen.getByText("Send")).toBeEnabled();
    });
  });*/
});
