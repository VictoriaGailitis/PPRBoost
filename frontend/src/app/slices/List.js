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


export const getAllChats = createAsyncThunk(
  'list/chats',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/chats');
      return {
        list: response.data,
      };
    } catch (error) {
      return rejectWithValue(error.response?.data);
    }
  }
);

export const createChat = createAsyncThunk(
  'list/createChat',
  async ({ title }, { rejectWithValue }) => {
    try {
      const response = await api.post('/create_chat',{title});
      return {
        id: response.data.id,
        title: response.data.title,
        activeId: response.data.id,
        messages: [{content:title, id: Date.now(), created_at: new Date().toLocaleDateString(), chat_id: response.data.id, }],
      };
    } catch (error) {
      return rejectWithValue(error.response?.data);
    }
  }
);

export const postCategory = createAsyncThunk(
  'list/postCategory',
  async ({text, chat_id}, { rejectWithValue }) => {
    try {
      const response = await api.post('/streaming/categorize', {text,chat_id});
      return {
        category: response.data,
        chat_id,
      };
    } catch (error) {
      return rejectWithValue(error.response?.data);
    }
  }
)

export const streamingChat = createAsyncThunk(
  'list/streamingChat',
  async ({message,reasoning,chat_id}, { rejectWithValue }) => {
    try {
      const response = await api.post(`/streaming/chat`,{message,reasoning,chat_id});
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data);
    }
  }
)


export const getCurrentChat = createAsyncThunk(
  'list/currentChat',
  async(id, { rejectWithValue }) => {
    try {
      const response = await api.get(`/chat/${id}`);
      return {
        chat:response.data,
        chat_id:id
      };
    } catch (error) {
      return rejectWithValue(error.response?.data);
    }
  }
)
export const deleteChat = createAsyncThunk(
  'list/deleteChat',
  async (id, { rejectWithValue }) => {
    try {
      await api.delete(`/chat/${id}`);
      return id;
    } catch (error) {
      return rejectWithValue(error.response?.data);
    }
  }
);

export const attachStreaming = createAsyncThunk(
  'list/attachStreaming',
  async ({ attachments, chatId, message, reasoning }, { rejectWithValue }) => {
    try {
      const response = await api.post('/streaming/chat_with_attachments', { attachments, chatId, message, reasoning});
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data);
    }
  }
);

const listSlice = createSlice({
  name: 'list',
  initialState: {
    list: [],
    activeChat: null,
    isStreamingPending: false,
  },
  reducers: {
    addMessage(state, action) {
      const { chat_id, ...message } = action.payload;
      console.log(action.payload);
      if (state.activeChat && state.activeChat.id === chat_id) {
        state.activeChat.messages.push(message);
      }
    }
  },
  extraReducers: (builder) => {
    builder
      // Обработка состояния загрузки
      .addCase(getAllChats.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      // Обработка успешного выполнения
      .addCase(getAllChats.fulfilled, (state, action) => {
        state.loading = false;
        state.list = action.payload.list;
      })
      // Обработка ошибки
      .addCase(getAllChats.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(createChat.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      // Обработка успешного выполнения
      .addCase(createChat.fulfilled, (state, action) => {
        state.loading = false;
        state.list.push(action.payload);
        state.activeChat = action.payload;
      })
      // Обработка ошибки
      .addCase(createChat.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(deleteChat.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      // Обработка успешного выполнения
      .addCase(deleteChat.fulfilled, (state, action) => {
        state.loading = false;
        state.list = state.list.filter((item) => item.id !== action.payload);
      })
      // Обработка ошибки
      .addCase(deleteChat.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(postCategory.pending, (state,action) => {
        const currentChat = state.list.find((item) => item.id === action.payload.chat_id);
        currentChat.messages[currentChat.messages.length-1].category = action.payload.category;
        state.list = state.list.map((item) => item.id === action.payload.chat_id ? currentChat : item);
      })
      .addCase(postCategory.fulfilled, (state, action) => {
        state.loading = false;
      })
      .addCase(getCurrentChat.fulfilled, (state, action) => {
        state.loading = false;
        state.activeChat = action.payload.chat;
      })      
      .addCase(streamingChat.fulfilled, (state, action) => {
        const { chat_id, ...message } = action.payload;
        if (state.activeChat) {
          state.activeChat.messages.push(message);
        }
        state.isStreamingPending = false;
      })
      .addCase(streamingChat.pending, (state) => {
        state.isStreamingPending = true;
      })
      .addCase(attachStreaming.fulfilled, (state, action) => {
        const { chat_id, ...message } = action.payload;
        if (state.activeChat) {
          state.activeChat.messages.push(message);
        }
        state.isStreamingPending = false;
      })
      .addCase(attachStreaming.pending, (state) => {
        state.isStreamingPending = true;
      })
  }
});

export const {addMessage} = listSlice.actions;
export default listSlice.reducer;