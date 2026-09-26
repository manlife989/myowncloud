from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify,send_from_directory,make_response
import mysql.connector
from flask_bcrypt import Bcrypt
import os
from dotenv import load_dotenv
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import secrets

load_doenv()
s = URLSafeTimedSerializer("your_secret_key")
app = Flask(__name__)
app.secret_key = 'your_secret_key' 
bcrypt = Bcrypt(app)

app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

mail = Mail(app)

verification_tokens = {}

PUBLIC_CLOUD_FOLDER = os.path.join(os.getcwd(), "/home/killer1400/uploads") # accessing the public folder
PRIVATE_CLOUD_FOLDER=os.path.join(os.getcwd(), "/home/killer1400/p_uploads") #private cloud
@app.route('/get_public_files')
def get_public_files():
    try:
        # Get list of files in public_cloud directory
        if os.path.exists(PUBLIC_CLOUD_FOLDER):
            files = os.listdir(PUBLIC_CLOUD_FOLDER)
        else:
            files = []

        return jsonify({"files": files})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Configure MySQL
db = mysql.connector.connect(
    host="localhost",
    user="clouduser",
    password="Strong@123",
    database="localcloud"
)
cursor = db.cursor()

# Home Route
@app.route('/')
def home():
    return render_template('index.html')

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Signup Route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Hash password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            flash("Email already registered!", "danger")
            return redirect(url_for('signup'))

        # Generate verification token
        token = s.dumps(email, salt='email-confirm')

        # Send verification email
        verification_link = url_for('verify_email', token=token, _external=True)
        msg = Message("Verify Your Email", sender="gillrao43@gmail.com", recipients=[email])
        msg.body = f"Click the link to verify your email: {verification_link}"
        mail.send(msg)
        email = request.form.get("email")
        print(f"Received email: {email}")  # Debugging statement


        # Store user in a temporary table
        cursor.execute("INSERT INTO pending_users (username, email, password) VALUES (%s, %s, %s)", 
                       (username, email, hashed_password))
        db.commit()

        flash("A verification email has been sent. Please check your inbox.", "info")
        return redirect(url_for('verify_email', token=token))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login and session management."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Fetch user data
        cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user[1], password):
            session['user_id'] = user[0]  # Store user ID in session
            session['username'] = username  # Also store username for better tracking
            return redirect(url_for('dashboard', view='public'))
        else:
            flash("Invalid username or password", "danger")
    
    return render_template('login.html')

@app.route('/verify_email/<token>')
def verify_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)  # Token expires in 1 hour

        # Retrieve user from pending_users
        cursor.execute("SELECT * FROM pending_users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            flash("Invalid or expired token!", "danger")
            return redirect(url_for('signup'))

        username, email, password = user[:3]
        session['user_id'] = user.id  
        # Move user to the main users table
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
                       (username, email, password))
        cursor.execute("DELETE FROM pending_users WHERE email = %s", (email,))
        db.commit()

        flash("Email verified! Logging you in.", "success")
        return redirect(url_for('dashboard', view="public"))

    except:
        flash("Verification link is invalid or expired.", "danger")
        return redirect(url_for('signup'))


# Login Route

@app.route('/dashboard')
def dashboard():
    """Dashboard route handling public and private files."""
    if 'user_id' not in session:
        flash("You need to log in first.", "danger")
        return redirect(url_for('home'))
    view = request.args.get('view', 'public')  # Default to 'public'
    
    if view == 'public':
        files = os.listdir(PUBLIC_CLOUD_FOLDER)
    elif view == 'private' and 'user_id' in session:
        user_folder = os.path.join(PRIVATE_CLOUD_FOLDER, str(session['user_id']))
        files = os.listdir(user_folder) if os.path.exists(user_folder) else []
    else:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('dashboard', view='public'))

    return render_template('dashboard.html', files=files, view=view)



@app.route('/public_cloud/<filename>')
def get_file(filename):
    """Serve files from the public_cloud folder"""
    return send_from_directory(PUBLIC_CLOUD_FOLDER, filename)

# Function to return the appropriate icon path
def get_icon(filename):
    ext = filename.split('.')[-1].lower()
    if ext in ['jpg', 'jpeg', 'png', 'gif']:
        return f"/public_cloud/{filename}"  # Display the actual image
    elif ext in ['mp4', 'mkv', 'avi']:
        return "/static/video_icon.png"  # Icon for video files
    elif ext in ['pdf']:
        return "/static/pdf_icon.png"  # Icon for PDFs
    else:
        return "/static/file_icon.png"  # Default icon

# Make the function available inside Jinja templates
app.jinja_env.globals.update(get_icon=get_icon)

#route to upload page
@app.route("/upload")
def upload_page():
    return render_template("upload.html")

#route for public_upload
@app.route("/upload_public", methods=["POST"])
def upload_public():
    if "file" not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"message": "No selected file"}), 400

    file.save(os.path.join(PUBLIC_CLOUD_FOLDER, file.filename))
    return jsonify({"message": "File uploaded successfully!"})

@app.route('/logout')
def logout():
    session.clear()  # Clears all session data
    return redirect(url_for('home'))

@app.route('/upload_private', methods=['POST'])
def upload_private():
    if 'user_id' not in session:
        flash("You must be logged in to upload files.")
        return redirect(url_for('login'))  # Redirect if the user is not logged in

    user_id = str(session.get('user_id'))  # Convert user ID to string
    user_folder = os.path.join(PRIVATE_CLOUD_FOLDER, user_id)

    # Ensure the user folder exists
    os.makedirs(user_folder, exist_ok=True)

    # Get the uploaded file
    file = request.files.get('file')

    if not file:
        flash("No file selected.")
        return redirect(url_for('upload'))  # Redirect back to the upload page

    file_path = os.path.join(user_folder, file.filename)
    file.save(file_path)  # Save the file

    return jsonify({"message": "File uploaded successfully!"})

    # flash("File uploaded successfully!")
    # return redirect(url_for('dashboard', view='private'))  # Redirect to private view

#showing the private stuff of the user
@app.route('/private_cloud/<filename>')
def get_private_file(filename):
    user_id = session.get("user_id")
    if not user_id:
        flash("You must be logged in to access private files.", "error")
        return redirect(url_for("login"))

    user_private_folder = os.path.join(PRIVATE_CLOUD_FOLDER, str(user_id))
    
    if not os.path.exists(os.path.join(user_private_folder, filename)):
        flash("File not found or unauthorized access!", "error")
        return redirect(url_for("dashboard",view='private'))

    return send_from_directory(user_private_folder, filename)

# Logout Route
# @app.route('/logout')
# def logout():
#     session.pop('user_id', None)
#     flash("Logged out successfully", "info")
#     return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
