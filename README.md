# medTrialMatch-Backend

## Setup Instructions

Follow these steps to get the backend server running:

### 1. Clone the repository

```bash
git clone https://github.com/GarudaSeva/medTrialMatch-Backend.git
```

### 2. Navigate to the backend directory

```bash
cd backend
```

### 3. Create a virtual environment

```bash
python -m venv myenv
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the backend directory and add the following:

```env
MONGO_URI=mongodb://localhost:27017
DB_NAME=medTrialMatch
```

### 6. Run the server

```bash
python app.py
```

The server will be running at **localhost:5000**

