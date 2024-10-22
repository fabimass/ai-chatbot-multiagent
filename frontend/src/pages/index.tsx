import { Link } from "@nextui-org/link";
import { Snippet } from "@nextui-org/snippet";
import { Code } from "@nextui-org/code";
import { button as buttonStyles } from "@nextui-org/theme";

import { siteConfig } from "@/config/site";
import { title, subtitle } from "@/components/primitives";
import { GithubIcon } from "@/components/icons";
import DefaultLayout from "@/layouts/default";
import { Card, CardHeader, CardBody, CardFooter, Input, Button } from '@nextui-org/react';
import { useState } from 'react';

export default function IndexPage() {
  const [messages, setMessages] = useState([
    { text: 'Hello! How can I assist you today?', sender: 'bot' }
  ]);
  const [input, setInput] = useState('');

  const handleSendMessage = () => {
    if (input.trim()) {
      setMessages([...messages, { text: input, sender: 'user' }]);
      setInput('');
    }
  };

  return (
    <DefaultLayout>
    <Card style={{ padding: '20px', maxWidth: '400px', margin: 'auto' }}>
      <CardHeader>
        <h3>Fabi</h3>
      </CardHeader>
      <CardBody style={{ height: '300px', overflowY: 'scroll' }}>
        {messages.map((msg, index) => (
          <div>fabi</div>
        ))}
      </CardBody>
      <CardFooter>
        <Input
          
          placeholder="Type a message"
          fullWidth
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
        />
        <Button  onClick={handleSendMessage}>
          Send
        </Button>
      </CardFooter>
    </Card>
    </DefaultLayout>
  );
}
