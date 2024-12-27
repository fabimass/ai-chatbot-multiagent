import { MessageBox } from "react-chat-elements";
import { FaThumbsUp, FaThumbsDown } from "react-icons/fa";
import { useState, useEffect } from "react";
import { getEnv } from "@/utils/getEnv";

export interface ChatMessageProps {
  text: string;
  sender: string;
  previous?: string;
}

export const ChatMessage = ({ text, sender, previous }: ChatMessageProps) => {
  const [liked, setLiked] = useState<boolean | null>(null); // Tracks if the message was liked or disliked
  const [animating, setAnimating] = useState(false); // Controls animation on click
  const [showIcons, setShowIcons] = useState(true); // Controls visibility of icons

  const sendFeedback = (sentiment: boolean) => {
    fetch(`${getEnv()["backend_url"]}/api/feedback`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question: previous,
        answer: text,
        like: sentiment,
        session_id: localStorage.getItem("chatbot_session_id"),
      }),
    })
      .then((response) => response.json())
      .then((result) => {
        console.log(result);
      })
      .catch((error) => console.error(error));
  };

  const handleThumbsUp = () => {
    if (liked !== true) {
      setAnimating(true);
      setLiked(true);
      sendFeedback(true);
    }
  };

  const handleThumbsDown = () => {
    if (liked !== false) {
      setAnimating(true);
      setLiked(false);
      sendFeedback(false);
    }
  };

  // Reset animation state after it completes
  useEffect(() => {
    if (animating) {
      const timeoutId = setTimeout(() => {
        setAnimating(false);
        setShowIcons(false);
      }, 900);
      return () => clearTimeout(timeoutId);
    }
  }, [animating]);

  return (
    <div className="my-5">
      <div className={`relative ${sender === "bot" ? "inline-block" : ""}`}>
        <MessageBox
          position={sender === "human" ? "right" : "left"}
          type="text"
          title={sender}
          text={text}
          id=""
          focus={false}
          date={new Date()}
          titleColor="rgba(12, 105, 176, 1)"
          forwarded={false}
          replyButton={false}
          removeButton={false}
          status="read"
          notch={true}
          retracted={false}
        />
        {sender === "bot" && showIcons && (
          <div className="flex space-x-2 mt-2 absolute bottom-2 left-8">
            <button
              onClick={handleThumbsUp}
              className={`text-sm ${liked === true ? "text-green-500" : "text-gray-500"} ${animating ? (liked === true ? "animate-ping" : "animate-fade") : ""} hover:text-green-300`}
            >
              <FaThumbsUp />
            </button>
            <button
              onClick={handleThumbsDown}
              className={`text-sm ${liked === false ? "text-red-500" : "text-gray-500"} ${animating ? (liked === false ? "animate-ping" : "animate-fade") : ""} hover:text-red-300`}
            >
              <FaThumbsDown />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
