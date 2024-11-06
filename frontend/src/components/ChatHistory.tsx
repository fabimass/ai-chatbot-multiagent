import { MessageBox } from "react-chat-elements";
import "react-chat-elements/dist/main.css";

interface ChatHistoryProps {
  messages: {
    text: string;
    sender: string;
  }[];
}

export const ChatHistory = ({ messages }: ChatHistoryProps) => {
  return (
    <>
      <div className="flex-grow">
        {messages.map((msg, index) => (
          // @ts-ignore
          <MessageBox
            position={"left"}
            type={"text"}
            title={"Message Box Title"}
            text="Here is a text type message box"
          />
        ))}
      </div>
    </>
  );
};
