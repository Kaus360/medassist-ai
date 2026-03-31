import { ThemeProvider } from './context/ThemeContext';
import { ChatProvider } from './context/ChatContext';
import { AppSidebar } from './components/AppSidebar';
import { ChatWindow } from './components/ChatWindow';
import './index.css';

export default function App() {
  return (
    <ThemeProvider>
      <ChatProvider>
        <div className="app-layout">
          <AppSidebar />
          <ChatWindow />
        </div>
      </ChatProvider>
    </ThemeProvider>
  );
}
