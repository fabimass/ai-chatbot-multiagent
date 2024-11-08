import { MessageBox } from "react-chat-elements";
import "react-chat-elements/dist/main.css";
import { ScrollShadow } from "@nextui-org/react";
import { useRef, useEffect } from "react";

export interface ChatHistoryProps {
  messages: {
    text: string;
    sender: string;
  }[];
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
      <ScrollShadow className="flex-grow" hideScrollBar ref={scrollbarsRef}>
        {messages.map((msg) => (
          // @ts-ignore
          <MessageBox
            position={msg.sender === "human" ? "right" : "left"}
            type="text"
            title={msg.sender}
            text={msg.text}
          />
        ))}
      </ScrollShadow>
    </>
  );
};
