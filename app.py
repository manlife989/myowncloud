from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify,send_from_directory
import mysql.connector
from flask_bcrypt import Bcrypt
import os
from flask_mail import Mail, Message
import secrets

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management
bcrypt = Bcrypt(app)

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "gillrao43@gmail.com"  # Replace with your email
app.config["MAIL_PASSWORD"] = "gbam ejne qrmd yxfv"  # Replace with your password
app.config["MAIL_DEFAULT_SENDER"] = "your-email@gmail.com"

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

@app.route("/send_verification", methods=["POST"])
def send_verification():
    email = request.form.get("email")

    if not email:
        flash("Please enter a valid email!", "error")
        return redirect(url_for("home"))

    # Generate a unique verification token
    token = secrets.token_urlsafe(16)
    verification_tokens[token] = email

    # Create the verification link
    verification_link = url_for("verify", token=token, _external=True)

    # Send verification email
    subject = "Verify Your Email"
    message_body = f"Click the link to verify your email: {verification_link}"

    try:
        msg = Message(subject, recipients=[email], body=message_body)
        mail.send(msg)
        return render_template("verify.html", email=email)  # Show verification page
    except Exception as e:
        return f"Error sending email: {e}"

@app.route("/verify/<token>")
def verify(token):
    email = verification_tokens.get(token)
    if email:
        del verification_tokens[token]  # Remove token (user is verified)
        flash("Email verified successfully!", "success")
        
        return redirect(url_for("dashboard"))
    else:
        flash("Invalid or expired token!", "error")
        return redirect(url_for("home"))

# Signup Route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Insert user into the database
        try:
            cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
                           (username, email, hashed_password))
            db.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('dashboard', view="public"))
        except mysql.connector.Error as err:
            flash("Error: " + str(err), "danger")
    
    return render_template('signup.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Fetch user data
        cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user[1], password):
            session['user_id'] = user[0]  # Store user ID in session
            #flash("Login successful!", "success")
            return redirect(url_for('dashboard',view='public'))
        else:
            flash("Invalid username or password", "danger")
    
    return render_template('login.html')

# Dashboard Route
@app.route('/dashboard')
def dashboard():
    view = request.args.get('view', 'public')  # Default to 'public'

    if view == 'public':
        files = os.listdir(PUBLIC_CLOUD_FOLDER)
    else:
        user_folder = os.path.join(PRIVATE_CLOUD_FOLDER, str(session.get('user_id')))
        if os.path.exists(user_folder):
            files = os.listdir(user_folder)
        else:
            files = []

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
