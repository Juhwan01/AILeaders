import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';
import './ChatbotUI.css';
import { CSSTransition, SwitchTransition } from 'react-transition-group';

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
  const [isLoading, setIsLoading] = useState(false);
  const [loadingDots, setLoadingDots] = useState('');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [showChatbot, setShowChatbot] = useState(false);

  useEffect(() => {
    if (!browserSupportsSpeechRecognition) {
      alert('Your browser does not support speech recognition.');
    }
  }, [browserSupportsSpeechRecognition]);

  useEffect(() => {
    scrollToBottom();
    localStorage.setItem('chatMessages', JSON.stringify(messages));
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

  const speak = async (text) => {
    try {
      setIsSpeaking(true);
      const response = await axiosInstance.post(
        "/tts",
        { text: text, lang: language === 'ko' ? 'ko' : 'en' },
        { responseType: 'blob' }
      );
      
      const audioBlob = new Blob([response.data], { type: 'audio/mpeg' });
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      
      audio.onended = () => setIsSpeaking(false);
      await audio.play();
    } catch (error) {
      console.error('TTS Error:', error);
      setIsSpeaking(false);
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

  const handleEndChat = async () => {
    try {
      const dialogueSetId = `B${Math.floor(Math.random() * 100000).toString().padStart(5, '0')}`;
      const formattedMessages = messages.map((message, index) => ({
        대화셋일련번호: dialogueSetId,
        고객질문: message.sender === 'user' ? message.text : "",
        상담사답변: message.sender === 'bot' ? message.text : ""
      }));
  
      await axiosInstance.post("/save_chat", { messages: formattedMessages });
      
      setMessages([]);
      localStorage.removeItem('chatMessages');
      
      alert('대화가 서버에 저장되었고, 채팅이 초기화되었습니다.');
      setShowChatbot(false);  // 챗봇 화면을 숨깁니다
    } catch (error) {
      console.error('Error saving chat:', error);
      alert('대화 저장 중 오류가 발생했습니다.');
    }
  };
  
  const TouchScreen = ({ onEnter }) => (
    <div className="touch-screen" onClick={onEnter}>
      <h1>터치하여 AI 챗봇 시작</h1>
    </div>
  );
  return (
    <SwitchTransition>
      <CSSTransition
        key={showChatbot ? "chatbot" : "touchscreen"}
        timeout={500}
        classNames="fade"
      >
        {showChatbot ? (
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
              disabled={isSpeaking || isLoading}
            />
            <button onClick={() => handleSend()} className="send-button" disabled={isSpeaking || isLoading}>
              전송
            </button>
            <button 
              onClick={isListening ? stopListening : startListening}
              className={`voice-button ${isListening ? 'listening' : ''}`}
              disabled={isSpeaking || isLoading}
            >
              {isListening ? '음성 입력 중지' : '음성 입력 시작'}
            </button>
          </div>
          </div>
        ) : (
          <TouchScreen onEnter={() => setShowChatbot(true)} />
        )}
      </CSSTransition>
    </SwitchTransition>
  );
};

export default ChatbotUI;
