
const DEFAULT_MODELS = {
  "/v1/chat/completions": "phi4",
  "/v1/embeddings": "granite-embedding:278m"
};

export const DEFAULT_BODIES = {
  "/v1/chat/completions": {
    model: DEFAULT_MODELS["/v1/chat/completions"],
    messages: [{ role: "user", content: "Learn me something!" }]
  },
  "/v1/embeddings": {
    model: DEFAULT_MODELS["/v1/embeddings"],
    input: [
      "Sun is shining in the blue sky.",
      "Clever Cloud is a great PaaS to use!",
      "AI is changing the world as we know it."
    ]
  }
};

export const DEFAULT_CONFIG = {
  host: "example.com",
  port: "11434",
  tls: false
};
