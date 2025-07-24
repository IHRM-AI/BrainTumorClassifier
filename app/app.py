import streamlit as st
import torch
from torchvision import models, transforms
from PIL import Image
import os
import json

# --- Set Background ---
def set_bg(image_path):
    with open(image_path, "rb") as image_file:
        import base64
        encoded = base64.b64encode(image_file.read()).decode()
    page_bg_img = f"""
    <style>
    .stApp {{
      background-image: url("data:image/jpg;base64,{encoded}");
      background-size: cover;
      background-repeat: no-repeat;
      background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

set_bg(os.path.join(os.path.dirname(__file__), "background.jpg"))

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

# --- User Auth Helpers ---
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def signup_form():
    st.title("Sign Up")
    username = st.text_input("Choose a username")
    password = st.text_input("Choose a password", type="password")
    if st.button("Sign Up"):
        users = load_users()
        if username in users:
            st.error("Username already exists!")
        elif username == "" or password == "":
            st.error("Username and password cannot be empty!")
        else:
            users[username] = password
            save_users(users)
            st.success("Account created! Please sign in.")
            st.session_state["show_signup"] = False

def login_form():
    st.title("Sign In")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Sign In"):
        users = load_users()
        if username in users and users[username] == password:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.success("Logged in!")
        else:
            st.error("Invalid credentials.")

# --- Model Loading ---
def load_model():
    model = models.resnet18(pretrained=False)
    num_ftrs = model.fc.in_features
    model.fc = torch.nn.Linear(num_ftrs, 4)
    model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../models/best_model.pth'))
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    model.eval()
    return model

@st.cache_resource
def get_model():
    return load_model()

class_names = ['glioma', 'meningioma', 'no_tumor', 'pituitary']

def preprocess_image(image):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5]*3, std=[0.5]*3)
    ])
    if image.mode != 'RGB':
        image = image.convert('RGB')
    return transform(image).unsqueeze(0)

def main_app():
    st.markdown(
    """
    <style>
    div[data-testid="stTextInput"] > div > input,
    div[data-testid="stTextArea"] > div > textarea,
    div[data-testid="stNumberInput"] > div > input {
        background: #00bfff !important;         /* Neon blue background */
        border: 2px solid #00fff7 !important;   /* Bright neon border */
        border-radius: 15px !important;
        color: #fff !important;                 /* White text */
        box-shadow: 0 0 15px #00eaff, 0 0 4px #00fff7 !important;
        padding: 0.75em !important;
        font-size: 1.1em !important;
        outline: none !important;
        transition: box-shadow 0.3s, border 0.3s;
    }
    div[data-testid="stTextInput"] > div > input:focus,
    div[data-testid="stTextArea"] > div > textarea:focus,
    div[data-testid="stNumberInput"] > div > input:focus {
        box-shadow: 0 0 25px #00ffff, 0 0 8px #00fff7 !important;
        border: 2.5px solid #00fff7 !important;
    }
    label {
        color: #fff !important;
        text-shadow: 0 0 5px #00bfff;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True
)
    st.markdown('<div class="big-font">MRI Tumor Classifier</div>', unsafe_allow_html=True)
    st.write(f"<span style='color:#fff;'>Welcome, <b>{st.session_state['username']}</b>!</span>", unsafe_allow_html=True)
    st.markdown('<div class="contrast-box">', unsafe_allow_html=True)
    name = st.text_input("Your Name")
    age = st.number_input("Age", min_value=0, max_value=120, step=1)
    phone = st.text_input("Phone Number")
    med_hist = st.text_area("Any Medical History?")
    st.markdown('</div>', unsafe_allow_html=True)

    if not name or not phone or not age:
        st.warning("Please fill in all personal details before uploading MRI.")
        return

    uploaded_file = st.file_uploader("Upload an MRI Image", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded MRI", use_container_width=True)
        input_tensor = preprocess_image(image)
        with torch.no_grad():
            outputs = get_model()(input_tensor)
            _, pred = torch.max(outputs, 1)
            result = class_names[pred.item()]
            st.markdown(
                f"<div style='background:#0078D7; color:white; border-radius:6px; padding:12px; margin-top:20px; text-align:center; font-size:24px;'>"
                f"<b>Prediction: {result.upper()}</b></div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='background:#222; color:#fff; border-radius:6px; padding:12px; margin-top:20px;'><b>Patient Info:</b><br>"
                f"Name: {name}<br>Age: {age}<br>Phone: {phone}<br>Medical History: {med_hist}</div>",
                unsafe_allow_html=True,
            )

# --- State Management ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'show_signup' not in st.session_state:
    st.session_state['show_signup'] = False

# --- UI Routing ---
if not st.session_state['logged_in']:
    if st.session_state['show_signup']:
        signup_form()
        if st.button("Already have an account? Sign In"):
            st.session_state['show_signup'] = False
    else:
        login_form()
        if st.button("Don't have an account? Sign Up"):
            st.session_state['show_signup'] = True
else:
    main_app()