from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, QTableWidget,
    QTableWidgetItem, QSpinBox, QHBoxLayout
)
import mysql.connector as sq

# Connect to DB
db = sq.connect(host="localhost", user="root", password="1234", database="KFC")
cursor = db.cursor()

class CustomerMenu(QWidget):
    def __init__(self, customer_id, customer_name):
        super().__init__()
        self.customer_id = customer_id
        self.customer_name = customer_name

        self.setWindowTitle(f"Welcome, {customer_name} — Place Your Order")
        self.resize(600, 400)

        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Item ID", "Item Name", "Price", "Quantity"])
        layout.addWidget(self.table)

        self.load_menu_items()

        self.order_btn = QPushButton("Place Order")
        self.order_btn.clicked.connect(self.place_order)
        layout.addWidget(self.order_btn)

        self.setLayout(layout)

    def load_menu_items(self):
        cursor.execute("SELECT * FROM menus")
        items = cursor.fetchall()

        self.table.setRowCount(len(items))

        for row, (id_, name, price) in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(str(id_)))
            self.table.setItem(row, 1, QTableWidgetItem(name))
            self.table.setItem(row, 2, QTableWidgetItem(str(price)))

            spinbox = QSpinBox()
            spinbox.setRange(0, 20)
            self.table.setCellWidget(row, 3, spinbox)

    def place_order(self):
        items_ordered = []
        total_items = 0
        total_price = 0

        for row in range(self.table.rowCount()):
            menu_id = int(self.table.item(row, 0).text())
            item_name = self.table.item(row, 1).text()
            price = float(self.table.item(row, 2).text())
            quantity = self.table.cellWidget(row, 3).value()

            if quantity > 0:
                subtotal = price * quantity
                items_ordered.append((menu_id, item_name, quantity, price, subtotal))
                total_items += quantity
                total_price += subtotal

        if not items_ordered:
            QMessageBox.warning(self, "No Items Selected", "Please select at least one item to place an order.")
            return

        # Build summary message
        summary = "You are about to order:\n\n"
        for item in items_ordered:
            summary += f"{item[1]} x {item[2]} = Rs {item[4]:.2f}\n"
        summary += f"\nTotal Items: {total_items}\nTotal Price: Rs {total_price:.2f}\n\n"
        summary += "Do you want to confirm the order?"

        # Show confirmation dialog
        confirm = QMessageBox.question(self, "Confirm Order", summary,
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if confirm == QMessageBox.Yes:
            # Insert order
            cursor.execute("INSERT INTO orders (customer_id) VALUES (%s)", (self.customer_id,))
            db.commit()
            order_id = cursor.lastrowid

            for item in items_ordered:
                menu_id = item[0]
                quantity = item[2]
                for _ in range(quantity):
                    cursor.execute("INSERT INTO order_items (menu_id, order_id) VALUES (%s, %s)", (menu_id, order_id))

            db.commit()

            QMessageBox.information(self, "Order Placed", "Your order has been successfully placed!")
            self.close()
        else:
            QMessageBox.information(self, "Order Cancelled", "You can now edit your selection.")
