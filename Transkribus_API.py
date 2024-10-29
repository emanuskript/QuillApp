import tkinter as tk
from tkinter import filedialog, messagebox
import requests

BASE_URL = "http://127.0.0.1:5000"
session_id = None  # Initialize session ID variable

def login():
    global session_id
    username = username_entry.get()
    password = password_entry.get()

    response = requests.post(f"{BASE_URL}/login", json={"username": username, "password": password})
    if response.status_code == 200:
        session_id = response.json()["session_id"]  # Store session ID
        messagebox.showinfo("Success", "Login successful")
    else:
        messagebox.showerror("Error", "Login failed")

def list_collections():
    if not session_id:
        messagebox.showerror("Error", "You must be logged in to list collections.")
        return

    response = requests.get(f"{BASE_URL}/collections?session_id={session_id}")
    if response.status_code == 200:
        collections_text.delete(1.0, tk.END)
        collections = response.json()
        for coll in collections:
            collections_text.insert(tk.END, f"{coll['colId']} - {coll['colName']}\n")  # Updated keys
    else:
        messagebox.showerror("Error", "Failed to retrieve collections")

def upload_document():
    if not session_id:
        messagebox.showerror("Error", "You must be logged in to upload a document.")
        return

    collection_id = collection_id_entry.get()
    file_path = filedialog.askopenfilename()
    if not file_path:
        return

    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/collections/{collection_id}/upload?session_id={session_id}", files=files)
        if response.status_code == 200:
            messagebox.showinfo("Success", "Document uploaded")
        else:
            messagebox.showerror("Error", "Upload failed")

def start_ocr():
    if not session_id:
        messagebox.showerror("Error", "You must be logged in to start OCR.")
        return

    collection_id = collection_id_entry.get()
    doc_id = doc_id_entry.get()
    page_number = page_number_entry.get()

    response = requests.post(f"{BASE_URL}/collections/{collection_id}/{doc_id}/{page_number}/ocr?session_id={session_id}")
    if response.status_code == 200:
        job_id = response.json()["job_id"]
        messagebox.showinfo("Success", f"OCR started. Job ID: {job_id}")
    else:
        messagebox.showerror("Error", "OCR failed to start")

app = tk.Tk()
app.title("Transkribus OCR Interface")

tk.Label(app, text="Username").grid(row=0, column=0)
username_entry = tk.Entry(app)
username_entry.grid(row=0, column=1)

tk.Label(app, text="Password").grid(row=1, column=0)
password_entry = tk.Entry(app, show="*")
password_entry.grid(row=1, column=1)

tk.Button(app, text="Login", command=login).grid(row=2, column=0, columnspan=2)

tk.Button(app, text="List Collections", command=list_collections).grid(row=3, column=0, columnspan=2)
collections_text = tk.Text(app, height=10, width=50)
collections_text.grid(row=4, column=0, columnspan=2)

tk.Label(app, text="Collection ID").grid(row=5, column=0)
collection_id_entry = tk.Entry(app)
collection_id_entry.grid(row=5, column=1)

tk.Button(app, text="Upload Document", command=upload_document).grid(row=6, column=0, columnspan=2)

tk.Label(app, text="Document ID").grid(row=7, column=0)
doc_id_entry = tk.Entry(app)
doc_id_entry.grid(row=7, column=1)

tk.Label(app, text="Page Number").grid(row=8, column=0)
page_number_entry = tk.Entry(app)
page_number_entry.grid(row=8, column=1)

tk.Button(app, text="Start OCR", command=start_ocr).grid(row=9, column=0, columnspan=2)

app.mainloop()
