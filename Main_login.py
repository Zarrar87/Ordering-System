import sys
from admin_interface import AdminWindow
from customer_interface import CustomerAuthDialog
from customer_menu import CustomerMenu

 
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QMessageBox, QLineEdit, QLabel, QDialog
)
import mysql.connector as sq

# Connect to the database
db = sq.connect(host="localhost", user="root", password="1234", database="KFC")
mycursor = db.cursor()

# Ensure tables are created
def create_database():
    mycursor.execute("SET FOREIGN_KEY_CHECKS = 0")

    mycursor.execute("""
        CREATE TABLE IF NOT EXISTS menus (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50),
            price INT
        )
    """)
    mycursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            email VARCHAR(250) UNIQUE
        )
    """)
    mycursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
)
    """)
    mycursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    menu_id INT,
    order_id INT,
    FOREIGN KEY (menu_id) REFERENCES menus(id),
    FOREIGN KEY (order_id) REFERENCES orders(id)
)
    """)
    db.commit()

class LoginDialog(QDialog):
    def __init__(self, role="admin"):
        super().__init__()
        self.setWindowTitle(f"{role.capitalize()} Login")
        layout = QVBoxLayout()

        self.label = QLabel("Enter Password:" if role == "admin" else "Enter Email:")
        layout.addWidget(self.label)

        self.input = QLineEdit()
        if role == "admin":
            self.input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.input)

        self.button = QPushButton("Login")
        layout.addWidget(self.button)
        self.button.clicked.connect(self.check_login)

        self.role = role
        self.setLayout(layout)

    def check_login(self):
        if self.role == "admin":
            if self.input.text() == "12345":
                QMessageBox.information(self, "Login", "Admin login successful!")
                self.accept()
            else:
                QMessageBox.warning(self, "Login Failed", "Incorrect password.")
        else:
            email = self.input.text()
            mycursor.execute("SELECT id, name FROM customers WHERE email = %s", (email,))
            user = mycursor.fetchone()
            if user:
                QMessageBox.information(self, "Login", f"Welcome, {user[1]}")
                self.accept()
            else:
                QMessageBox.warning(self, "Login Failed", "Email not found.")

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KFC Ordering System")

        layout = QVBoxLayout()

        self.admin_btn = QPushButton("Admin Login")
        self.admin_btn.clicked.connect(self.admin_login)
        layout.addWidget(self.admin_btn)

        self.customer_btn = QPushButton("Customer Login")
        self.customer_btn.clicked.connect(self.customer_login)
        layout.addWidget(self.customer_btn)

        self.setLayout(layout)

    def admin_login(self):
        dialog = LoginDialog(role="admin")
        if dialog.exec_():
            self.admin_panel = AdminWindow()
            self.admin_panel.show()

#self.window
    def customer_login(self):
        dialog = CustomerAuthDialog()
        dialog.exec_()

if __name__ == "__main__":
    create_database()
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
