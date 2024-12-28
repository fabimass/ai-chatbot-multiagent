import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ChatMessage } from "./ChatMessage";

global.fetch = jest.fn();

jest.mock("@/utils/getEnv", () => ({
  getEnv: () => ({
    backend_url: "http://mocked-backend",
  }),
}));

jest.mock("react-chat-elements", () => ({
  MessageBox: ({ text, title }: { text: string; title: string }) => (
    <div data-testid="mock-messagebox">
      <p>{title}</p>
      <p>{text}</p>
    </div>
  ),
}));

jest.mock("react-icons/fa", () => ({
  FaThumbsUp: () => <div data-testid="thumbs-up">ThumbsUp</div>,
  FaThumbsDown: () => <div data-testid="thumbs-down">ThumbsDown</div>,
}));

describe("ChatMessage component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.setItem("chatbot_session_id", "test-session-id");
  });

  it("renders messages correctly", () => {
    render(<ChatMessage text="Hello, world!" sender="bot" />);
    expect(screen.getByText("Hello, world!")).toBeInTheDocument();
    expect(screen.getByText("bot")).toBeInTheDocument();
  });

  it("shows thumbs up and thumbs down buttons for bot messages", () => {
    render(<ChatMessage text="Hello, bot here!" sender="bot" />);
    expect(screen.getByTestId("thumbs-up")).toBeInTheDocument();
    expect(screen.getByTestId("thumbs-down")).toBeInTheDocument();
  });

  it("does not show thumbs up and thumbs down buttons for human messages", () => {
    render(<ChatMessage text="Hello, human here!" sender="human" />);
    expect(screen.queryByText("ThumbsUp")).not.toBeInTheDocument();
    expect(screen.queryByText("ThumbsDown")).not.toBeInTheDocument();
  });

  it("handles thumbs up click and sends feedback", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: jest.fn().mockResolvedValueOnce({ success: true }),
    });

    render(
      <ChatMessage
        text="Hello, bot here!"
        sender="bot"
        previous="What is your name?"
      />
    );

    const thumbsUpButton = screen.getByTestId("thumbs-up");
    fireEvent.click(thumbsUpButton);

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/feedback"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          question: "What is your name?",
          answer: "Hello, bot here!",
          like: true,
          session_id: "test-session-id",
        }),
      })
    );
  });

  it("handles thumbs down click and sends feedback", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: jest.fn().mockResolvedValueOnce({ success: true }),
    });

    render(
      <ChatMessage text="I am a bot." sender="bot" previous="Who are you?" />
    );

    const thumbsDownButton = screen.getByTestId("thumbs-down");
    fireEvent.click(thumbsDownButton);

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/feedback"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          question: "Who are you?",
          answer: "I am a bot.",
          like: false,
          session_id: "test-session-id",
        }),
      })
    );
  });

  it("hides icons after animation completes", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: jest.fn().mockResolvedValueOnce({ success: true }),
    });
    jest.useFakeTimers();
    render(<ChatMessage text="Goodbye!" sender="bot" />);

    const thumbsUpButton = screen.getByTestId("thumbs-up");
    fireEvent.click(thumbsUpButton);

    jest.advanceTimersByTime(900);

    await waitFor(() => {
      expect(screen.queryByText("ThumbsUp")).not.toBeInTheDocument();
      expect(screen.queryByText("ThumbsDown")).not.toBeInTheDocument();
    });

    jest.useRealTimers();
  });
});
