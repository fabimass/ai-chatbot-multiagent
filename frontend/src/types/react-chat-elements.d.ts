declare module "react-chat-elements" {
  import * as React from "react";

  export interface MessageBoxProps {
    position?: "left" | "right";
    type?: string;
    title?: string;
    text?: string;
    date?: Date;
    titleColor?: string;
    forwarded?: boolean;
    replyButton?: boolean;
    removeButton?: boolean;
    status?: string;
    notch?: boolean;
    retracted?: boolean;
    id?: string;
    focus?: boolean;
  }

  export class MessageBox extends React.Component<MessageBoxProps> {}
}
