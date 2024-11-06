import { Textarea } from "@nextui-org/react";
import { Send28Filled } from "@fluentui/react-icons";
import { useState } from "react";

interface ChatInputProps {
  onSend: (question: string) => void;
}

export const ChatInput = ({ onSend }: ChatInputProps) => {
  const [question, setQuestion] = useState<string>("");

  const handleSend = () => {
    onSend(question);
    setQuestion("");
  };

  return (
    <>
      <div className="content-center flex justify-center items-center my-5">
        <div className="relative w-3/4 max-w-[720px]">
          <Textarea
            placeholder="Ask me something..."
            onChange={(e) => setQuestion(e.target.value)}
            onKeyUp={(e) => e.key === "Enter" && handleSend()}
            value={question}
          />
          <div
            className="absolute bottom-0 right-0 p-2"
            aria-label="Ask question button"
            onClick={handleSend}
          >
            <Send28Filled
              primaryFill="rgba(12, 105, 176, 1)"
              className="cursor-pointer"
            />
          </div>
        </div>
      </div>
    </>
  );
};
