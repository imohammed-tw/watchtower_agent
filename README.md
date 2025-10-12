# AI Watchtower - Multi-Agent Newsletter Generation System

A sophisticated AI-powered newsletter generation system that monitors AI-related content, analyzes risks, and creates personalized newsletters with multi-agent orchestration.

## 🚀 Features

- **Multi-Agent Architecture**: Specialized agents for content analysis, risk assessment, and newsletter generation
- **Real-time Monitoring**: Continuous monitoring of AI news sources and content
- **Risk Assessment**: Advanced risk analysis and alert system
- **Personalized Newsletters**: Customizable newsletter generation (daily, weekly, monthly)
- **Modern Web Interface**: React-based frontend with responsive design
- **Export Functionality**: HTML export for newsletters
- **User Management**: Authentication and preference management
- **Dashboard Analytics**: Comprehensive metrics and insights

## 🏗️ Architecture

```
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── agents/         # AI agents (orchestrator, analysis, content, newsletter)
│   │   ├── api/           # REST API endpoints
│   │   ├── tools/         # External service clients (OpenAI, Perplexity)
│   │   ├── utils/         # Utility functions
│   │   └── templates/     # Newsletter templates
│   └── requirements.txt
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Application pages
│   │   └── services/      # API service layer
│   └── package.json
└── README.md
```

## 📋 Prerequisites

### System Requirements
- **Python 3.8+** (recommended: Python 3.11+)
- **Node.js 18+** (recommended: Node.js 20+)
- **Git**

### API Keys Required
- **OpenAI API Key**: For content analysis and generation
- **Perplexity API Key**: For enhanced content research

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/imohammed-tw/watchtower_agent.git
cd watchtower_agent
```

### 2. Backend Setup

#### Create Virtual Environment
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Environment Configuration
Create a `.env` file in the `backend/` directory:
```env
# API Keys (Required)
OPENAI_API_KEY=your_openai_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Security (Change in production)
SECRET_KEY=your-secret-key-change-this

# Database (Optional - defaults to SQLite)
DATABASE_URL=sqlite+aiosqlite:///./ai_watchtower_new.db

# Server Configuration (Optional)
HOST=127.0.0.1
PORT=8000
DEBUG=true

# Timezone (Optional - defaults to Asia/Kolkata)
TIMEZONE=Asia/Kolkata
```

### 3. Frontend Setup

#### Navigate to Frontend Directory
```bash
cd ../frontend
```

#### Install Dependencies
```bash
npm install
```

## 🚀 Running the Application

### Backend Server
```bash
# From backend/ directory
cd backend
uvicorn app.main:app --reload 
```

The backend will start on `http://localhost:8000`

**Available Endpoints:**
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`
- Dashboard API: `http://localhost:8000/api/v1/dashboard`
- Newsletter API: `http://localhost:8000/api/v1/newsletter`

### Frontend Development Server
```bash
# From frontend/ directory
cd frontend
npm run dev
```

The frontend will start on `http://localhost:5173`

### Production Build
```bash
# Build frontend for production
cd frontend
npm run build

# Preview production build
npm run preview
```

## 🔧 Configuration

### Backend Configuration
The main configuration is in `backend/app/config.py`. Key settings:

- **API Keys**: Set your OpenAI and Perplexity API keys
- **Database**: SQLite by default (easily configurable for PostgreSQL/MySQL)
- **Timezone**: Configure for your region
- **Agent Settings**: Customize analysis batch sizes and content limits

### Frontend Configuration
- **API Base URL**: Configured in `frontend/src/services/api.js`
- **Theme**: Customizable with Tailwind CSS
- **Components**: Modular UI components in `frontend/src/components/`

## 📊 API Documentation

### Core Endpoints

#### Newsletter Management
- `GET /api/v1/newsletter/` - List newsletters
- `POST /api/v1/newsletter/generate` - Generate new newsletter
- `GET /api/v1/newsletter/{id}` - Get specific newsletter

#### Dashboard
- `GET /api/v1/dashboard/metrics` - Get system metrics
- `GET /api/v1/dashboard/alerts` - Get risk alerts
- `GET /api/v1/dashboard/analytics` - Get analytics data

#### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/auth/me` - Get current user

#### Export
- `GET /api/v1/export/newsletter/{id}` - Export newsletter as HTML

## 🤖 AI Agents

### Orchestrator Agent
- Coordinates all other agents
- Manages workflow and scheduling
- Handles error recovery

### Analysis Agent
- Analyzes content for risks and trends
- Performs sentiment analysis
- Identifies key themes

### Content Agent
- Fetches and processes content from sources
- Handles content filtering and validation
- Manages content caching

### Newsletter Agent
- Generates newsletter content
- Applies user preferences
- Handles formatting and styling

## 🗄️ Database

### Default: SQLite
- File-based database for easy setup
- Automatic initialization
- No additional configuration required

### Production: PostgreSQL/MySQL
Update `DATABASE_URL` in your `.env` file:
```env
DATABASE_URL=postgresql://user:password@localhost/watchtower
```

## 🔒 Security

### API Keys
- Store API keys in `.env` file (never commit to version control)
- Use environment variables in production
- Rotate keys regularly

### Authentication
- JWT-based authentication
- Password hashing with bcrypt
- Session management

### CORS
- Configured for development and production
- Whitelist specific origins in production

## 📈 Monitoring & Analytics

### Health Checks
- `/health` endpoint for system status
- Component-level health monitoring
- Database connectivity checks

### Metrics
- Newsletter generation statistics
- Agent performance metrics
- User engagement analytics

### Alerts
- Risk threshold monitoring
- System health alerts
- Performance degradation warnings

## 🚀 Deployment

### Development
```bash
# Backend
cd backend
uvicorn app.main:app --reload

# Frontend
cd frontend
npm run dev
```

### Production
```bash
# Build frontend
cd frontend
npm run build

# Run backend with production settings
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker (Optional)
```dockerfile
# Dockerfile for backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🧪 Testing

### Backend Testing
```bash
cd backend
python -m pytest tests/
```

### Frontend Testing
```bash
cd frontend
npm test
```

## 📝 Development

### Code Structure
- **Backend**: FastAPI with async/await patterns
- **Frontend**: React with modern hooks
- **Database**: SQLAlchemy ORM
- **Styling**: Tailwind CSS with custom components

### Adding New Features
1. Create new API endpoints in `backend/app/api/`
2. Add corresponding frontend components
3. Update database models if needed
4. Add tests for new functionality

## 🐛 Troubleshooting

### Common Issues

#### Backend Issues
- **Database Connection**: Check SQLite file permissions
- **API Keys**: Verify keys are set in `.env`
- **Port Conflicts**: Change port in config if 8000 is occupied

#### Frontend Issues
- **Build Errors**: Clear `node_modules` and reinstall
- **API Connection**: Check backend is running and CORS settings
- **Styling Issues**: Verify Tailwind CSS is properly configured

### Debug Mode
Enable debug mode in `.env`:
```env
DEBUG=true
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the troubleshooting section
- Review API documentation at `/docs`
- Open an issue on GitHub

---

**Happy Coding! 🚀**