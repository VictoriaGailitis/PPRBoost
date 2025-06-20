import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import axios from 'axios';
import { API_URL } from '../../shared/consts';

const api = axios.create({
  baseURL: API_URL,
});

// Добавляем interceptor для вставки токена в заголовки
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});




export const rateMessage = createAsyncThunk(
  'chat/rateMessage',
  async({message_id, rating, chat_id}, { rejectWithValue }) => {
    try {
      const response = await api.post(`/rate_message`, {message_id:message_id,rating,});
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data);
    }
  }
)


const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    messages: [],
    loading: false
  },
  reducers: {
    addUserMessage: (state, action) => {
      state.messages.push({
        id: Date.now(),
        text: action.payload,
        isBot: false,
        time: new Date().toLocaleTimeString().slice(0, 5)
      });
    },
    addBotChunk: (state, action) => {
      if (!state.messages.length || !state.messages[state.messages.length-1].isBot) {
        state.messages.push({
          id: Date.now(),
          text: action.payload,
          isBot: true,
          time: new Date().toLocaleTimeString().slice(0, 5)
        });
      } else {
        state.messages[state.messages.length-1].text += action.payload;
      }
    },
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
    setMessages: (state, action) => { state.messages = action.payload; },
    clearChat: (state) => { state.messages = []; }
  },
});

export const { addUserMessage, addBotChunk, setLoading,setMessages, clearChat} = chatSlice.actions;
export default chatSlice.reducer;