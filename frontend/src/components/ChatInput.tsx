import { Textarea, Spinner } from "@nextui-org/react";
import { Send28Filled } from "@fluentui/react-icons";
import { useState } from "react";

interface ChatInputProps {
  onSend: (question: string) => void;
  loading: boolean;
}

export const ChatInput = ({ onSend, loading }: ChatInputProps) => {
  const [question, setQuestion] = useState<string>("");

  const handleSend = () => {
    if (question != "") {
      onSend(question);
      setQuestion("");
    }
  };

  return (
    <>
      <div className="content-center flex justify-center items-center my-5">
        <div className="relative w-[100%] max-w-[720px]">
          <Textarea
            placeholder="Ask me something..."
            onChange={(e) => setQuestion(e.target.value.replace(/\n/g, ""))}
            onKeyUp={(e) => e.key === "Enter" && handleSend()}
            value={question}
          />
          <div
            className="absolute bottom-0 right-0 p-2"
            aria-label="Ask question button"
            onClick={handleSend}
          >
            {loading ? (
              <Spinner size="md" color="primary" />
            ) : (
              <Send28Filled
                primaryFill="rgba(12, 105, 176, 1)"
                className="cursor-pointer"
              />
            )}
          </div>
        </div>
      </div>
    </>
  );
};
