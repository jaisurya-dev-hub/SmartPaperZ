# 📚 SmartPaperZ

### Your Next Exam Starts Here.

**SmartPaperZ** is a question-paper sharing platform designed for school students, college students, and government exam aspirants. It helps users discover, view, download, and share previous-year question papers in one place.

The goal is to make exam preparation easier by bringing college examination papers and competitive examination resources together on a single platform.

---

## ✨ Features

- 🔍 **Smart Search** — Find question papers by title, subject, year, college, or examination.
- 🎓 **Search by College** — Discover college-level question papers and browse available academic resources.
- 🏛️ **Search by Government Exam** — Explore examinations such as TNPSC Group 4, UPSC, SSC, banking, and railway exams.
- 📄 **PDF Viewing & Downloading** — Access available question papers conveniently.
- 🔗 **Shareable Paper Links** — Share individual paper pages with friends and fellow aspirants.
- 👤 **User Authentication** — Register and log in to access account-specific features.
- 🛡️ **Admin Dashboard** — Manage question papers, colleges, exams, and user submissions.
- 📤 **Paper Submission** — Submit question papers and relevant source links where supported.
- 🗄️ **Database Management** — Store paper metadata and application data using SQLite.
- 📱 **Responsive Interface** — Designed to work across desktop and mobile screens.

> **Content availability:** The government-exam directory contains exam listings, but previous-year papers must be added separately. The project does not include preloaded official question papers.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| HTML5 | Page structure |
| CSS3 | Styling and responsive design |
| JavaScript | Frontend interactions |
| Python | Backend application |
| Flask | Web framework |
| SQLite | Database |
| Jinja2 | Dynamic HTML templates |
| Pytest | Automated testing |

## 🚀 Getting Started

### Prerequisites

Install the following before running the project:

- Python 3.10 or newer
- Git
- Visual Studio Code (recommended)

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/SmartPaperZ.git
cd SmartPaperZ
```

Replace `YOUR-USERNAME` with your GitHub username.

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create your local environment file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and configure a strong, private `SECRET_KEY` using the format already provided in the example file.

Set the same secret in your current PowerShell session:

```powershell
$env:SECRET_KEY="your-generated-secret-key"
```

**Security:** Never commit `.env` or expose your secret key publicly.

### 5. Initialize the database

```powershell
python init_db.py
```

### 6. Create an administrator account

```powershell
flask --app app create-admin
```

Follow the prompts to configure your administrator account.

### 7. Run the application

```powershell
python app.py
```

Open the following URLs in your browser:

- **Website:** http://127.0.0.1:5000
- **Admin Login:** http://127.0.0.1:5000/admin/login

Keep the terminal open while the application is running.

## 🧪 Running Tests

Run the automated test suite with:

```powershell
python -m pytest -q
```

Review the output to confirm which tests pass or fail.

## 📄 Adding Question Papers

To add the first TNPSC Group 4 question paper:

1. Start the application and log in as an administrator.
2. Open the paper submission interface.
3. Select the `Competitive Exam` category.
4. Choose `TNPSC Group 4`.
5. Enter the examination year, subject, and language.
6. Upload a PDF or provide an official source URL, as supported by the application.
7. Save the paper and verify that it appears in the appropriate listing.

Use authentic, verified examination papers and respect applicable copyright and distribution restrictions.

## 📁 Project Structure

```text
SmartPaperZ/
├── app.py
├── config.py
├── db.py
├── init_db.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── templates/
│   ├── base.html
│   └── ...
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── uploads/
└── tests/
```

*The exact files and folders may vary slightly depending on the project version.*

## 🔐 Security & Deployment Notes

- Store secret keys in environment variables.
- Never upload passwords, `.env` files, or private user data to GitHub.
- Use secure session settings and HTTPS in production.
- Configure persistent storage or a suitable managed database before hosting user accounts and uploaded papers.
- Test administrator permissions and upload validation before making the platform publicly available.
- Configure a production WSGI server when deploying the Flask application.

## 🗺️ Future Enhancements

- Advanced filters for courses, semesters, subjects, and examination years.
- Verified answer keys and solutions.
- Bookmarking and personalized paper collections.
- More colleges and universities across India.
- Expanded state and national competitive-exam coverage.
- Improved PDF preview and accessibility.
- Persistent cloud storage for uploaded papers.
- A richer dashboard for students and administrators.

## 🎯 Project Objective

SmartPaperZ aims to make previous-year question papers easier to discover and share, helping students and government-exam aspirants organize their preparation resources in one place.

## 👨‍💻 Author

**MJS**

*Built with the goal of making exam preparation resources more accessible to students.*

---

⭐ **If you find this project useful, consider starring the repository!**
