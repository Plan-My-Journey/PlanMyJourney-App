import { FormEvent, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Bot, Send } from "lucide-react";

import { api } from "../api/client";
import PageHeader from "../components/PageHeader";
import { ChatMessage } from "../types";

export default function AITravelAssistant() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Tell me where you are going, your dates, budget, and what you want to optimize."
    }
  ]);
  const [question, setQuestion] = useState("");
  const inputRef = useRef<HTMLInputElement | null>(null);

  const mutation = useMutation({
    mutationFn: async (nextQuestion: string) => (await api.post<{ answer: string }>("/ai/chat", { question: nextQuestion })).data,
    onSuccess: (data) => {
      setMessages((current) => [...current, { role: "assistant", content: data.answer }]);
      inputRef.current?.focus();
    },
    onError: () => {
      setMessages((current) => [...current, { role: "assistant", content: "Sorry, I couldn't reach the AI service right now. Please check if your network is stable or try a different question." }]);
    }
  });

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) {
      return;
    }
    setMessages((current) => [...current, { role: "user", content: trimmed }]);
    setQuestion("");
    mutation.mutate(trimmed);
  };

  return (
    <div>
      <PageHeader title="AI Travel Assistant" description="Ask trip planning, routing, safety, budget, and timing questions." />

      <section className="flex min-h-[calc(100vh-160px)] flex-col rounded-lg border border-zinc-200 bg-white">
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.map((message, index) => (
            <div key={`${message.role}-${index}`} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={[
                  "max-w-3xl rounded-lg px-4 py-3 text-sm leading-6",
                  message.role === "user" ? "bg-teal-700 text-white" : "bg-zinc-100 text-zinc-800"
                ].join(" ")}
              >
                {message.role === "assistant" && (
                  <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-zinc-600">
                    <Bot className="h-4 w-4" aria-hidden="true" />
                    Assistant
                  </div>
                )}
                {message.content}
              </div>
            </div>
          ))}
          {mutation.isPending && <div className="text-sm text-zinc-500">Assistant is thinking...</div>}
        </div>

        <form onSubmit={handleSubmit} className="flex gap-2 border-t border-zinc-200 p-4">
          <input
            ref={inputRef}
            className="field"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask about routes, budgets, hotels, packing, or weather"
          />
          <button type="submit" className="primary-button px-3" disabled={mutation.isPending || !question.trim()} aria-label="Send message">
            <Send className="h-4 w-4" aria-hidden="true" />
          </button>
        </form>
      </section>
    </div>
  );
}
