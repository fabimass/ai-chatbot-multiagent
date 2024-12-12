import DefaultLayout from "@/layouts/default";
import { ChatInput } from "@/components/ChatInput";
import { ChatHistory, ChatHistoryProps } from "@/components/ChatHistory";
import { useState } from "react";

export default function IndexPage() {
  const [messages, setMessages] = useState<ChatHistoryProps["messages"]>([]);

  // Generate a unique session_id for the user
  const sessionId =
    localStorage.getItem("chatbot_session_id") || crypto.randomUUID();
  localStorage.setItem("chatbot_session_id", sessionId);

  const handleSendMessage = (msg: string) => {
    setMessages((history) => [...history, { text: msg, sender: "human" }]);
    console.log("human message: ", msg);

    fetch(`${import.meta.env.VITE_API_URL}/api/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question: msg,
        session_id: sessionId,
      }),
    })
      .then((response) => response.json())
      .then((result) => {
        console.log(result);
        setMessages((history) => [
          ...history,
          { text: result["answer"], sender: "bot" },
        ]);
      })
      .catch((error) => console.error(error));
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
