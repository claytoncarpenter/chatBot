import React, { useState } from "react";

const GROK_API_URL = "http://localhost:3001/api/grok";

export default function ChatBot() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);

    const sendMessage = async () => {
        console.log("Send button clicked");
        if (!input.trim()) return;
        const userMessage = { role: "user", content: input };
        const newMessages = [...messages, userMessage];
        setMessages(newMessages);
        setLoading(true);

        try {
            const response = await fetch(GROK_API_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer API_KEY"
                },
                body: JSON.stringify({
                    messages: newMessages
                })
            });
            console.log("API response status:", response.status);
            const data = await response.json();
            console.log("API response data:", data);
            const botMessage = {
                role: "assistant",
                content: data.choices?.[0]?.message?.content?.content || "No response"
            };
            setMessages([...newMessages, botMessage]);
        } catch (err) {
            console.error("API error:", err);
            setMessages([...newMessages, { role: "assistant", content: "Error: " + err.message }]);
        }
        setInput("");
        setLoading(false);
    };

    return (
        <div>
            <div style={{ minHeight: 200, border: "1px solid #ccc", padding: 10 }}>
                {messages.map((msg, i) => (
                    <div key={i}><b>{msg.role}:</b> {msg.content}</div>
                ))}
                {loading && <div>Loading...</div>}
            </div>
            <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === "Enter" && sendMessage()}
                disabled={loading}
                style={{ width: "80%" }}
            />
            <button onClick={sendMessage} disabled={loading}>Send</button>
        </div>
    );
}
