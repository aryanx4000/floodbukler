import mysql.connector
from datetime import datetime

print("="*40)
print("CAFE MANAGEMENT SYSTEM")
print("="*40)

# ============ DATABASE CONNECTION ============
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="aryansql@380",
        database="cafe",
    )
    mycursor = db.cursor()
    print("Database connected successfully\n")
except mysql.connector.Error as err:
    print(f"Database Connection Error: {err}")
    exit()


current_customer_id = None
current_customer_name = None
current_customer_mobilenum = None

# ============ USER AUTHENTICATION ============

def signup():
    """New user registration"""
    print("\n--- CREATE NEW ACCOUNT ---")
    username = input("Enter your username: ")
    mobilenum = input("Enter your 10-digit mobile number: ")
    address = input("Enter your address: ")

    if len(mobilenum)!= 10 or not mobilenum.isdigit():
        print("Invalid mobile number. Must be 10 digits.")
        return None, None, None

    sql = "INSERT INTO customerinfo (username, mobilenum, address) VALUES (%s, %s, %s)"
    val = (username, mobilenum, address)

    try:
        mycursor.execute(sql, val)
        db.commit()
        customer_id = mycursor.lastrowid
        print("Account created successfully!")
        return customer_id, username, mobilenum
    except mysql.connector.Error as err:
        if err.errno == 1062:
            print("Mobile number already registered. Please login.")
        else:
            print(f"Error: {err}")
        return None, None, None

def login():
    """Login with mobile number only """
    print("\n--- LOGIN ---")
    mobilenum = input("Enter your mobile number: ")

    mycursor.execute(
        "SELECT customer_id, username, mobilenum, address FROM customerinfo WHERE mobilenum = %s",
        (mobilenum,)
    )
    result = mycursor.fetchone()

    if result:
        print(f"\nWelcome back, {result[1]}!")
        print(f"Mobile: {result[2]}")
        print(f"Address: {result[3]}")
        return result[0], result[1], result[2]
    else:
        print("Mobile number not found. Please create an account.")
        return None, None, None

def authenticate():
    """Main auth flow - ek baar login/signup"""
    global current_customer_id, current_customer_name, current_customer_mobilenum

    while current_customer_id is None:
        print("\n1. Login")
        print("2. Sign Up")
        print("3. Exit")
        choice = input("Enter choice: ")

        if choice == "1":
            current_customer_id, current_customer_name, current_customer_mobilenum = login()
        elif choice == "2":
            current_customer_id, current_customer_name, current_customer_mobilenum = signup()
        elif choice == "3":
            db.close()
            exit()
        else:
            print("Invalid choice")

# ============ MENU FUNCTIONS ============

def view_menu():
    """View menu by category"""
    print("\n--- VIEW MENU ---")
    print("1. Main Course")
    print("2. Beverages")
    print("3. Sweets")
    print("4. Combo")
    print("5. All Items")

    underchoice = input("Choose category: ")
    category_map = {
        "1": "Main",
        "2": "Beverage",
        "3": "Sweets",
        "4": "Combo"
    }

    if underchoice in category_map:
        mycursor.execute(
            "SELECT item_id, item_name, price, stock FROM menu WHERE category = %s AND stock > 0",
            (category_map[underchoice],)
        )
    elif underchoice == "5":
        mycursor.execute("SELECT item_id, item_name, price, stock, category FROM menu WHERE stock > 0")
    else:
        print("Invalid choice")
        return

    res = mycursor.fetchall()
    if res:
        print("\n" + "="*60)
        print(f"{'ID':<5} {'Item Name':<35} {'Price':<10} {'Stock':<10}")
        print("="*60)
        for row in res:
            if underchoice == "5":
                print(f"{row[0]:<5} {row[1]:<35} ₹{row[2]:<9} {row[3]:<10} [{row[4]}]")
            else:
                print(f"{row[0]:<5} {row[1]:<35} ₹{row[2]:<9} {row[3]:<10}")
        print("="*60)
    else:
        print("No items found in this category")

# ============ ORDER & BILLING ============

def customer_order():
    """Place order and generate bill"""
    if current_customer_id is None:
        print("Please login first to place order.")
        return

    cart = []
    total_amount = 0

    while True:
        print("\n--- MENU ---")
        mycursor.execute("SELECT item_id, item_name, price, stock, category FROM menu WHERE stock > 0")
        menu_items = mycursor.fetchall()

        print(f"{'ID':<5} {'Item Name':<35} {'Price':<10} {'Stock':<10}")
        print("-"*60)
        for item in menu_items:
            print(f"{item[0]:<5} {item[1]:<35} ₹{item[2]:<9} {item[3]:<10}")

        try:
            item_id = int(input("\nEnter item ID to add to cart, 0 to checkout: "))
            if item_id == 0:
                break

            mycursor.execute("SELECT item_name, price, stock FROM menu WHERE item_id = %s", (item_id,))
            item = mycursor.fetchone()

            if not item:
                print("Invalid item ID")
                continue

            qty = int(input(f"Enter quantity for {item[0]}: "))
            if qty <= 0:
                print("Quantity must be > 0")
                continue
            if qty > item[2]:
                print(f"Only {item[2]} left in stock")
                continue

            cart.append((item_id, item[0], qty, item[1]))
            total_amount += item[1] * qty
            print(f"Added {qty} x {item[0]} to cart | Current Total: ₹{total_amount}")

        except ValueError:
            print("Enter valid numbers only")

    if not cart:
        print("Cart empty. Order cancelled.")
        return

    # Billing
    print("\n" + "="*50)
    print(f"BILL - Customer: {current_customer_name}")
    print(f"Mobile: {current_customer_mobilenum}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    for item in cart:
        print(f"{item[1]:<30} x {item[2]:<3} = ₹{item[2] * item[3]}")
    print("-"*50)
    print(f"{'TOTAL AMOUNT:':<35} ₹{total_amount}")
    print("="*50)

    confirm = input("Confirm order? (yes/no): ").lower()
    if confirm == "yes":
        try:
            order_sql = "INSERT INTO orders (customer_id, order_date, total_amount) VALUES (%s, %s, %s)"
            mycursor.execute(order_sql, (current_customer_id, datetime.now(), total_amount))
            order_id = mycursor.lastrowid

            for item in cart:
                item_sql = "INSERT INTO order_items (order_id, item_id, quantity, price) VALUES (%s, %s, %s, %s)"
                mycursor.execute(item_sql, (order_id, item[0], item[2], item[3]))

                update_stock = "UPDATE menu SET stock = stock - %s WHERE item_id = %s"
                mycursor.execute(update_stock, (item[2], item[0]))

            db.commit()
            print(f"\nOrder placed successfully! Order ID: {order_id}")
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            db.rollback()
    else:
        print("Order cancelled")

def view_order_history():
    """User ka order history SQL se"""
    if current_customer_id is None:
        print("Please login first")
        return

    mycursor.execute("""
        SELECT o.order_id, o.order_date, o.total_amount
        FROM orders o
        WHERE o.customer_id = %s
        ORDER BY o.order_date DESC LIMIT 10
    """, (current_customer_id,))

    orders = mycursor.fetchall()
    if not orders:
        print("No orders found")
        return

    print("\n" + "="*60)
    print("YOUR ORDER HISTORY")
    print("="*60)
    for order in orders:
        print(f"\nOrder ID: {order[0]} | Date: {order[1]} | Total: ₹{order[2]}")
        mycursor.execute("""
            SELECT m.item_name, oi.quantity, oi.price
            FROM order_items oi
            JOIN menu m ON oi.item_id = m.item_id
            WHERE oi.order_id = %s
        """, (order[0],))
        items = mycursor.fetchall()
        for item in items:
            print(f" - {item[0]} x {item[1]} = ₹{item[1] * item[2]}")
    print("="*60)

# ============ TABLE RESERVATION ============
def reserve_table():
    """Reserve a table"""
    if current_customer_id is None:
        print("Please login first")
        return

    try:
        table_no = int(input("Enter table number (1-20): "))
        if table_no < 1 or table_no > 20:
            print("Table number must be between 1-20")
            return

        reservation_date = input("Enter reservation date (YYYY-MM-DD): ")
        reservation_time = input("Enter reservation time (HH:MM:SS): ")
        no_of_people = int(input("Enter number of people: "))

        datetime.strptime(reservation_date, "%Y-%m-%d")
        datetime.strptime(reservation_time, "%H:%M:%S")

        if no_of_people <= 0:
            print("Number of people must be greater than zero.")
            return

        if datetime.strptime(reservation_date, "%Y-%m-%d").date() < datetime.now().date():
            print("Cannot book for past dates")
            return

    except ValueError:
        print("Invalid input. Please enter correct format.")
        return

    check_sql = """
    SELECT * FROM reservation
    WHERE table_no = %s AND reservation_date = %s AND reservation_time = %s AND table_status = 'reserved'
    """
    mycursor.execute(check_sql, (table_no, reservation_date, reservation_time))
    if mycursor.fetchone():
        print(f"Table {table_no} is already reserved at {reservation_time} on {reservation_date}.")
        return

    sql = """
    INSERT INTO reservation
    (customer_id, customer_name, mobilenum, table_no, reservation_date, reservation_time, no_of_people, table_status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, 'reserved')
    """
    val = (current_customer_id, current_customer_name, current_customer_mobilenum,
           table_no, reservation_date, reservation_time, no_of_people)

    try:
        mycursor.execute(sql, val)
        db.commit()
        print("Table reserved successfully!")
    except mysql.connector.Error as err:
        print("Error:", err)
        db.rollback()

# ============ ADMIN PANEL ============

def admin_panel():
    """Admin functions"""
    admin_pass = input("Enter Admin Password: ")
    if admin_pass!= "admin380747":
        print("Wrong password! Access denied")
        return

    while True:
        print("\n" + "="*40)
        print("ADMIN PANEL")
        print("="*40)
        print("1. Add New Item to Menu")
        print("2. Update Item Price/Stock")
        print("3. Delete Item from Menu")
        print("4. View All Reservations")
        print("5. View All Customers")
        print("6. View All Orders")
        print("7. Back to Main Menu")

        admin_choice = input("Enter your choice: ")

        if admin_choice == "1":
            try:
                item_id = int(input("Enter item id: "))
                item_name = input("Enter item name: ")
                price = float(input("Enter price: "))
                stock = int(input("Enter stock: "))
                category = input("Enter category (Main/Beverage/Sweets/Combo): ")

                sql = "INSERT INTO menu(item_id, item_name, price, stock, category) VALUES(%s, %s, %s, %s, %s)"
                val = (item_id, item_name, price, stock, category)

                mycursor.execute(sql, val)
                db.commit()
                print("Item Added Successfully")
            except mysql.connector.Error as err:
                if err.errno == 1062:
                    print("This item ID already exists")
                else:
                    print(f"Error: {err}")
            except ValueError:
                print("Invalid input")

        elif admin_choice == "2":
            try:
                item_id = int(input("Enter item id to update: "))
                price = float(input("Enter new price: "))
                stock = int(input("Enter new stock: "))
                sql = "UPDATE menu SET price=%s, stock=%s WHERE item_id=%s"
                val = (price, stock, item_id)
                mycursor.execute(sql, val)
                db.commit()
                if mycursor.rowcount > 0:
                    print("Item Updated")
                else:
                    print("Item ID not found")
            except ValueError:
                print("Invalid input")

        elif admin_choice == "3":
            try:
                item_id = int(input("Enter item id to delete: "))
                mycursor.execute("DELETE FROM menu WHERE item_id=%s", (item_id,))
                db.commit()
                if mycursor.rowcount > 0:
                    print("Item deleted")
                else:
                    print("Item ID not found")
            except ValueError:
                print("Invalid input")

        elif admin_choice == "4":
            mycursor.execute("""
                SELECT r.reservation_id, c.username, r.table_no, r.reservation_date,
                       r.reservation_time, r.no_of_people, r.table_status
                FROM reservation r
                JOIN customerinfo c ON r.customer_id = c.customer_id
                ORDER BY r.reservation_date DESC
            """)
            result = mycursor.fetchall()
            print("\n--- All Reservations ---")
            print(f"{'ID':<5} {'Customer':<15} {'Table':<7} {'Date':<12} {'Time':<10} {'People':<8} {'Status':<10}")
            print("-"*70)
            for row in result:
                print(f"{row[0]:<5} {row[1]:<15} {row[2]:<7} {str(row[3]):<12} {str(row[4]):<10} {row[5]:<8} {row[6]:<10}")

        elif admin_choice == "5":
            mycursor.execute("SELECT customer_id, username, mobilenum, address FROM customerinfo")
            result = mycursor.fetchall()
            print("\n--- All Customers ---")
            print(f"{'ID':<5} {'Username':<20} {'Mobile':<12} {'Address':<30}")
            print("-"*70)
            for row in result:
                print(f"{row[0]:<5} {row[1]:<20} {row[2]:<12} {row[3]:<30}")

        elif admin_choice == "6":
            mycursor.execute("""
                SELECT o.order_id, c.username, o.order_date, o.total_amount
                FROM orders o
                JOIN customerinfo c ON o.customer_id = c.customer_id
                ORDER BY o.order_date DESC LIMIT 20
            """)
            result = mycursor.fetchall()
            print("\n--- Recent Orders ---")
            for row in result:
                print(f"Order #{row[0]} | {row[1]} | {row[2]} | ₹{row[3]}")

        elif admin_choice == "7":
            break
        else:
            print("Invalid choice!")

# ============ SALES REPORT ============

def sales_report():
    """Sales analytics"""
    print("\n--- SALES REPORT ---")
    print("1. Today's Sales")
    print("2. Sales by Date")
    print("3. Top Selling Items")
    print("4. Monthly Summary")
    print("5. Back")

    report_choice = input("Enter choice: ")

    if report_choice == "1":
        today = datetime.now().date()
        mycursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(total_amount), 0)
            FROM orders WHERE DATE(order_date) = %s
        """, (today,))
        result = mycursor.fetchone()
        print(f"\nDate: {today}")
        print(f"Total Orders: {result[0]}")
        print(f"Total Revenue: ₹{result[1]}")

    elif report_choice == "2":
        date_str = input("Enter date (YYYY-MM-DD): ")
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            mycursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(total_amount), 0)
                FROM orders WHERE DATE(order_date) = %s
            """, (date_str,))
            result = mycursor.fetchone()
            print(f"\nDate: {date_str}")
            print(f"Total Orders: {result[0]}")
            print(f"Total Revenue: ₹{result[1]}")
        except ValueError:
            print("Invalid date format")

    elif report_choice == "3":
        mycursor.execute("""
            SELECT m.item_name, SUM(oi.quantity) as total_sold, SUM(oi.quantity * oi.price) as revenue
            FROM order_items oi
            JOIN menu m ON oi.item_id = m.item_id
            GROUP BY m.item_id, m.item_name
            ORDER BY total_sold DESC
            LIMIT 10
        """)
        results = mycursor.fetchall()
        print("\n--- TOP 10 SELLING ITEMS ---")
        print(f"{'Rank':<6} {'Item Name':<30} {'Qty Sold':<12} {'Revenue':<12}")
        print("-"*60)
        for i, row in enumerate(results, 1):
            print(f"{i:<6} {row[0]:<30} {row[1]:<12} ₹{row[2]:<11}")

    elif report_choice == "4":
        month = input("Enter month (YYYY-MM): ")
        try:
            mycursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(total_amount), 0), AVG(total_amount)
                FROM orders WHERE DATE_FORMAT(order_date, '%Y-%m') = %s
            """, (month,))
            result = mycursor.fetchone()
            print(f"\nMonth: {month}")
            print(f"Total Orders: {result[0]}")
            print(f"Total Revenue: ₹{result[1]}")
            print(f"Average Order Value: ₹{result[2] if result[2] else 0:.2f}")
        except:
            print("Invalid format")

# ============ MAIN PROGRAM ============
def main():
    # One time login
    authenticate()

    while True:
        print("\n" + "="*40)
        print(f"MAIN MENU - Logged in as: {current_customer_name}")
        print("="*40)
        print("1. Customer Order")
        print("2. View Menu")
        print("3. View Order History")
        print("4. Table Reservation")
        print("5. Sales Report")
        print("6. Admin Panel")
        print("7. Logout & Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            customer_order()
        elif choice == "2":
            view_menu()
        elif choice == "3":
            view_order_history()
        elif choice == "4":
            reserve_table()
        elif choice == "5":
            sales_report()
        elif choice == "6":
            admin_panel()
        elif choice == "7":
            print(f"Goodbye {current_customer_name}!")
            db.close()
            break
        else:
            print("Invalid choice! Try again")

if __name__ == "__main__":
    main()




    