export type SiteConfig = typeof siteConfig;

export const siteConfig = {
  name: "RAG AI chatbot",
  description: "An AI-powered chatbot utilizing Retrieval-Augmented Generation (RAG) to deliver accurate and contextually relevant responses by combining the strengths of pre-trained language models with dynamic, real-time information retrieval.",
  navItems: [
    {
      label: "Home",
      href: "/",
    },
    {
      label: "About",
      href: "/about",
    },
  ],
  navMenuItems: [
    {
      label: "Home",
      href: "/",
    },
    {
      label: "About",
      href: "/about",
    },
  ],
  links: {
    github: "https://github.com/fabimass/rag-ai-chatbot",
  },
};
