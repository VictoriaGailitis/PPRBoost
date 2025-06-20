import { BrowserRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store';
import AppRouter from './routes';
import { ConfigProvider } from 'antd';

function App() {
  return (
    <Provider store={store}>
      <BrowserRouter>
        <ConfigProvider
          theme={{
            token: {
              colorPrimary: '#DB2B21',
              colorBgLayout: '#E7EEF7',
            },
          }}
        >
          <AppRouter />
        </ConfigProvider>
      </BrowserRouter>
    </Provider>
  );
}

export default App;