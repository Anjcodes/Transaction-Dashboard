import streamlit as st
import sqlite3
import hashlib
import app  # Import your app.py

# Function to connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect('users.db')
    return conn

# Create a connection and table if it doesn't exist
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        password_hash TEXT NOT NULL
    )
''')
conn.commit()
conn.close()

# Password hashing function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# User registration and authentication
def register_user(username, name, password):
    password_hash = hash_password(password)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, name, password_hash) VALUES (?, ?, ?)", 
                   (username, name, password_hash))
    conn.commit()
    conn.close()

def authenticate_user(username, password):
    password_hash = hash_password(password)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?", (username, password_hash))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def login():
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if authenticate_user(username, password):
            st.session_state['logged_in'] = True  # Set the login state
            st.session_state['username'] = username  # Store the username
        else:
            st.error("Invalid username or password.")

def sign_up():
    st.subheader("Sign Up")
    name = st.text_input("Full Name")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    
    if st.button("Create Account"):
        if password == confirm_password:
            try:
                register_user(username, name, password)
                st.success("Account created successfully! You can now log in.")
            except sqlite3.IntegrityError:
                st.error("Username already exists. Choose a different one.")
        else:
            st.error("Passwords do not match.")

def logout():
    # Clear the session state variables
    st.session_state.clear()  # This will clear all session state variables

def main():    
    # Check if the user is logged in
    if 'logged_in' in st.session_state and st.session_state['logged_in']:
        app.main()  # Call the main dashboard if logged in

        # Logout button
        if st.button("Logout"):
            logout()  # Call logout function

    else:
        st.title("Transaction Dashboard Login")
        choice = st.selectbox("Choose an option", ["Login", "Sign Up"])
        
        if choice == "Login":
            login()
        elif choice == "Sign Up":
            sign_up()

if __name__ == "__main__":
    main()
