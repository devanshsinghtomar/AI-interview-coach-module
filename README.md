# 🤖 AI Interview Coach Module

An advanced web-based platform for interview preparation powered by AI. Get personalized interview questions, real-time feedback, resume analysis, and comprehensive performance tracking.

## ✨ Features

### 🎤 Mock Interview
- **AI-Generated Questions**: Intelligent questions based on job role and experience level
- **Real-time Evaluation**: Get instant feedback on your answers
- **STAR Method Guidance**: Structured approach to answer behavioral questions
- **Performance Scoring**: 0-100 scale with detailed metrics

### 📄 Resume Analysis
- **AI-Powered Review**: Comprehensive resume evaluation
- **Strengths & Weaknesses**: Detailed breakdown of your resume
- **Actionable Recommendations**: Specific suggestions for improvement
- **Scoring System**: Overall resume score with improvements

### 📊 Performance Tracking
- **Interview History**: View all past interviews
- **Progress Analytics**: Track improvement over time
- **Performance Metrics**: Communication, Relevance, Confidence scores
- **Detailed Reports**: Download PDF reports of your evaluations

### 🧠 Skill Assessment
- **Technical Tests**: Evaluate technical knowledge
- **Domain-Specific Tests**: Role-based assessments
- **Performance Insights**: Identify weak areas

### 👤 User Account Management
- **Secure Registration & Login**: User authentication
- **Session Management**: Persistent user sessions
- **Account Security**: Password-protected profiles
- **Profile Data**: Personal performance dashboard

## 🚀 Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite3
- **Frontend**: HTML5, CSS3, JavaScript
- **AI Integration**: Google Generative AI
- **PDF Generation**: ReportLab, fpdf
- **File Processing**: PyPDF2, Pillow

## 📋 Requirements

- Python 3.8+
- Flask 3.1.0
- google-generativeai 0.8.5
- PyPDF2 3.0.1
- reportlab
- Other dependencies in requirements.txt

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/devanshsinghtomar/AI-interview-coach-module.git
cd AI-interview-coach-module

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SECRET_KEY="your-secret-key"
export GOOGLE_API_KEY="your-google-api-key"

# Run the application
python app.py
```

## 🌐 Deployment

### Heroku
```bash
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Set environment variables
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set GOOGLE_API_KEY="your-google-api-key"

# Deploy
git push heroku main
```

## 📖 Usage

1. **Register** - Create a new account
2. **Login** - Access your dashboard
3. **Start Interview** - Choose role and difficulty level
4. **Answer Questions** - Practice your responses
5. **Get Feedback** - Review detailed evaluation
6. **Analyze Resume** - Upload and optimize your resume
7. **Track Progress** - Monitor your improvement

## 🎯 Supported Roles

- Python Developer
- Java Developer
- JavaScript Developer
- Data Scientist
- Full Stack Developer
- DevOps Engineer

## 📊 Performance Metrics

- **Communication Level**: How well you articulate your thoughts
- **Relevance**: How relevant your answer is to the question
- **Confidence**: Overall confidence shown in your response
- **Overall Score**: 0-100 rating

## 🔧 Configuration

Edit `.env` file or environment variables:
```
SECRET_KEY=your-secret-key
GOOGLE_API_KEY=your-google-generativeai-key
DATABASE_URL=sqlite:///interview.db
PORT=5000
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🙋 Support

For issues, questions, or suggestions, please open an issue on GitHub.

## 🎓 Learning Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Google Generative AI](https://ai.google.dev/)
- [Interview Preparation Guide](https://www.interviewbit.com/)

## 🚀 Future Enhancements

- [ ] Video recording and playback
- [ ] Speech-to-text integration
- [ ] Peer comparison analytics
- [ ] Interview scheduling with mentors
- [ ] Advanced analytics dashboard
- [ ] Mobile app (React Native)
- [ ] Multi-language support

---

**Made with ❤️ for Interview Preparation**

Last Updated: 2026-06-06