import DefaultLayout from "@/layouts/default";
import { Card, CardHeader, CardBody, CardFooter } from "@nextui-org/react";
import { ChatInput } from "@/components/ChatInput";
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
      <Card
        className="flex-grow"
        style={{ padding: "20px", maxWidth: "400px", margin: "auto" }}
      >
        <CardHeader>
          <h3>Fabi</h3>
        </CardHeader>
        <CardBody style={{ height: "300px", overflowY: "scroll" }}>
          {messages.map((msg, index) => {
            console.log(msg, index);
            return <div>fabi</div>;
          })}
        </CardBody>
        <CardFooter></CardFooter>
      </Card>

      <ChatInput onSend={(newQuestion) => console.log(newQuestion)} />
    </DefaultLayout>
  );
}
