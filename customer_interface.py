from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel,
    QMessageBox, QDialog, QApplication
)
import mysql.connector as sq
from customer_menu import CustomerMenu

# Connect to DB
db = sq.connect(host="localhost", user="root", password="1234", database="KFC")
cursor = db.cursor()

class CustomerWindow(QWidget):
    def __init__(self, customer_name):
        super().__init__()
        self.setWindowTitle(f"Welcome, {customer_name}")
        self.resize(400, 200)

        layout = QVBoxLayout()
        label = QLabel(f"Welcome {customer_name}!\n(Menu and Order system goes here)")
        layout.addWidget(label)
        self.setLayout(layout)


class CustomerAuthDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Customer Portal")
        self.resize(300, 200)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.login_btn = QPushButton("Login")
        self.signup_btn = QPushButton("Sign Up")

        self.login_btn.clicked.connect(self.login_form)
        self.signup_btn.clicked.connect(self.signup_form)

        self.layout.addWidget(self.login_btn)
        self.layout.addWidget(self.signup_btn)
#self.window
    def login_form(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Customer Login")
        layout = QVBoxLayout(dialog)

        email_input = QLineEdit()
        email_input.setPlaceholderText("Enter your email")
        login_btn = QPushButton("Login")

        layout.addWidget(QLabel("Email:"))
        layout.addWidget(email_input)
        layout.addWidget(login_btn)

        def handle_login():
            email = email_input.text().strip()
            if not email:
                QMessageBox.warning(self, "Error", "Please enter your email.")
                return

            cursor.execute("SELECT id, name FROM customers WHERE email = %s", (email,))
            result = cursor.fetchone()
            if result:
                QMessageBox.information(self, "Login Successful", f"Welcome {result[1]}")
                dialog.accept()
                self.accept()  # Close the auth dialog too
                self.menu_window = CustomerMenu(result[0], result[1])  # result[0] = customer_id, result[1] = name
                self.menu_window.show()
            else:
                QMessageBox.warning(self, "Login Failed", "Email not registered.")

        login_btn.clicked.connect(handle_login)
        dialog.exec_()


    def signup_form(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Customer Sign Up")
        layout = QVBoxLayout(dialog)

        name_input = QLineEdit()
        email_input = QLineEdit()
        signup_btn = QPushButton("Sign Up")

        layout.addWidget(QLabel("Name:"))
        layout.addWidget(name_input)
        layout.addWidget(QLabel("Email:"))
        layout.addWidget(email_input)
        layout.addWidget(signup_btn)

        def handle_signup():
            name = name_input.text().strip()
            email = email_input.text().strip()

            if not name or not email:
                QMessageBox.warning(self, "Error", "Please enter both name and email.")
                return

            try:
                cursor.execute("INSERT INTO customers (name, email) VALUES (%s, %s)", (name, email))
                db.commit()
                QMessageBox.information(self, "Sign Up Successful", "You can now log in.")
                dialog.close()
            except sq.errors.IntegrityError:
                QMessageBox.warning(self, "Error", "Email already exists.")

        signup_btn.clicked.connect(handle_signup)
        dialog.exec_()

# Place this after the LoginDialog or anywhere after the imports
class CustomerOrderHistory(QWidget):
    def __init__(self, customer_id, name):
        super().__init__()
        self.setWindowTitle(f"{name}'s Order History")
        layout = QVBoxLayout()

        label = QLabel(f"<b>Order history for {name}:</b>")
        layout.addWidget(label)

        cursor.execute("""
            SELECT 
                GROUP_CONCAT(CONCAT(m.name, ' (Qty:', oi.quantity, ', Rs', m.price, ')') SEPARATOR ', ') AS items,
                SUM(oi.quantity * m.price) AS total_price
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN menus m ON oi.menu_id = m.id
            WHERE o.customer_id = %s
        """, (customer_id,))

        result = cursor.fetchone()

        if result and result[0]:
            items_str = result[0]
            total_price = result[1]
            layout.addWidget(QLabel(f"Items: {items_str}"))
            layout.addWidget(QLabel(f"<b>Total Price: Rs{total_price}</b>"))
        else:
            layout.addWidget(QLabel("No orders found."))

        self.setLayout(layout)
