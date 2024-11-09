import { MessageBox } from "react-chat-elements";
import { FaThumbsUp, FaThumbsDown } from "react-icons/fa";
import { useState } from "react";

export interface ChatMessageProps {
  text: string;
  sender: string;
}

export const ChatMessage = ({ text, sender }: ChatMessageProps) => {
  const [liked, setLiked] = useState<boolean | null>(null); // Tracks if the message was liked or disliked
  const [animating, setAnimating] = useState(false); // Controls animation on click

  const handleThumbsUp = () => {
    if (liked !== true) {
      setAnimating(true);
      setLiked(true);
    }
  };

  const handleThumbsDown = () => {
    if (liked !== false) {
      setAnimating(true);
      setLiked(false);
    }
  };

  return (
    <>
      <MessageBox
        position={sender === "human" ? "right" : "left"}
        type="text"
        title={sender}
        text={text}
      />
      <button
        onClick={handleThumbsUp}
        className={`text-2xl ${liked === true ? "text-green-500" : "text-gray-500"} ${animating ? "animate-ping" : ""}`}
      >
        <FaThumbsUp />
      </button>
    </>
  );
};
