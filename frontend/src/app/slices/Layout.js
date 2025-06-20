import {createSlice} from '@reduxjs/toolkit';

const initialState = {
    overlay: false
};

const layoutSlice = createSlice({
  name: 'layout',
  initialState,
  reducers: {
    toogleOverlay: (state) => {
      state.overlay = !state.overlay
    },
  },
});

export const { toogleOverlay } = layoutSlice.actions;

export default layoutSlice.reducer;
