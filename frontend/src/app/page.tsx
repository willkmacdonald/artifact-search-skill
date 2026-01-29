"use client";

import { useState, useRef, useEffect } from "react";
import {
  Send,
  Loader2,
  ExternalLink,
  AlertCircle,
  CheckCircle2,
  FileText,
  Palette,
  Database,
  Network,
  Shield,
} from "lucide-react";

interface Artifact {
  id: string;
  source: string;
  type: string;
  title: string;
  content: string;
  url: string | null;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  artifacts?: Artifact[];
  sources?: string[];
  isLoading?: boolean;
}

const sourceIcons: Record<string, React.ReactNode> = {
  azure_devops: <Database className="w-4 h-4" />,
  figma: <Palette className="w-4 h-4" />,
  notion: <FileText className="w-4 h-4" />,
  icepanel: <Network className="w-4 h-4" />,
};

const sourceColors: Record<string, string> = {
  azure_devops: "bg-blue-100 text-blue-800 border-blue-200",
  figma: "bg-purple-100 text-purple-800 border-purple-200",
  notion: "bg-gray-100 text-gray-800 border-gray-200",
  icepanel: "bg-cyan-100 text-cyan-800 border-cyan-200",
};

const typeColors: Record<string, string> = {
  risk: "bg-red-100 text-red-800",
  mitigation: "bg-green-100 text-green-800",
  requirement: "bg-blue-100 text-blue-800",
  design: "bg-purple-100 text-purple-800",
  architecture: "bg-cyan-100 text-cyan-800",
  work_item: "bg-yellow-100 text-yellow-800",
  test_case: "bg-orange-100 text-orange-800",
  document: "bg-gray-100 text-gray-800",
};

const suggestedQueries = [
  "What are the risks related to alerts?",
  "Show me the system architecture for CardioWatch",
  "Find UI designs for the risk dashboard",
  "What mitigations exist for arrhythmia detection?",
  "Show requirements linked to RISK-001",
];

// API base URL - uses environment variable in production, empty string for local dev with proxy
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<
    "checking" | "connected" | "error"
  >("checking");
  const [configuredSources, setConfiguredSources] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    checkHealth();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const checkHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (response.ok) {
        const data = await response.json();
        setConnectionStatus("connected");
        setConfiguredSources(data.configured_sources || []);
      } else {
        setConnectionStatus("error");
      }
    } catch {
      setConnectionStatus("error");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    // Add loading message
    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "", isLoading: true },
    ]);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage, history: [] }),
      });

      if (!response.ok) throw new Error("Chat request failed");

      const data = await response.json();

      // Replace loading message with actual response
      setMessages((prev) => [
        ...prev.slice(0, -1),
        {
          role: "assistant",
          content: data.message,
          artifacts: data.artifacts,
          sources: data.sources_searched,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev.slice(0, -1),
        {
          role: "assistant",
          content:
            "Sorry, I encountered an error while searching. Please check that the backend is running.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestionClick = (query: string) => {
    setInput(query);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                MedTech Risk Copilot
              </h1>
              <p className="text-sm text-gray-500">
                AI-powered artifact search for risk management
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {connectionStatus === "checking" && (
              <span className="flex items-center gap-1 text-sm text-gray-500">
                <Loader2 className="w-4 h-4 animate-spin" />
                Connecting...
              </span>
            )}
            {connectionStatus === "connected" && (
              <span className="flex items-center gap-1 text-sm text-green-600">
                <CheckCircle2 className="w-4 h-4" />
                Connected
              </span>
            )}
            {connectionStatus === "error" && (
              <span className="flex items-center gap-1 text-sm text-red-600">
                <AlertCircle className="w-4 h-4" />
                Backend offline
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Connected Sources */}
      {configuredSources.length > 0 && (
        <div className="bg-white border-b border-gray-200 px-6 py-2">
          <div className="max-w-4xl mx-auto flex items-center gap-2">
            <span className="text-xs text-gray-500">Connected:</span>
            {configuredSources.map((source) => (
              <span
                key={source}
                className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs border ${
                  sourceColors[source] || "bg-gray-100"
                }`}
              >
                {sourceIcons[source]}
                {source.replace("_", " ")}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto px-6 py-4">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Shield className="w-8 h-8 text-primary-600" />
              </div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                Welcome to MedTech Risk Copilot
              </h2>
              <p className="text-gray-600 mb-8 max-w-lg mx-auto">
                Ask me about risks, mitigations, requirements, designs, or
                architecture for your medical device. I'll search across Azure
                DevOps, Figma, Notion, and Ice Panel.
              </p>
              <div className="flex flex-wrap gap-2 justify-center">
                {suggestedQueries.map((query) => (
                  <button
                    key={query}
                    onClick={() => handleSuggestionClick(query)}
                    className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:border-primary-300 hover:bg-primary-50 transition-colors"
                  >
                    {query}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-3xl rounded-2xl px-4 py-3 ${
                    message.role === "user"
                      ? "bg-primary-600 text-white"
                      : "bg-white border border-gray-200"
                  }`}
                >
                  {message.isLoading ? (
                    <div className="flex items-center gap-2 text-gray-500">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Searching across your tools...
                    </div>
                  ) : (
                    <>
                      <p
                        className={
                          message.role === "user"
                            ? "text-white"
                            : "text-gray-800"
                        }
                      >
                        {message.content}
                      </p>

                      {/* Sources searched */}
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-gray-100">
                          <span className="text-xs text-gray-500">
                            Searched:{" "}
                          </span>
                          {message.sources.map((source) => (
                            <span
                              key={source}
                              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ml-1 ${
                                sourceColors[source] || "bg-gray-100"
                              }`}
                            >
                              {sourceIcons[source]}
                              {source.replace("_", " ")}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Artifacts */}
                      {message.artifacts && message.artifacts.length > 0 && (
                        <div className="mt-4 space-y-2">
                          {message.artifacts.map((artifact) => (
                            <div
                              key={`${artifact.source}-${artifact.id}`}
                              className="bg-gray-50 rounded-lg p-3 border border-gray-100"
                            >
                              <div className="flex items-start justify-between gap-2">
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 mb-1">
                                    <span
                                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${
                                        sourceColors[artifact.source] ||
                                        "bg-gray-100"
                                      }`}
                                    >
                                      {sourceIcons[artifact.source]}
                                      {artifact.source.replace("_", " ")}
                                    </span>
                                    <span
                                      className={`px-2 py-0.5 rounded text-xs ${
                                        typeColors[artifact.type] ||
                                        "bg-gray-100"
                                      }`}
                                    >
                                      {artifact.type.replace("_", " ")}
                                    </span>
                                  </div>
                                  <h4 className="font-medium text-gray-900 text-sm">
                                    {artifact.title}
                                  </h4>
                                  {artifact.content && (
                                    <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                                      {artifact.content}
                                    </p>
                                  )}
                                </div>
                                {artifact.url && (
                                  <a
                                    href={artifact.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-primary-600 hover:text-primary-700 p-1"
                                  >
                                    <ExternalLink className="w-4 h-4" />
                                  </a>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Area */}
      <footer className="bg-white border-t border-gray-200 px-6 py-4">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="flex items-center gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about risks, requirements, designs, or architecture..."
              className="flex-1 px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              disabled={isLoading || connectionStatus === "error"}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim() || connectionStatus === "error"}
              className="px-4 py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
        </form>
      </footer>
    </div>
  );
}
