// File Path: components/agent/ChatInterface.tsx
// Description: Component responsible for rendering the chat message display area and the message input form.
// Dependencies:
// - React: For component structure, state management (passed as props or managed via context/hooks later).
// - ../../app/(agent)/actions (indirectly, via props): For sending messages.
// - Tailwind CSS: For styling.
// Dependents:
// - app/(agent)/page.tsx: This component will be used within the main agent page.

'use client';

import React, { useState, FormEvent, useEffect, useRef } from 'react';

// Type for individual chat messages (can be shared or moved to a types file)
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  isStreaming?: boolean;
}

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (messageText: string) => Promise<void>; // Simplified callback for sending
  isSending: boolean;
  currentConversationId: string | null;
}

export default function ChatInterface({
  messages,
  onSendMessage,
  isSending,
  currentConversationId,
}: ChatInterfaceProps) {
  const [messageInput, setMessageInput] = useState("");
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleLocalFormSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!messageInput.trim() || isSending) return;
    
    const textToSend = messageInput;
    setMessageInput(""); // Clear input locally
    await onSendMessage(textToSend); // Call the passed-in send message handler
  };

  return (
    <section className="w-full h-full flex flex-col bg-white dark:bg-gray-900 rounded-lg shadow overflow-hidden">
      {/* Message Display Area */}
      <div ref={chatContainerRef} className="flex-grow p-4 overflow-y-auto border-b border-gray-200 dark:border-gray-700 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 dark:text-gray-400 py-20">
            <p>No messages yet.</p>
            <p className="text-xs mt-1">Send a message to start the chat.</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div 
              key={msg.id} 
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div 
                className={`whitespace-pre-wrap max-w-xl lg:max-w-2xl px-4 py-2 rounded-lg shadow ${ 
                  msg.role === 'user' 
                    ? 'bg-blue-500 text-white' 
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
                }`}>
                <p className="text-sm">{msg.content}{msg.isStreaming && msg.role === 'assistant' ? "" : ""}</p>
                {msg.timestamp && !msg.isStreaming && (
                  <p className={`text-xs mt-1 ${msg.role === 'user' ? 'text-blue-200' : 'text-gray-500 dark:text-gray-400'}`}>
                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Message Input Area */}
      <div className="flex-shrink-0 p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
        <form className="flex gap-2" onSubmit={handleLocalFormSubmit}>
          <input
            type="text"
            placeholder={`Type message${currentConversationId ? " to "+currentConversationId.substring(0,8)+"..." : "..."}`}
            value={messageInput}
            onChange={(e) => setMessageInput(e.target.value)}
            disabled={isSending}
            className="flex-grow p-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none bg-white dark:bg-gray-700 text-foreground disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isSending || !messageInput.trim()}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 outline-none transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSending ? 'Sending...' : 'Send'}
          </button>
        </form>
      </div>
    </section>
  );
} 