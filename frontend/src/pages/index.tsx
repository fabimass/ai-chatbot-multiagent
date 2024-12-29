import DefaultLayout from "@/layouts/default";
import { ChatInput } from "@/components/ChatInput";
import { ChatHistory, ChatHistoryProps } from "@/components/ChatHistory";
import { useState, useEffect } from "react";
import { getEnv } from "@/utils/getEnv";

export default function IndexPage() {
  const [messages, setMessages] = useState<ChatHistoryProps["messages"]>([]);
  const [loading, setLoading] = useState(false);

  // Generate a unique session_id for the user
  const sessionId =
    localStorage.getItem("chatbot_session_id") || crypto.randomUUID();
  localStorage.setItem("chatbot_session_id", sessionId);

  useEffect(() => {
    fetch(`${getEnv()["backend_url"]}/api/greetings`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((response) => response.json())
      .then((result) => {
        console.log(result);
        setMessages((history) => [
          ...history,
          { text: result["answer"], sender: "bot" },
        ]);
      })
      .catch((error) => {
        setMessages((history) => [
          ...history,
          {
            text: "whoops, something went wrong! 😵",
            sender: "bot",
          },
        ]);
        console.error(error);
      });
  }, []);

  const handleSendMessage = (msg: string) => {
    setMessages((history) => [...history, { text: msg, sender: "human" }]);
    console.log("human message: ", msg);

    setLoading(true);

    fetch(`${getEnv()["backend_url"]}/api/ask`, {
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
        setLoading(false);
      })
      .catch((error) => {
        setLoading(false);
        console.error(error);
      });
  };

  return (
    <DefaultLayout>
      <div className="flex flex-col h-full min-h-0">
        <ChatHistory messages={messages} />
        <ChatInput
          onSend={(newQuestion) => handleSendMessage(newQuestion)}
          loading={loading}
        />
      </div>
    </DefaultLayout>
  );
}
