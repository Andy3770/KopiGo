# KopiGo Flask App

KopiGo is a tourism-focused Flask web application that integrates SQL (MariaDB) and NoSQL (MongoDB Atlas) to help users discover nearby eateries around attractions, submit reviews with images, and manage itineraries.

## 📋 Requirements

- Python 3.x
- MariaDB Server (installed and running)
- MongoDB Atlas (NoSQL)
- AWS S3 Bucket (for image uploads)

### pip packages:
- flask, flask-sqlalchemy, pymysql, boto3, pillow, flask-bcrypt
- pandas, pymongo, requests

## 🚀 Setup Instructions (Recommended)

### For Mac/Linux users:

```bash
chmod +x setup_kopigo.sh
./setup_kopigo.sh
```

### For Windows users:

Double-click or run in Command Prompt:

```cmd
setup_kopigo.bat
```

Both scripts will:
1. Create a Python virtual environment
2. Install dependencies
3. Set up the MariaDB database
4. Import the SQL schema
5. Launch the Flask app

## 🔧 Manual Setup (Optional)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/KopiGo.git
cd KopiGo
```

### 2. Create a Virtual Environment & Activate It

```bash
python3 -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate.bat     # Windows
```

### 3. Install Dependencies

```bash
pip install flask flask-sqlalchemy pymysql boto3 pillow flask-bcrypt pandas pymongo requests
```

### 4. Create MariaDB Database

```bash
mysql -u root -p -e "CREATE DATABASE KopiGo;"
```

### 5. Import SQL Schema

```bash
mysql -u root -p KopiGo < schema.sql
```

## 🔑 Key Features

- 🔐 Secure sign-up & login using Flask-Bcrypt
- 🏪 Filter eateries by postal code, price, hygiene, etc.
- 📸 Upload review images to AWS S3
- 🗺️ Find nearby tourist attractions and eateries
- 📋 View & manage personal itineraries
- 📊 Admin analytics dashboard with review & search statistics
- ⚡ Full MySQL + MongoDB indexing & performance benchmarks

## 🛠️ Technologies Used

- **Backend**: Flask (Python)
- **Databases**: MariaDB (SQL), MongoDB Atlas (NoSQL)
- **Cloud Storage**: AWS S3
- **Authentication**: Flask-Bcrypt
- **Image Processing**: Pillow
- **Data Processing**: Pandas
- **HTTP Requests**: Requests library

## 📂 Project Structure

```
KopiGo/
├── app.py                 # Main Flask application
├── schema.sql            # Database schema
├── setup_kopigo.sh       # Mac/Linux setup script
├── setup_kopigo.bat      # Windows setup script
├── requirements.txt      # Python dependencies
├── static/              # Static files (CSS, JS, images)
├── templates/           # HTML templates
└── README.md           # This file
```

## 🏃‍♂️ Running the Application

1. Ensure MariaDB is running
2. Activate your virtual environment
3. Run the Flask app:
   ```bash
   python app.py
   ```
4. Open your browser and navigate to `http://localhost:5000`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

**Made with ❤️ for food lovers and travelers**