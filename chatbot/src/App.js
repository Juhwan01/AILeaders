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
  const [messages, setMessages] = useState(() => {
    const savedMessages = localStorage.getItem('chatMessages');
    return savedMessages ? JSON.parse(savedMessages) : [];
  });
  const [input, setInput] = useState('');
  const { transcript, resetTranscript, browserSupportsSpeechRecognition } = useSpeechRecognition();
  const [isListening, setIsListening] = useState(false);
  const messagesEndRef = useRef(null);
  const [language, setLanguage] = useState('ko');

  useEffect(() => {
    if (!browserSupportsSpeechRecognition) {
      alert('Your browser does not support speech recognition.');
    }
  }, [browserSupportsSpeechRecognition]);

  useEffect(() => {
    scrollToBottom();
    localStorage.setItem('chatMessages', JSON.stringify(messages));
  }, [messages]);

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

  const speak = async (text) => {
    try {
      const response = await axiosInstance.post(
        "/tts",
        { text: text, lang: language === 'ko' ? 'ko' : 'en' },
        { responseType: 'blob' }
      );
      
      const audioBlob = new Blob([response.data], { type: 'audio/mpeg' });
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audio.play();
    } catch (error) {
      console.error('TTS Error:', error);
    }
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
    resetTranscript();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  const handleEndChat = async () => {
    try {
      // 서버에 대화 내용 전송
      await axiosInstance.post("/save_chat", { messages: messages });
      
      // 대화 내용 초기화
      setMessages([]);
      localStorage.removeItem('chatMessages');
      
      alert('대화가 서버에 저장되었고, 채팅이 초기화되었습니다.');
    } catch (error) {
      console.error('Error saving chat:', error);
      alert('대화 저장 중 오류가 발생했습니다.');
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
        <button onClick={handleEndChat} className="end-chat-button">
          대화 종료
        </button>
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