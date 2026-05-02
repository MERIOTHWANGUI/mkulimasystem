# Smart Farming Support System 🌱

A web-based decision support system that uses machine learning to recommend suitable crops based on environmental and soil conditions, with an integrated chatbot for user interaction and guidance.

---

## Problem
Farmers often rely on guesswork when selecting crops, which can lead to poor yields and inefficient use of resources due to mismatched environmental conditions.

---

## Solution
This system provides data-driven crop recommendations using a trained machine learning model and allows users to interact with the system through a simple web interface and chatbot.

---

## Features
- Crop recommendation using machine learning (Random Forest model)
- User input interface for environmental and soil parameters
- Chatbot to guide users and answer basic queries
- Backend processing and data handling
- Database integration for storing and retrieving system data

---

## System Architecture
- **Frontend:** HTML/CSS (Flask templates)
- **Backend:** Python (Flask)
- **Database:** SQLite (local) / PostgreSQL (deployment)
- **Machine Learning Model:** Random Forest (Scikit-learn)
- **Chatbot:** api connection with lanrge language model and use of knowledge fallbck

---

## Tech Stack
- Python
- Flask
- Scikit-learn
- SQLite / PostgreSQL
- HTML/CSS

---

## How It Works
1. User enters environmental data (e.g., soil type, rainfall, temperature)
2. Data is sent to the Flask backend
3. The trained Random Forest model processes the input
4. The system predicts the most suitable crop
5. Results are displayed to the user
6. Chatbot assists with answering and guiding farmers on best agricultural practices including advice when to plant

---
screen shot
landing page
<img width="1358" height="655" alt="image" src="https://github.com/user-attachments/assets/193ab849-b86d-4346-bc90-0701eb032f27" />
registering account
<img width="1271" height="636" alt="image" src="https://github.com/user-attachments/assets/a3d7b59e-f00d-4439-9e22-666dbdced9f0" />
recommending module
<img width="1361" height="645" alt="image" src="https://github.com/user-attachments/assets/d5512edc-9912-429b-b16b-448d0b63e040" />
<img width="1351" height="654" alt="image" src="https://github.com/user-attachments/assets/ee7f3548-a198-4c44-8aa3-16b3e27f98cb" />
<img width="1362" height="651" alt="image" src="https://github.com/user-attachments/assets/deb9a3c3-5d1a-4793-a5b8-4546fccd84d6" />
<img width="1356" height="649" alt="image" src="https://github.com/user-attachments/assets/0ad3583e-5992-4320-83b1-e2bb9436830f" />
 intelligent chatbot
 <img width="1141" height="633" alt="image" src="https://github.com/user-attachments/assets/db99c94d-e729-4fb7-9f5c-17967f3d03c7" />
<img width="1355" height="647" alt="image" src="https://github.com/user-attachments/assets/bf46fe7d-d6b0-456e-8a9a-63d4629ea909" />
marketplace module
<img width="1343" height="565" alt="image" src="https://github.com/user-attachments/assets/9f9b38d2-56ce-4be9-ba95-cf4f98068165" />
supplier module
<img width="1358" height="634" alt="image" src="https://github.com/user-attachments/assets/aefea63d-f353-424b-9dc9-c953551206b6" />
<img width="1366" height="640" alt="image" src="https://github.com/user-attachments/assets/38c42796-b184-4363-838b-48b5d82890e2" />
<img width="1366" height="564" alt="image" src="https://github.com/user-attachments/assets/5d966c5b-6dc2-48e2-94bd-02ad1c94d7af" />
<img width="1062" height="588" alt="image" src="https://github.com/user-attachments/assets/efdc06f6-f329-41a6-bb30-51356c89657a" />


## Installation

```bash
git clone https://github.com/yourusername/smart-farming-system.git
cd smart-farming-system
pip install -r requirements.txt
python app.py
