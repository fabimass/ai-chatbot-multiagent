import DefaultLayout from "@/layouts/default";
import { ChatInput } from "@/components/ChatInput";
import { ChatHistory } from "@/components/ChatHistory";
import { useState } from "react";

export default function IndexPage() {
  const [messages, setMessages] = useState([
    { text: "Hello! How can I assist you today?", sender: "bot" },
  ]);
  const [input, setInput] = useState("");

  const handleSendMessage = () => {
    if (input.trim()) {
      setMessages([...messages, { text: input, sender: "user" }]);
      setInput("");
    }
  };

  return (
    <DefaultLayout>
      <ChatHistory messages={messages} />

      <ChatInput onSend={(newQuestion) => console.log(newQuestion)} />
    </DefaultLayout>
  );
}
