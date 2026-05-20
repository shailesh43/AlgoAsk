"use client";

import { useState, useRef, useEffect } from "react";
import { Chat } from "@/components/ui/chat";

export default function Home() {
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Hello! I'm AlgoAsk. How can I help you?",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event:any) => {
    if (event) event.preventDefault();

    const userMessage = input.trim();
    if (!userMessage) return;

    const newMessages = [
      ...messages,
      { id: Date.now().toString(), role: "user", content: userMessage },
    ];
    setMessages(newMessages);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch("http://localhost:8080/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage }),
      });

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: data.response || "No response received.",
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "Failed to connect to the server. Please try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex h-screen flex-col bg-background mx-8 lg:mx-48 md:mx-20 pb-8 pt-4">
      <header className="px-6 py-4">
        <h1 className="text-xl font-semibold tracking-tight text-teal-300"> &#9786; AlgoAsk</h1>
        <p className="text-sm text-muted-foreground">
          RAG based Algorithm assistant
        </p>
      </header>

      <div className="flex-1 overflow-hidden">
        <Chat
          messages={messages}
          input={input}
          handleInputChange={(e) => setInput(e.target.value)}
          handleSubmit={handleSubmit}
          isGenerating={isLoading}
          className="h-full"
        />
      </div>
    </main>
  );
}