import { ChatMessage, ChatMessageProps } from "./ChatMessage";
import "react-chat-elements/dist/main.css";
import { ScrollShadow } from "@nextui-org/react";
import { useRef, useEffect } from "react";

export interface ChatHistoryProps {
  messages: ChatMessageProps[];
}

export const ChatHistory = ({ messages }: ChatHistoryProps) => {
  const scrollbarsRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (scrollbarsRef.current) {
      // Scroll to the bottom whenever the messages change
      scrollbarsRef.current.scrollTop = scrollbarsRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <>
      <ScrollShadow
        className="flex-grow px-[25%]"
        hideScrollBar
        ref={scrollbarsRef}
      >
        {messages.map((msg) => (
          <ChatMessage text={msg.text} sender={msg.sender} />
        ))}
      </ScrollShadow>
    </>
  );
};
