# 📚 Library Catalog System

A proof-of-concept library catalog system with Azure SQL, Python Flask API, and HTML/CSS/JS frontend.

## Table of Contents
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Team Collaboration](#team-collaboration)
- [Setup Instructions](#setup-instructions)
- [Deployment to Azure](#deployment-to-azure)
- [API Endpoints](#api-endpoints)
- [Testing the System](#testing-the-system)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### Patron Features
- 🔍 Search Catalog - Search books by keyword or genre
- 📝 Sign Up - Get a library card with unique 8-digit number
- 👤 My Account - View currently checked out books and active reservations
- 📖 Reserve Books - Queue for unavailable books (FIFO)

### Librarian Features
- ➕ Add Books - Add new books to the catalog
- ❌ Remove Books - Remove books from the catalog
- ✅ Checkout Books - Check out books to patrons (with 4-week due date)
- 🔄 Process Returns - Return books and trigger reservation queue
- 📊 Full Catalog View - See who has checked out/reserved each book

### Automated Features
- ⏰ Daily Expiry Job - Releases reservations older than 3 days
- 🔄 Queue Promotion - Automatically promotes next patron in queue

---

## Technology Stack

| Component | Technology | Azure Service |
|-----------|------------|---------------|
| Database | Azure SQL | Azure SQL Database |
| Backend API | Python Flask | Azure App Service |
| Frontend | HTML/CSS/JavaScript | Azure Static Web Apps |
| Automation | Python | Azure Functions (Timer Trigger) |
| Version Control | Git | GitHub |
| Deployment | Azure CLI | Various |

---

## Setup Instructions

### Prerequisites

Before you begin, ensure you have:
- Python 3.9+ (https://www.python.org/downloads/)
- VS Code (https://code.visualstudio.com/download)
- Git (https://git-scm.com/downloads)
- Azure Subscription (https://azure.microsoft.com/free/)
- GitHub Account (https://github.com/)

### VS Code Extensions (Recommended)

Install these extensions for a better development experience:

code --install-extension ms-python.python
code --install-extension eamodio.gitlens
code --install-extension ms-vsliveshare.vsliveshare
code --install-extension ms-mssql.mssql
code --install-extension GitHub.vscode-pull-request-github
code --install-extension esbenp.prettier-vscode

### Local Development

#### 1. Clone the Repository

git clone https://github.com/YOUR_USERNAME/library-catalog-system.git
cd library-catalog-system

#### 2. Set Up Python Virtual Environment

python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

#### 3. Install Backend Dependencies

cd backend
pip install -r requirements.txt

#### 4. Configure Environment Variables

cp .env.example .env

Edit .env with your Azure SQL connection string:

SQL_CONNECTION_STRING=Driver={ODBC Driver 17 for SQL Server};Server=tcp:your-server.database.windows.net,1433;Database=your-database;Uid=your-username;Pwd=your-password;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1

#### 5. Run the Flask API

python app.py

You should see:
✓ Configuration loaded successfully
✓ Database connection successful
 * Serving Flask app 'app.py'
 * Debug mode: on
 * Running on http://127.0.0.1:5000 (Press CTRL+C to quit)

#### 6. Open the Frontend

Option A: Directly in Browser
- Navigate to frontend/index.html
- Double-click to open in your default browser

Option B: VS Code Live Server
- Install VS Code "Live Server" extension
- Right-click index.html → "Open with Live Server"

Option C: Python HTTP Server
cd frontend
python -m http.server 8000

Then open http://localhost:8000 in your browser

### Database Setup

#### 1. Create Azure SQL Database

az group create --name library-rg --location eastus

az sql server create \
  --name library-sql-server \
  --resource-group library-rg \
  --location eastus \
  --admin-user LibraryAdmin \
  --admin-password YourStrongPassword123!

az sql db create \
  --resource-group library-rg \
  --server library-sql-server \
  --name LibraryDB \
  --edition GeneralPurpose \
  --family Gen5 \
  --capacity 2

#### 2. Configure Firewall Rules

az sql server firewall-rule create \
  --resource-group library-rg \
  --server library-sql-server \
  --name AllowYourIP \
  --start-ip-address YOUR_IP_ADDRESS \
  --end-ip-address YOUR_IP_ADDRESS

az sql server firewall-rule create \
  --resource-group library-rg \
  --server library-sql-server \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

#### 3. Run Schema Scripts

Option A: Using Azure Data Studio
1. Download Azure Data Studio
2. Connect to your Azure SQL Server
3. Open database/schema.sql
4. Run the script (F5)

Option B: Using Python

Create database/init_db.py:

import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

conn = pyodbc.connect(os.getenv('SQL_CONNECTION_STRING'))
cursor = conn.cursor()

with open('schema.sql', 'r') as f:
    schema = f.read()

for statement in schema.split(';'):
    if statement.strip():
        cursor.execute(statement)
        conn.commit()

print("Database initialized successfully")
conn.close()

---

## Deployment to Azure

### Deploy Flask API to Azure App Service

#### 1. Create App Service

az appservice plan create \
  --name library-plan \
  --resource-group library-rg \
  --sku B1 \
  --is-linux

az webapp create \
  --name library-api \
  --resource-group library-rg \
  --plan library-plan \
  --runtime "PYTHON:3.9"

#### 2. Deploy Code

cd backend
zip -r ../library-api.zip .

az webapp deployment source config-zip \
  --resource-group library-rg \
  --name library-api \
  --src ../library-api.zip

#### 3. Set Environment Variables

az webapp config appsettings set \
  --resource-group library-rg \
  --name library-api \
  --settings \
    SQL_CONNECTION_STRING="YOUR_CONNECTION_STRING" \
    FLASK_ENV="production"

#### 4. Test the API

curl https://library-api.azurewebsites.net/api/health

Expected response:
{"message":"Library API is running","status":"healthy"}

### Deploy Azure Function (Timer Trigger)

#### 1. Create Function App

az storage account create \
  --name librarystorage \
  --resource-group library-rg \
  --location eastus \
  --sku Standard_LRS

az functionapp create \
  --resource-group library-rg \
  --name library-timer-function \
  --storage-account librarystorage \
  --runtime python \
  --runtime-version 3.9 \
  --functions-version 4 \
  --os-type Linux \
  --consumption-plan-location eastus

#### 2. Deploy Function

npm install -g azure-functions-core-tools@4

cd azure-function
func azure functionapp publish library-timer-function

#### 3. Set Environment Variables

az functionapp config appsettings set \
  --resource-group library-rg \
  --name library-timer-function \
  --settings SQL_CONNECTION_STRING="YOUR_CONNECTION_STRING"

### Deploy Frontend

#### Option A: Azure Static Web Apps

npm install -g @azure/static-web-apps-cli

swa deploy ./frontend \
  --app-name library-frontend \
  --resource-group library-rg \
  --env production

#### Option B: Azure Storage Static Website

az storage account create \
  --name libraryfrontend \
  --resource-group library-rg \
  --location eastus \
  --sku Standard_LRS \
  --kind StorageV2

az storage blob service-properties update \
  --account-name libraryfrontend \
  --static-website \
  --index-document index.html

az storage azcopy blob upload \
  --account-name libraryfrontend \
  --container \$web \
  --source ./frontend \
  --recursive

---

## API Endpoints

### Patron Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/books | Search books (genre, keyword) |
| POST | /api/patrons | Sign up for library card |
| GET | /api/patrons/{card}/account | View patron account |
| POST | /api/reservations | Make a reservation |

### Librarian Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/librarians/books | Add a book |
| DELETE | /api/librarians/books/{id} | Remove a book |
| POST | /api/librarians/checkout | Checkout a book |
| POST | /api/librarians/return | Process a return |
| GET | /api/librarians/catalog | View full catalog |

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/health | API health status |

---

## Testing the System

### Test Flow for Patrons

1. Search for books
   - Visit the frontend
   - Use search bar with keyword or genre filter

2. Reserve an unavailable book
   - Find an unavailable book
   - Click "Reserve" and enter your card number
   - Check your queue position

3. Sign up for a card
   - Go to "Sign Up" section
   - Fill in your details and choose an 8-digit card number

4. View your account
   - Enter your card number in "My Account"
   - See your checkouts and reservations

### Test Flow for Librarians

1. Add a book
   - Go to "Librarian Dashboard"
   - Fill in book details and add

2. Checkout a book
   - Enter Book ID, Patron Card, and Librarian ID
   - Click "Checkout"

3. Process a return
   - Enter Book ID and click "Return"

4. View full catalog
   - Click "Refresh Catalog" to see all books with patron info

### Manual Database Testing

-- Check all books
SELECT * FROM Books;

-- Check active reservations
SELECT * FROM Reservations WHERE is_active = 1;

-- Check active checkouts
SELECT * FROM Checkouts WHERE is_returned = 0;

-- Test stored procedures
EXEC sp_CheckoutBook 1, '02255327', 1, '';
EXEC sp_ReturnBook 1, '';
EXEC sp_ReleaseExpiredReservations;

---

## Project Structure

library-catalog-system/
├── backend/
│   ├── app.py                 # Flask API
│   ├── config.py              # Configuration
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Environment variables (not in repo)
├── frontend/
│   └── index.html             # Single page application
├── azure-function/
│   ├── __init__.py            # Timer trigger function
│   ├── function.json          # Function configuration
│   └── requirements.txt       # Function dependencies
├── database/
│   ├── schema.sql             # Database schema
│   └── sample-data.sql        # Sample inserts (optional)
├── .github/
│   ├── workflows/
│   │   └── ci.yml             # GitHub Actions CI
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── pull_request_template.md
├── .gitignore                 # Git ignore file
├── .env.example               # Environment template
└── README.md                  # This file

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed
Error: SQL_CONNECTION_STRING environment variable not set
Solution: Create .env file in backend/ with your connection string.

#### 2. Azure SQL Firewall Blocking
Cannot open server requested by the login. Client with IP address is not allowed.
Solution: Run the firewall rule command to add your IP.

#### 3. Flask Port Already in Use
OSError: [Errno 98] Address already in use
Solution: Change the port in app.py or kill the existing process.

#### 4. ODBC Driver Not Found
pyodbc.Error: Can't open lib 'ODBC Driver 17 for SQL Server'
Solution: Install ODBC Driver from Microsoft.

---

## Contributing

### Development Workflow

1. Pick an issue from the GitHub Issues
2. Create a feature branch from develop
3. Write code with proper comments
4. Run tests locally
5. Commit with conventional commit message
6. Push and open Pull Request
7. Address review feedback
8. Merge after approval

### Code Style Guidelines
- Python: Follow PEP 8 (use flake8 for linting)
- HTML: Use semantic HTML5 elements
- CSS: Use classes, not IDs for styling
- JavaScript: Use const and let, avoid var
- SQL: Use uppercase for keywords, lowercase for identifiers

### Testing
pip install pytest flake8
pytest tests/
flake8 backend/

---

## License

This project is licensed under the  GPL-3.0 License - see the LICENSE file for details.

---

---

## Contact

- Project Member #1: Melika Bagheri
- Email: [mbagheri@cpp.edu]
- GitHub: [@bagherim8650](https://github.com/bagherim8650)

---

## Status

- ✅ Database Schema Complete
- ✅ Sample Data Loaded
- ✅ Backend API Functional
- ✅ Frontend UI Basic
- ✅ Azure Function Setup
- 🚧 Testing In Progress
- 📝 Documentation In Progress

---

Last Updated: June 2026