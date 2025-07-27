# The Team - An Interactive Social Media Platform

This is a full-stack web application project developed using the Python Flask framework. It simulates a simple social media platform where users can share posts containing images or videos and interact with other users.

## Key Features

-   **User Authentication:** A complete system for user registration, login, and logout.
-   **Post Management:**
    -   Create new posts with image (`.jpg`, `.png`) or video (`.mp4`) uploads.
    -   Browse all public posts in a card-based layout on the main feed.
    -   View and manage your own posts on a dedicated "My Posts" page.
-   **Interaction System:**
    -   Post comments under each post.
    -   View all comments in real-time.
-   **Responsive Design (RWD):** Built with Bootstrap 5 to ensure a great viewing experience on desktops, tablets, and mobile devices.
-   **Personalization & UX:**
    -   Users can manage their own profile information.
    -   The homepage features a carousel with randomly selected posts for dynamic content discovery.
    -   Flash messages provide instant feedback for user actions.
-   **Security & Validation:**
    -   Validates uploaded files based on type, size, and video duration.
    -   Uses `uuid` to generate unique filenames for all uploads to prevent conflicts.


## Tech Stack
-   **Backend:**
    -   Python 3
    -   Flask
    -   SQLite 3
-   **Frontend:**
    -   HTML5
    -   CSS3
    -   Bootstrap 5
-   **Core Python Libraries:**
    -   `Flask`: The core web framework.
    -   `moviepy`: Used for server-side video processing to validate duration.
    -   `pytz`: Used for handling timezone conversions (UTC to HKT).
    -   `uuid`: Used for generating unique identifiers for filenames.

## Setup and Installation

Follow these steps to run the project on your local machine.

**1. Clone the Repository**
   git clone <https://github.com/czmyu03160/The_team_Project.git>
   cd The_team_Project

**2. Create and Activate a Virtual Environment**
# For Windows
python -m venv venv
.\venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

**3. Install Dependencies**
pip install Flask moviepy==1.0.3 pytz

**4. Initialize the Database**
If you have an init_db.py script, run it to create the database tables.
python init_db.py
(If this file doesn't exist, Flask may create database.db on the first request based on your models.)

**5. Run the Application**
flask run
Or, if your file is configured to run directly:
python app.py
The application will be available at http://127.0.0.1:5000.

**Contributors** <br>
* Yu Tang Hing <br>
* Sze Chi Keung
