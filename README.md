# 💻 Axio - AI Code Assistant

**by Perfionix AI**

A beautiful, modern AI coding assistant with syntax highlighting, markdown rendering, and intelligent code conversations. Get help with programming, debugging, algorithms, and more!

![Axio](https://img.shields.io/badge/Axio-Code%20Assistant-blueviolet?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green?style=for-the-badge&logo=flask)
![Perfionix AI](https://img.shields.io/badge/Perfionix-AI-orange?style=for-the-badge)

## ✨ Features

### 💬 **Intelligent Code Chat**
- Real-time AI conversations powered by your local GPT server
- **Syntax highlighting** for all major programming languages
- **Markdown rendering** with beautiful formatting
- **Code block copy buttons** for easy code copying
- Inline code highlighting
- Conversation history management
- Streaming responses with typing indicators

### ✅ **Task Management**
- Create, complete, and delete tasks
- Priority levels (High, Medium, Low)
- Filter tasks by status
- Track completion statistics

### 📝 **Notes**
- Create and manage personal notes
- Beautiful card-based layout
- Quick access to all your notes
- Timestamps for tracking

### ⏰ **Reminders**
- Set time-based reminders
- Never forget important events
- Easy-to-manage reminder list

### 🎨 **Premium Design**
- Modern dark theme with vibrant gradients
- **Tokyo Night** syntax highlighting theme
- **JetBrains Mono** font for code
- Smooth animations and transitions
- Fully responsive layout
- Glassmorphism effects

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **Local GPT Server** running on `localhost:11434` (Ollama or similar)
3. **(Optional)** ElevenLabs API key for voice features

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd "c:\Users\progr\Desktop\personal  Assistant"
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   - Copy `.env.example` to `.env`
   - Update with your API keys (if using voice features)
   ```
   ELEVENLABS_API_KEY=your_key_here
   GPT_SERVER_URL=http://localhost:11434/api/chat
   GPT_MODEL=gpt-oss:120b-cloud
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Open your browser:**
   Navigate to `http://localhost:5000`

## 📁 Project Structure

```
personal Assistant/
├── app.py                 # Flask backend with API routes
├── requirements.txt       # Python dependencies
├── .env                   # Environment configuration
├── templates/
│   └── index.html        # Main HTML template
├── static/
│   ├── style.css         # Premium styling
│   └── script.js         # Interactive JavaScript
└── README.md             # This file
```

## 🎯 Usage

### Chat with Nova
1. Click on the **Chat** tab in the sidebar
2. Type your message in the input box
3. Press Enter or click the send button
4. Nova will respond with helpful information

### Manage Tasks
1. Navigate to the **Tasks** tab
2. Click **+ Add Task**
3. Enter task details and priority
4. Click tasks to mark as complete
5. Filter by All, Pending, or Completed

### Create Notes
1. Go to the **Notes** tab
2. Click **+ New Note**
3. Add a title and content
4. Your notes are saved automatically

### Set Reminders
1. Open the **Reminders** tab
2. Click **+ Add Reminder**
3. Enter reminder details and date/time
4. Never miss important events!

## 🔧 Configuration

### GPT Server Settings

The app connects to a local GPT server. Make sure you have:
- **Ollama** or similar GPT server running
- Model `gpt-oss:120b-cloud` available
- Server accessible at `http://localhost:11434`

### Voice Features (Optional)

To enable text-to-speech:
1. Get an ElevenLabs API key from https://elevenlabs.io
2. Add it to your `.env` file
3. Voice responses will be automatically enabled

## 🎨 Customization

### Change Theme Colors
Edit `static/style.css` and modify the CSS variables:
```css
:root {
    --primary: #667eea;
    --accent: #f5576c;
    /* ... more colors */
}
```

### Adjust AI Behavior
Modify the system prompt in `app.py`:
```python
conversation = [
    {
        "role": "system",
        "content": "Your custom instructions here..."
    }
]
```

## 🐛 Troubleshooting

### "Connection error" in chat
- Ensure your GPT server is running on `localhost:11434`
- Check the model name matches your server configuration
- Verify the server URL in `.env`

### Voice not working
- Check if `ELEVENLABS_API_KEY` is set in `.env`
- Verify your API key is valid
- Voice features are optional and won't affect other functionality

### Tasks/Notes not saving
- Check browser console for errors
- Ensure Flask server is running
- Data is stored in memory (will reset on server restart)

## 🚀 Future Enhancements

- [ ] Database integration for persistent storage
- [ ] User authentication and multi-user support
- [ ] Voice input (speech-to-text)
- [ ] Calendar integration
- [ ] Mobile app version
- [ ] Browser notifications for reminders
- [ ] Export/import data functionality
- [ ] Dark/Light theme toggle

## 📝 License

This project is open source and available for personal use.

## 🤝 Contributing

Feel free to fork, modify, and enhance this project!

## 💬 Support

For issues or questions, please check:
1. This README file
2. The troubleshooting section
3. Server logs in the terminal

---

**Built with ❤️ using Flask, JavaScript, and AI**

Enjoy your personal AI assistant! ✨
