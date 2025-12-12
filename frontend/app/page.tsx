"use client";

import React, {
  useEffect,
  useMemo,
  useRef,
  useState,
  useCallback,
} from "react";

// ===== TYPES =====
type ChatMsg = {
  role: "user" | "assistant";
  content: string;
  id?: number;
  reactions?: string[];
  bookmarked?: boolean;
};
type VoiceConfig = {
  voices: Record<string, string>;
  default_voice: string;
  recommended: string;
  speed_min: number;
  speed_max: number;
  default_speed: number;
};
type Session = {
  id: number;
  title: string;
  persona: string;
  created_at: string;
  updated_at: string;
  message_count: number;
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ===== VOICE INPUT HOOK =====
function useVoiceInput() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [isSupported, setIsSupported] = useState(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      setIsSupported(true);
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = "en-US"; // Can be changed to "ja-JP", "vi-VN", etc.

      recognition.onresult = (event) => {
        const current = event.resultIndex;
        const result = event.results[current];
        setTranscript(result[0].transcript);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  }, []);

  const startListening = useCallback(() => {
    if (recognitionRef.current && !isListening) {
      setTranscript("");
      recognitionRef.current.start();
      setIsListening(true);
    }
  }, [isListening]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  }, [isListening]);

  return {
    isListening,
    transcript,
    isSupported,
    startListening,
    stopListening,
    setTranscript,
  };
}

// ===== MAIN COMPONENT =====
export default function Home() {
  // Chat state
  const [message, setMessage] = useState("");
  const [history, setHistory] = useState<ChatMsg[]>([]);
  const [status, setStatus] = useState("Ready");
  const [loading, setLoading] = useState(false);

  // Dark mode state
  const [darkMode, setDarkMode] = useState(false);

  // Reactions state
  const [showReactionPopup, setShowReactionPopup] = useState<number | null>(
    null
  );
  const availableReactions = ["❤️", "👍", "😊", "🎉", "💡", "📌"];

  // Voice TTS state
  const [voices, setVoices] = useState<Record<string, string>>({});
  const [voice, setVoice] = useState("Arista-PlayAI");
  const [speed, setSpeed] = useState(1.05);
  const [textOnly, setTextOnly] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Session/History state
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);
  const [showSidebar, setShowSidebar] = useState(true);

  // Voice input
  const {
    isListening,
    transcript,
    isSupported,
    startListening,
    stopListening,
    setTranscript,
  } = useVoiceInput();
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }
  }, [history]);

  // Update message when transcript changes
  useEffect(() => {
    if (transcript) {
      setMessage(transcript);
    }
  }, [transcript]);

  // Dark mode initialization and toggle
  useEffect(() => {
    // Check localStorage or system preference
    const savedTheme = localStorage.getItem("theme");
    const prefersDark = window.matchMedia(
      "(prefers-color-scheme: dark)"
    ).matches;

    if (savedTheme === "dark" || (!savedTheme && prefersDark)) {
      setDarkMode(true);
      document.documentElement.classList.add("dark");
    }
  }, []);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    if (!darkMode) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  };

  // Reaction handlers
  const addReaction = (messageIndex: number, emoji: string) => {
    setHistory((prev) =>
      prev.map((msg, i) => {
        if (i === messageIndex) {
          const currentReactions = msg.reactions || [];
          const hasReaction = currentReactions.includes(emoji);
          return {
            ...msg,
            reactions: hasReaction
              ? currentReactions.filter((r) => r !== emoji)
              : [...currentReactions, emoji],
          };
        }
        return msg;
      })
    );
    setShowReactionPopup(null);
  };

  const toggleBookmark = (messageIndex: number) => {
    setHistory((prev) =>
      prev.map((msg, i) => {
        if (i === messageIndex) {
          return { ...msg, bookmarked: !msg.bookmarked };
        }
        return msg;
      })
    );
  };

  // Load voice config on mount
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const res = await fetch(`${API_BASE}/voice/groq/config`);
        if (!res.ok) return;
        const cfg: VoiceConfig = await res.json();
        setVoices(cfg.voices);
        setVoice(cfg.default_voice ?? "Fritz-PlayAI");
        setSpeed(cfg.default_speed ?? 1.05);
      } catch (e) {
        console.error(e);
      }
    };
    loadConfig();
  }, []);

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  // Play audio when URL changes
  useEffect(() => {
    if (audioUrl && audioRef.current) {
      audioRef.current.src = audioUrl;
      audioRef.current.play().catch(() => undefined);
    }
  }, [audioUrl]);

  // ===== API FUNCTIONS =====
  const loadSessions = async () => {
    try {
      const res = await fetch(`${API_BASE}/sessions`);
      if (!res.ok) return;
      const data = await res.json();
      setSessions(data.sessions || []);
    } catch (e) {
      console.error("Failed to load sessions:", e);
    }
  };

  const loadSession = async (sessionId: number) => {
    try {
      const res = await fetch(`${API_BASE}/sessions/${sessionId}`);
      if (!res.ok) return;
      const data = await res.json();
      setHistory(
        data.messages.map((m: any) => ({
          role: m.role,
          content: m.content,
          id: m.id,
        }))
      );
      setCurrentSessionId(sessionId);
      setStatus(`Loaded: ${data.session.title}`);
    } catch (e) {
      console.error("Failed to load session:", e);
    }
  };

  const createNewSession = async () => {
    setHistory([]);
    setCurrentSessionId(null);
    setAudioUrl(null);
    setStatus("New chat started");
  };

  const deleteSession = async (sessionId: number) => {
    try {
      await fetch(`${API_BASE}/sessions/${sessionId}?permanent=true`, {
        method: "DELETE",
      });
      await loadSessions();
      if (currentSessionId === sessionId) {
        createNewSession();
      }
    } catch (e) {
      console.error("Failed to delete session:", e);
    }
  };

  const sendChat = async () => {
    if (!message.trim()) return;

    const userMsg: ChatMsg = { role: "user", content: message.trim() };
    setHistory((h) => [...h, userMsg]);
    setMessage("");
    setTranscript("");
    setLoading(true);
    setStatus("Thinking...");

    try {
      // Use session endpoint for auto-save
      const res = await fetch(`${API_BASE}/chat/session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMsg.content,
          session_id: currentSessionId,
          persona: "iroha",
        }),
      });

      if (!res.ok) throw new Error(`Chat failed (${res.status})`);
      const data = await res.json();

      // Update session ID if new
      if (data.metadata?.session_id && !currentSessionId) {
        setCurrentSessionId(data.metadata.session_id);
        loadSessions(); // Refresh sidebar
      }

      const botMsg: ChatMsg = { role: "assistant", content: data.response };
      setHistory((h) => [...h, botMsg]);
      setStatus(`Response time: ${data?.metadata?.duration_seconds ?? "?"}s`);

      // Generate voice if not text-only
      if (!textOnly) {
        setStatus("Generating voice...");
        const voiceRes = await fetch(
          `${API_BASE}/voice/groq/stream?text=${encodeURIComponent(
            data.response
          )}&voice=${encodeURIComponent(voice)}&speed=${encodeURIComponent(
            speed.toString()
          )}`,
          { method: "POST" }
        );
        if (!voiceRes.ok) throw new Error(`TTS failed (${voiceRes.status})`);
        const buf = await voiceRes.arrayBuffer();
        setAudioUrl(
          URL.createObjectURL(new Blob([buf], { type: "audio/wav" }))
        );
        setStatus("Ready");
      }
    } catch (err: any) {
      console.error(err);
      setStatus(`Error: ${err?.message ?? err}`);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendChat();
    }
  };

  const clearAll = () => {
    setHistory([]);
    setAudioUrl(null);
    setCurrentSessionId(null);
    setStatus("Cleared");
  };

  // ===== RENDER =====
  return (
    <main
      className={`min-h-screen flex transition-colors duration-300 ${
        darkMode ? "dark" : ""
      }`}
    >
      {/* Sidebar - Studygram Style */}
      {showSidebar && (
        <aside className="w-72 border-r-2 border-dashed border-dot-grid bg-paper-white dark:bg-dark-surface flex flex-col transition-colors duration-300">
          {/* Logo Area */}
          <div className="p-5 border-b-2 border-dashed border-dot-grid">
            <div className="text-center">
              <h2 className="title-sunset text-2xl">Study Notes</h2>
              <p className="font-note text-ink-secondary text-sm mt-1">
                ✨ Chat History ✨
              </p>
            </div>
            <button
              onClick={createNewSession}
              className="btn-hand btn-hand-pink w-full mt-4 text-sm"
            >
              📝 New Chat
            </button>
          </div>

          {/* Sessions List */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {sessions.length === 0 ? (
              <div
                className="sticky-note sticky-blue mx-auto mt-4 text-center"
                style={{ transform: "rotate(1deg)" }}
              >
                <p className="font-hand text-ink-secondary">No notes yet!</p>
                <p className="font-note text-sm mt-2">
                  Start chatting with Iroha~ 💕
                </p>
              </div>
            ) : (
              sessions.map((s, idx) => (
                <div
                  key={s.id}
                  className={`group relative p-3 rounded-xl cursor-pointer transition-all duration-200 border-2 ${
                    currentSessionId === s.id
                      ? "bg-sticky-pink border-pink-300 shadow-sticky"
                      : "bg-paper-white dark:bg-dark-card border-transparent hover:border-dot-grid hover:shadow-sticky"
                  }`}
                  style={{ transform: `rotate(${idx % 2 === 0 ? -1 : 1}deg)` }}
                  onClick={() => loadSession(s.id)}
                >
                  <div className="font-hand text-ink-primary truncate">
                    {s.title}
                  </div>
                  <div className="font-note text-xs text-ink-secondary mt-1">
                    📚 {s.message_count} messages
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteSession(s.id);
                    }}
                    className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 text-accent-rose hover:scale-110 transition-all"
                  >
                    ✕
                  </button>
                </div>
              ))
            )}
          </div>

          {/* Decorative Footer */}
          <div className="p-4 border-t-2 border-dashed border-dot-grid text-center">
            <p className="font-note text-xs text-ink-secondary">
              🌸 Made with love 🌸
            </p>
          </div>
        </aside>
      )}

      {/* Main Content - Paper Style */}
      <div className="flex-1 flex items-center justify-center py-8 px-4 dot-grid">
        <div className="w-full max-w-4xl paper-card p-6 space-y-5 relative transition-colors duration-300">
          {/* Washi Tape Decoration */}
          <div
            className="washi-tape washi-blue"
            style={{ top: "-12px", left: "20%", transform: "rotate(-5deg)" }}
          ></div>
          <div
            className="washi-tape"
            style={{ top: "-12px", right: "20%", transform: "rotate(3deg)" }}
          ></div>

          {/* Header */}
          <header className="space-y-4 pt-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => setShowSidebar(!showSidebar)}
                  className="text-ink-secondary hover:text-ink-primary text-xl transition-colors"
                  title="Toggle sidebar"
                >
                  📓
                </button>
                <div>
                  <h1 className="title-sunset text-3xl">Iroha Chat</h1>
                  <p className="font-hand text-ink-secondary text-sm">
                    Your cute study buddy~ ✨
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                {/* Dark Mode Toggle */}
                <button
                  onClick={toggleDarkMode}
                  className="p-2 rounded-full bg-sticky-yellow dark:bg-sticky-dark-yellow border-2 border-yellow-300 dark:border-yellow-600 hover:scale-110 transition-all"
                  title={
                    darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"
                  }
                >
                  {darkMode ? "☀️" : "🌙"}
                </button>

                {currentSessionId && (
                  <span className="font-note text-xs text-ink-secondary bg-sticky-yellow dark:bg-sticky-dark-yellow px-3 py-1 rounded-lg border border-yellow-300 dark:border-yellow-600">
                    📌 Note #{currentSessionId}
                  </span>
                )}
              </div>
            </div>

            {/* Controls - Sticky Note Style */}
            <div className="flex flex-wrap gap-4 items-center">
              <div className="flex items-center gap-2 bg-sticky-blue dark:bg-sticky-dark-blue px-3 py-2 rounded-lg border border-blue-200 dark:border-blue-700">
                <span className="font-hand text-sm text-ink-primary">
                  🎤 Voice
                </span>
                <select
                  value={voice}
                  onChange={(e) => setVoice(e.target.value)}
                  className="input-paper text-sm py-1"
                >
                  {Object.entries(voices).map(([k, v]) => (
                    <option key={k} value={k}>
                      {k}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-2 bg-sticky-green dark:bg-sticky-dark-green px-3 py-2 rounded-lg border border-green-200 dark:border-green-700">
                <span className="font-hand text-sm text-ink-primary">
                  ⚡ Speed
                </span>
                <input
                  type="range"
                  min={0.5}
                  max={2}
                  step={0.05}
                  value={speed}
                  onChange={(e) => setSpeed(parseFloat(e.target.value))}
                  className="w-20 accent-accent-rose"
                />
                <span className="font-note text-xs text-ink-secondary w-10">
                  {speed.toFixed(2)}
                </span>
              </div>

              <label className="flex items-center gap-2 bg-sticky-pink dark:bg-sticky-dark-pink px-3 py-2 rounded-lg border border-pink-200 dark:border-pink-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={textOnly}
                  onChange={(e) => setTextOnly(e.target.checked)}
                  className="accent-accent-rose"
                />
                <span className="font-hand text-sm text-ink-primary">
                  📝 Text only
                </span>
              </label>
            </div>
          </header>

          {/* Chat Area - Notebook Style */}
          <div
            ref={chatContainerRef}
            className="h-[380px] rounded-xl bg-paper-white dark:bg-dark-surface border-2 border-dashed border-dot-grid p-4 overflow-y-auto space-y-4 transition-colors duration-300"
            style={{
              backgroundImage: darkMode
                ? "repeating-linear-gradient(transparent, transparent 31px, #334155 31px, #334155 32px)"
                : "repeating-linear-gradient(transparent, transparent 31px, #e5d4c0 31px, #e5d4c0 32px)",
              backgroundSize: "100% 32px",
            }}
          >
            {history.length === 0 && (
              <div className="text-center py-8">
                <div
                  className="inline-block sticky-note sticky-yellow"
                  style={{ transform: "rotate(-2deg)" }}
                >
                  <p className="font-hand text-ink-primary text-lg">
                    Hi there, Senpai~ 💕
                  </p>
                  <p className="font-note text-ink-secondary mt-2">
                    Say something to start our study session!
                  </p>
                </div>
              </div>
            )}

            {history.map((m, i) => (
              <div
                key={i}
                className={`message-wrapper relative flex ${
                  m.role === "user" ? "justify-end" : "justify-start"
                } animate-pop group`}
              >
                {/* Bookmark */}
                <div
                  className={`bookmark-btn ${m.bookmarked ? "active" : ""}`}
                  onClick={() => toggleBookmark(i)}
                  title={m.bookmarked ? "Remove bookmark" : "Add bookmark"}
                />

                <div
                  className={`max-w-[80%] px-4 py-3 relative ${
                    m.role === "user"
                      ? "chat-bubble-user"
                      : "chat-bubble-assistant"
                  }`}
                >
                  <div className="font-hand text-xs font-semibold mb-1 opacity-80">
                    {m.role === "user" ? "📚 You" : "🌸 Iroha"}
                  </div>
                  <div className="font-note text-sm leading-7 whitespace-pre-wrap">
                    {m.content}
                  </div>

                  {/* Reactions Display */}
                  {m.reactions && m.reactions.length > 0 && (
                    <div className="flex gap-1 mt-2 flex-wrap">
                      {m.reactions.map((emoji, idx) => (
                        <span
                          key={idx}
                          className="text-sm bg-white/50 dark:bg-black/20 px-1.5 py-0.5 rounded-full"
                        >
                          {emoji}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Reaction Button */}
                  <div className="absolute -bottom-3 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="relative">
                      <button
                        onClick={() =>
                          setShowReactionPopup(
                            showReactionPopup === i ? null : i
                          )
                        }
                        className="reaction-btn"
                      >
                        😊
                      </button>

                      {/* Reaction Popup */}
                      <div
                        className={`reaction-popup ${
                          showReactionPopup === i ? "show" : ""
                        }`}
                      >
                        {availableReactions.map((emoji) => (
                          <button
                            key={emoji}
                            onClick={() => addReaction(i, emoji)}
                            className={`reaction-btn ${
                              m.reactions?.includes(emoji) ? "active" : ""
                            }`}
                          >
                            {emoji}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start animate-pop">
                <div className="chat-bubble-assistant px-4 py-3">
                  <div className="font-hand text-xs font-semibold mb-1 opacity-80">
                    🌸 Iroha
                  </div>
                  {/* Improved Typing Indicator */}
                  <div className="flex items-center gap-3">
                    <div className="flex gap-1.5">
                      <span className="typing-dot"></span>
                      <span className="typing-dot"></span>
                      <span className="typing-dot"></span>
                    </div>
                    <span className="font-note text-sm text-ink-secondary dark:text-ink-dark-secondary thinking-emoji">
                      💭
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="space-y-4">
            <div className="flex gap-3">
              <div className="flex-1 relative">
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={
                    isListening
                      ? "🎤 Listening..."
                      : "✏️ Write your message here..."
                  }
                  className={`input-paper w-full h-24 resize-none font-note ${
                    isListening ? "border-accent-rose border-solid" : ""
                  }`}
                  disabled={isListening}
                />
                {/* Mic Button */}
                {isSupported && (
                  <button
                    onClick={isListening ? stopListening : startListening}
                    className={`absolute right-3 top-3 p-2 rounded-full transition-all ${
                      isListening
                        ? "bg-accent-rose text-white animate-pulse shadow-lg"
                        : "bg-sticky-pink border-2 border-pink-300 text-accent-rose hover:scale-110"
                    }`}
                    title={isListening ? "Stop recording" : "Start voice input"}
                  >
                    {isListening ? "⏹️" : "🎤"}
                  </button>
                )}
              </div>

              <div className="flex flex-col gap-2">
                <button
                  onClick={sendChat}
                  disabled={loading || !message.trim()}
                  className="btn-hand btn-hand-pink disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? "..." : "Send 💌"}
                </button>
                <button
                  onClick={clearAll}
                  className="btn-hand btn-hand-blue text-sm py-2"
                >
                  Clear 🗑️
                </button>
              </div>
            </div>

            {/* Audio Player & Status */}
            <div className="flex items-center gap-4 bg-sticky-yellow/50 dark:bg-sticky-dark-yellow/50 p-3 rounded-xl border border-yellow-200 dark:border-yellow-700">
              <span className="font-hand text-sm text-ink-primary">🔊</span>
              <audio
                ref={audioRef}
                controls
                className="flex-1 h-10 rounded-lg"
              />
              <div className="font-note text-xs text-ink-secondary whitespace-nowrap px-2 py-1 bg-paper-white dark:bg-dark-surface rounded-lg">
                {status}
              </div>
            </div>
          </div>

          {/* Decorative Corner Doodles */}
          <div className="absolute bottom-2 right-4 font-script text-2xl opacity-20 text-accent-rose dark:text-accent-pink">
            ♡
          </div>
        </div>
      </div>
    </main>
  );
}

// Add SpeechRecognition types
declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof SpeechRecognition;
  }
}
