import DefaultLayout from "@/layouts/default";
import { ChatInput } from "@/components/ChatInput";
import { ChatHistory, ChatHistoryProps } from "@/components/ChatHistory";
import { useState } from "react";

export default function IndexPage() {
  const [messages, setMessages] = useState<ChatHistoryProps["messages"]>([]);

  const handleSendMessage = (msg: string) => {
    setMessages((history) => [...history, { text: msg, sender: "human" }]);
    console.log("call the api with: ", msg);
    setMessages((history) => [
      ...history,
      { text: "some response...", sender: "bot" },
    ]);
  };

  return (
    <DefaultLayout>
      <div className="flex flex-col h-full min-h-0">
        <ChatHistory messages={messages} />
        <ChatInput onSend={(newQuestion) => handleSendMessage(newQuestion)} />
      </div>
    </DefaultLayout>
  );
}
