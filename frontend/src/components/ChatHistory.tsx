import { MessageBox } from "react-chat-elements";
import "react-chat-elements/dist/main.css";

export interface ChatHistoryProps {
  messages: {
    text: string;
    sender: string;
  }[];
}

export const ChatHistory = ({ messages }: ChatHistoryProps) => {
  return (
    <>
      <div className="flex-grow">
        {messages.map((msg) => (
          // @ts-ignore
          <MessageBox
            position={msg.sender === "human" ? "right" : "left"}
            type="text"
            title={msg.sender}
            text={msg.text}
          />
        ))}
      </div>
    </>
  );
};
