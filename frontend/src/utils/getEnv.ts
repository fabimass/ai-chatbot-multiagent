export const getEnv = () => {
  return {
    backend_url: import.meta.env.VITE_API_URL,
  };
};
