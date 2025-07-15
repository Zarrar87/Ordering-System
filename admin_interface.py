from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QMessageBox,
    QTableWidget, QTableWidgetItem, QHBoxLayout
)
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)

from PyQt5.QtCore import Qt
import mysql.connector as sq

# Database connection
db = sq.connect(host="localhost", user="root", password="1234", database="KFC")
cursor = db.cursor()



class AdminWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Menu Editor")
        self.resize(750, 500)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.table = QTableWidget()
        self.layout.addWidget(self.table)

        self.load_table()

        self.save_btn = QPushButton("💾 Save Changes")
        self.save_btn.clicked.connect(self.save_changes)
        self.layout.addWidget(self.save_btn)

        self.history_btn = QPushButton("📜 View Order History")
        self.history_btn.clicked.connect(self.open_order_history)
        self.layout.addWidget(self.history_btn)

    def load_table(self):
        cursor.execute("SELECT * FROM menus")
        data = cursor.fetchall()

        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Price", "Delete"])
        self.table.setRowCount(len(data) + 1)  # extra row for new item

        for row, (id_, name, price) in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(str(id_)))
            self.table.item(row, 0).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

            self.table.setItem(row, 1, QTableWidgetItem(name))
            self.table.setItem(row, 2, QTableWidgetItem(str(price)))

            del_btn = QPushButton("🗑️")
            from functools import partial
            del_btn.clicked.connect(partial(self.delete_row, row))
            self.table.setCellWidget(row, 3, del_btn)

        # Last row: new item
        self.table.setItem(len(data), 0, QTableWidgetItem("New"))
        self.table.item(len(data), 0).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.table.setItem(len(data), 1, QTableWidgetItem(""))
        self.table.setItem(len(data), 2, QTableWidgetItem(""))

    def open_order_history(self):
        self.history_window = AdminOrderHistory()
        self.history_window.show()

    def delete_row(self, row):
        item_id = self.table.item(row, 0).text()
        if not item_id.isdigit():
            QMessageBox.warning(self, "Invalid", "Cannot delete unsaved/new row.")
            return

        confirm = QMessageBox.question(self, "Delete", f"Delete item ID {item_id} (and related order records)?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            # First delete from order_items to satisfy foreign key constraint
            cursor.execute("DELETE FROM order_items WHERE menu_id = %s", (item_id,))
            cursor.execute("DELETE FROM menus WHERE id = %s", (item_id,))
            db.commit()
            QMessageBox.information(self, "Deleted", f"Item ID {item_id} and its references deleted.")
            self.load_table()



    def save_changes(self):
        rows = self.table.rowCount()

        for row in range(rows):
            item_id = self.table.item(row, 0).text().strip()
            name = self.table.item(row, 1).text().strip()
            price_text = self.table.item(row, 2).text().strip()

            # Skip if empty row
            if not name or not price_text:
                continue

            if not price_text.isdigit():
                QMessageBox.warning(self, "Invalid Price", f"Row {row + 1}: Price must be a number.")
                return

            price = int(price_text)

            if item_id == "New":
                # Insert new item
                cursor.execute("INSERT INTO menus (name, price) VALUES (%s, %s)", (name, price))
            elif item_id.isdigit():
                # Update existing
                cursor.execute("UPDATE menus SET name=%s, price=%s WHERE id=%s", (name, price, int(item_id)))

        db.commit()
        QMessageBox.information(self, "Saved", "Changes saved successfully.")
        self.load_table()

class AdminOrderHistory(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("All Customer Orders")
        self.resize(800, 400)

        layout = QVBoxLayout()
        label = QLabel("<b>All Orders:</b>")
        layout.addWidget(label)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Customer", "Order ID", "Items", "Total Price", "Order Time"])
        layout.addWidget(self.table)

        cursor.execute("""
            SELECT 
                c.name,
                o.id AS order_id,
                GROUP_CONCAT(CONCAT(m.name, ' (Qty:', oi.quantity, ', Rs', m.price, ')') SEPARATOR ', ') AS items,
                SUM(oi.quantity * m.price) AS total_price,
                o.order_time
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            JOIN order_items oi ON o.id = oi.order_id
            JOIN menus m ON oi.menu_id = m.id
            GROUP BY o.id
            ORDER BY o.order_time DESC
        """)

        results = cursor.fetchall()
        self.table.setRowCount(len(results))

        for row_index, (cust_name, order_id, items, total_price, order_time) in enumerate(results):
            self.table.setItem(row_index, 0, QTableWidgetItem(cust_name))
            self.table.setItem(row_index, 1, QTableWidgetItem(str(order_id)))
            self.table.setItem(row_index, 2, QTableWidgetItem(items))
            self.table.setItem(row_index, 3, QTableWidgetItem(f"Rs{total_price}"))
            self.table.setItem(row_index, 4, QTableWidgetItem(str(order_time)))

        self.setLayout(layout)


class AdminLogin(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Login")
        self.resize(300, 150)

        layout = QVBoxLayout()

        self.pass_label = QLabel("Enter Admin Password:")
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)

        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.check_login)

        self.history_btn = QPushButton("View Order History")
        self.history_btn.setVisible(False)
        self.history_btn.clicked.connect(self.open_order_history)

        layout.addWidget(self.pass_label)
        layout.addWidget(self.pass_input)
        layout.addWidget(self.login_btn)
        layout.addWidget(self.history_btn)

        self.setLayout(layout)

    def check_login(self):
        password = self.pass_input.text().strip()

        # Replace this with a secure password or a DB check if needed
        if password == "12345":
            QMessageBox.information(self, "Access Granted", "Welcome, Admin!")
            self.history_btn.setVisible(True)
        else:
            QMessageBox.warning(self, "Access Denied", "Incorrect admin password.")

    def open_order_history(self):
        self.history_window = AdminOrderHistory()
        self.history_window.show()