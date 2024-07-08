import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';
import './ChatbotUI.css';

const axiosInstance = axios.create({
  baseURL: process.env.NODE_ENV === 'development' 
    ? 'http://127.0.0.1:8000/api'
    : 'https://port-0-fastapi-dc9c2nlsw04cjb.sel5.cloudtype.app/api',
});

const ChatbotUI = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const { transcript, resetTranscript, browserSupportsSpeechRecognition } = useSpeechRecognition();
  const [isListening, setIsListening] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (!browserSupportsSpeechRecognition) {
      alert('Your browser does not support speech recognition.');
    }
  }, [browserSupportsSpeechRecognition]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const startListening = () => {
    setIsListening(true);
    SpeechRecognition.startListening({ continuous: true, language: 'ko' });
  };

  const stopListening = () => {
    setIsListening(false);
    SpeechRecognition.stopListening();
    handleSend(transcript);
    resetTranscript();
  };

  const speak = (text) => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ko-KR';
    window.speechSynthesis.speak(utterance);
  };

  const getAnswer = async (text) => {
    try {
      const response = await axiosInstance.post(
        "/use_chain",
        { query: text },
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error:', error);
      return "죄송합니다. 답변을 생성하는 데 문제가 발생했습니다.";
    }
  };

  const handleSend = async (text = input) => {
    if (text.trim() === '') return;

    const newMessage = { text: text, sender: 'user' };
    setMessages(prevMessages => [...prevMessages, newMessage]);
    setInput('');

    const answer = await getAnswer(text);
    const botMessage = { text: answer, sender: 'bot' };
    setMessages(prevMessages => [...prevMessages, botMessage]);

    speak(answer);
    resetTranscript(); // Ensure transcript is reset after handling send
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  return (
    <div className="chatbot-container">
      <div className="chat-header">
        <h2>AI 챗봇</h2>
      </div>
      <div className="chat-messages">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.sender}`}>
            {message.sender === 'user' ? '👤' : '🤖'} {message.text}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="메시지를 입력하세요..."
          onKeyDown={handleKeyDown}
        />
        <button onClick={() => handleSend()} className="send-button">
          전송
        </button>
        <button 
          onClick={isListening ? stopListening : startListening}
          className={`voice-button ${isListening ? 'listening' : ''}`}
        >
          {isListening ? '음성 입력 중지' : '음성 입력 시작'}
        </button>
      </div>
    </div>
  );
};

export default ChatbotUI;
