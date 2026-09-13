
const DEFAULT_MODELS = {
  "/v1/chat/completions": "phi4",
  "/v1/embeddings": "granite-embedding:278m",
  "/v1/responses": "gpt-4o"
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
  },
  "/v1/responses": {
    model: DEFAULT_MODELS["/v1/responses"],
    instructions: "You are a helpful assistant. Be concise.",
    input: [
      { role: "user", content: "What is the Responses API?" }
    ],
    temperature: 0.7,
    max_output_tokens: 1024,
    tools: [
      { type: "web_search" }
    ],
    store: true
  },
  "/v1/responses/compact": {
    model: DEFAULT_MODELS["/v1/responses"],
    input: [
      {
        type: "message",
        role: "user",
        content: "Can you recommend a good recipe for banana bread?"
      },
      {
        id: "msg_001",
        type: "message",
        role: "assistant",
        status: "completed",
        content: [
          {
            type: "output_text",
            annotations: [],
            logprobs: [],
            text: "Sure! Mash 3 ripe bananas, mix with 75g melted butter, 150g sugar, 1 egg, 1 tsp vanilla, 1 tsp baking soda, and 185g flour. Pour into a loaf pan and bake at 175°C for about 60 minutes."
          }
        ]
      },
      {
        type: "message",
        role: "user",
        content: "Can I add chocolate chips?"
      },
      {
        id: "msg_002",
        type: "message",
        role: "assistant",
        status: "completed",
        content: [
          {
            type: "output_text",
            annotations: [],
            logprobs: [],
            text: "Absolutely! Fold in about 100g of chocolate chips into the batter just before pouring it into the pan. Dark chocolate works especially well with the banana flavor."
          }
        ]
      }
    ]
  }
};

export const DEFAULT_CONFIG = {
  host: "example.com",
  port: "11434",
  tls: false
};
