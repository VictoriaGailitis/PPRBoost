import {createSlice, createAsyncThunk} from '@reduxjs/toolkit';

import axios from 'axios';
import { API_URL } from '../../shared/consts';

const getInitialState = () => {
  const token = localStorage.getItem('token');
  const userLogin = localStorage.getItem('userLogin');
  const model = localStorage.getItem('model');
  const systemPrompt = JSON.parse(localStorage.getItem('systemPrompt'));
  
  return {
    email: userLogin ? userLogin : '',
    access_token: token || null,
    model: model || 'gpt-3.5-turbo',
    systemPrompt: systemPrompt ||     {
      "id": 1,
      "name": "знаток личного кабинета",
      "text": "Ты — интеллектуальный ассистент, отвечающий на вопросы пользователей на основе базы знаний ППР."
  },
    isAuthenticated: !!token,
    loading: false,
    error: null,
    systemPrompts: null
  };
};

// Базовый URL 


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

export const loginUser = createAsyncThunk(
  'auth/login',
  async ({ email, password }, { rejectWithValue }) => {
    try {
      const response = await axios.post(`${API_URL}/login`, {
        email,
        password
      });

      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('userLogin', email);
      
      return {
        email: email,
        access_token: response.data.token
      };
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);
export const registerUser = createAsyncThunk(
  'auth/register',
  async ({ email, password }, { rejectWithValue }) => {
    try {
      const response = await axios.post(`${API_URL}/register`, {
        email,
        password
      });
      
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('userLogin', email);
      
      return {
        email: email,
        access_token: response.data.access_token
      };
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

export const getAllPromts = createAsyncThunk(
  'auth/getAllPromts',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get(`/system_prompts`);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

export const postSystemPrompt = createAsyncThunk(
  'auth/postSystemPrompt',
  async (system_prompt_id, { rejectWithValue }) => {
    try {
      const response = await api.post(`/system_prompt`, {system_prompt_id});
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);


const authSlice = createSlice({
  name: 'auth',
  initialState: getInitialState(),
  reducers: {
    updateSystemPrompt: (state, action) => {
      state.systemPrompt.id = action.payload.value;
      state.systemPrompt.name = action.payload.label;
      state.systemPrompt.text = action.payload.promptText;
      localStorage.setItem('systemPrompt', JSON.stringify(state.systemPrompt));
    },
  },
  extraReducers: (builder) => {
    builder
      // Обработка логина
      .addCase(loginUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.user = action.payload.email;
        state.access_token = action.payload.access_token;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      
      // Обработка регистрации
      .addCase(registerUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.email = action.payload.email;
        state.access_token = action.payload.access_token;
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(getAllPromts.fulfilled, (state, action) => {
        state.loading = false;
        state.systemPrompts = action.payload;
      })
  }
});

export const { setCredentials, logout,updateModel, updateSystemPrompt} = authSlice.actions;

export default authSlice.reducer;
