import tkinter as tk
import requests

# Flask API endpoint
API_URL = "http://localhost:5000/get_inventory"

# Function to update UI with inventory data
def update_ui():
    try:
        response = requests.get(API_URL)
        data = response.json()
        pcs_label.config(text=f"PCs: {data['pcs']}")
        floor_label.config(text=f"Floor: {data['floor']}")
        inv_label.config(text=f"Inventory: {data['inv']}")
        prk_label.config(text=f"Perk: {data['prk']}")
    except Exception as e:
        status_label.config(text=f"Error: {e}")

# Initialize Tkinter window
root = tk.Tk()
root.title("Pixoo Inventory Dashboard")
root.geometry("300x200")

# Labels to display inventory data
pcs_label = tk.Label(root, text="PCs: -", font=("Arial", 14))
pcs_label.pack(pady=5)

floor_label = tk.Label(root, text="Floor: -", font=("Arial", 14))
floor_label.pack(pady=5)

inv_label = tk.Label(root, text="Inventory: -", font=("Arial", 14))
inv_label.pack(pady=5)

prk_label = tk.Label(root, text="Perk: -", font=("Arial", 14))
prk_label.pack(pady=5)

status_label = tk.Label(root, text="", font=("Arial", 10), fg="red")
status_label.pack(pady=5)

# Button to refresh data
refresh_button = tk.Button(root, text="Refresh", command=update_ui)
refresh_button.pack(pady=10)

# Initial data load
update_ui()

# Run the UI
root.mainloop()
