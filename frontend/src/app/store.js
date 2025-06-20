import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/User';
import chatReducer from './slices/Chat';
import layoutReducer from './slices/Layout';
import listReducer from "./slices/List";

export const store = configureStore({
  reducer: {
    auth: authReducer,
    chat: chatReducer,
    layout: layoutReducer,
    list: listReducer
  },
});