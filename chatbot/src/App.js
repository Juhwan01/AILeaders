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
  const [language, setLanguage] = useState('ko');
  const [isLoading, setIsLoading] = useState(false); // 새로운 상태 추가
  const [loadingDots, setLoadingDots] = useState('');

  useEffect(() => {
    if (!browserSupportsSpeechRecognition) {
      alert('Your browser does not support speech recognition.');
    }
  }, [browserSupportsSpeechRecognition]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    let interval;
    if (isLoading) {
      let dots = '';
      interval = setInterval(() => {
        dots = dots.length >= 4 ? '' : dots + '.';
        setLoadingDots(dots);
      }, 500);
    }
    return () => clearInterval(interval);
  }, [isLoading]);

  const handleLanguageChange = (e) => {
    setLanguage(e.target.value);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const startListening = () => {
    setIsListening(true);
    SpeechRecognition.startListening({ continuous: true, language: language });
  };

  const stopListening = () => {
    setIsListening(false);
    SpeechRecognition.stopListening();
    handleSend(transcript);
    resetTranscript();
  };

  const speak = (text) => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = language === 'ko' ? 'ko-KR' : 'en-US';
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

    setIsLoading(true);
    setMessages(prevMessages => [...prevMessages, { sender: 'bot', loading: true }]);

    const answer = await getAnswer(text);
    
    setMessages(prevMessages => {
      const updatedMessages = [...prevMessages];
      updatedMessages[updatedMessages.length - 1] = { text: answer, sender: 'bot', loading: false };
      return updatedMessages;
    });
    setIsLoading(false);

    speak(answer);
    resetTranscript();
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
        <select value={language} onChange={handleLanguageChange} className="language-selector">
          <option value="ko">한국어</option>
          <option value="en">English</option>
        </select>
      </div>
      <div className="chat-messages">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.sender}`}>
            {message.sender === 'user' ? '👤' : '🤖'} 
            <div className="message-content">
              {message.loading ? (
                <div className="loading-message">
                  <span className="loading-text">AI가 답변을 생성 중입니다</span>
                  <span className="loading-dots">{loadingDots}</span>
                </div>
              ) : (
                message.text
              )}
            </div>
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
