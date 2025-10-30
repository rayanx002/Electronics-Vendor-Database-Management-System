import streamlit as st # type: ignore
import sqlite3
import pandas as pd # type: ignore
import altair as alt # type: ignore
import base64

def add_bg_from_local(image_file):
    with open(image_file, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        [data-testid="stHeader"] {{
            background: rgba(0,0,0,0);
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


st.set_page_config(page_title="Electronics Vendor DB", layout="wide")

# Connect to SQLite DB
conn = sqlite3.connect('electronics_vendor.db')

st.title("📦 Electronics Vendor Database")
add_bg_from_local("background.png")

menu = [
    "Home",
    "View Tables",
    "Run Queries",
    "Visual Analytics",
    "Search & Filters",
    "Add Product"
]
choice = st.sidebar.selectbox("Select Option", menu)

# ------------------ HOME ------------------



if choice == "Home":

    st.subheader("Welcome 👋")
    st.markdown("""
    Our project demonstrates a full DBMS implementation for an **Electronics Vendor**.  
    It includes:
    - Database design using SQLite
    - CRUD operations
    - Data visualization (Altair charts) 
    - Interactive search & filters using Streamlit 
    - Database design using SQLite  
    """)

# ------------------ VIEW TABLES ------------------
elif choice == "View Tables":
    st.subheader("📋 View Database Tables")
    tables = ["Vendor", "Product", "Customer", "Shipment", "Order_Table", "Order_Details"]
    selected_table = st.selectbox("Select Table", tables)
    df = pd.read_sql_query(f"SELECT * FROM {selected_table}", conn)
    st.dataframe(df, use_container_width=True)

# ------------------ RUN QUERIES ------------------
elif choice == "Run Queries":
    st.subheader("🧠 Analytical Queries")

    q_type = st.selectbox("Choose Query", [
        "Top 2 Products by Sales",
        "Customer Who Spent the Most",
        "Delayed Shipments"
    ])

    if q_type == "Top 2 Products by Sales":
        query = """
        SELECT p.Product_Name, SUM(od.Quantity * p.Unit_Price) AS TotalSales
        FROM Product p
        JOIN Order_Details od ON p.Product_ID = od.Product_ID
        GROUP BY p.Product_Name
        ORDER BY TotalSales DESC
        LIMIT 2;
        """
    elif q_type == "Customer Who Spent the Most":
        query = """
        SELECT c.Name, SUM(o.Total_Amount) AS TotalSpent
        FROM Customer c
        JOIN Order_Table o ON c.Customer_ID = o.Customer_ID
        GROUP BY c.Name
        ORDER BY TotalSpent DESC
        LIMIT 1;
        """
    else:
        query = """
        SELECT * FROM Shipment
        WHERE julianday(Delivery_Date) - julianday(Shipment_Date) > 7;
        """

    df = pd.read_sql_query(query, conn)
    st.dataframe(df, use_container_width=True)

# ------------------ VISUAL ANALYTICS ------------------
elif choice == "Visual Analytics":
    st.subheader("📈 Data Visualizations")

    # 1️⃣ Top-selling products
    st.markdown("### 🏆 Top-Selling Products")
    query1 = """
    SELECT p.Product_Name, SUM(od.Quantity * p.Unit_Price) AS TotalSales
    FROM Product p
    JOIN Order_Details od ON p.Product_ID = od.Product_ID
    GROUP BY p.Product_Name
    ORDER BY TotalSales DESC;
    """
    df1 = pd.read_sql_query(query1, conn)
    if not df1.empty:
        chart1 = alt.Chart(df1).mark_bar(color='teal').encode(
            x=alt.X('Product_Name', sort='-y'),
            y='TotalSales'
        ).properties(width=700, height=400)
        st.altair_chart(chart1, use_container_width=True)
    else:
        st.info("No data available for product sales.")

    # 2️⃣ Sales by brand
    st.markdown("### 💼 Sales by Brand")
    query2 = """
    SELECT p.Brand, SUM(od.Quantity * p.Unit_Price) AS TotalSales
    FROM Product p
    JOIN Order_Details od ON p.Product_ID = od.Product_ID
    GROUP BY p.Brand
    ORDER BY TotalSales DESC;
    """
    df2 = pd.read_sql_query(query2, conn)
    if not df2.empty:
        chart2 = alt.Chart(df2).mark_arc(innerRadius=50).encode(
            theta='TotalSales',
            color='Brand',
            tooltip=['Brand', 'TotalSales']
        ).properties(width=400, height=400)
        st.altair_chart(chart2, use_container_width=True)
    else:
        st.info("No brand sales data available.")

    # 3️⃣ Stock per vendor
    st.markdown("### 🏬 Stock Quantity by Vendor")
    query3 = """
    SELECT v.Vendor_Name, SUM(p.Stock_Quantity) AS TotalStock
    FROM Product p
    JOIN Vendor v ON p.Vendor_ID = v.Vendor_ID
    GROUP BY v.Vendor_Name;
    """
    df3 = pd.read_sql_query(query3, conn)
    if not df3.empty:
        chart3 = alt.Chart(df3).mark_bar(color='orange').encode(
            x=alt.X('Vendor_Name', sort='-y'),
            y='TotalStock'
        ).properties(width=700, height=400)
        st.altair_chart(chart3, use_container_width=True)
    else:
        st.info("No inventory data available.")

# ------------------ SEARCH & FILTERS ------------------
elif choice == "Search & Filters":
    st.subheader("🔍 Search Products and Filter Orders")

    tab1, tab2 = st.tabs(["Search Products", "Filter Orders"])

    # 🔎 Search Products
    with tab1:
        st.markdown("### 🔍 Search Products by Brand or Category")
        search_type = st.radio("Search by", ["Brand", "Category"], horizontal=True)
        keyword = st.text_input(f"Enter {search_type} name").strip()

        if st.button("Search"):
            if keyword:
                query = f"""
                SELECT * FROM Product
                WHERE {search_type} LIKE '%{keyword}%';
                """
                df_search = pd.read_sql_query(query, conn)
                if not df_search.empty:
                    st.dataframe(df_search, use_container_width=True)
                else:
                    st.warning(f"No products found for {search_type} '{keyword}'")
            else:
                st.info("Please enter a keyword.")

    # 🧾 Filter Orders
    with tab2:
        st.markdown("### 🧾 Filter Orders by Customer")
        customers = pd.read_sql_query("SELECT DISTINCT Name FROM Customer;", conn)
        selected_customer = st.selectbox("Select Customer", customers["Name"])

        query = f"""
        SELECT o.Order_ID, o.Order_Date, o.Total_Amount, s.Status
        FROM Order_Table o
        JOIN Customer c ON o.Customer_ID = c.Customer_ID
        JOIN Shipment s ON o.Shipment_ID = s.Shipment_ID
        WHERE c.Name = '{selected_customer}';
        """
        df_orders = pd.read_sql_query(query, conn)
        if not df_orders.empty:
            st.dataframe(df_orders, use_container_width=True)
        else:
            st.warning("No orders found for this customer.")

# ------------------ ADD PRODUCT ------------------
elif choice == "Add Product":
    st.subheader("➕ Add New Product")
    with st.form("product_form"):
        pid = st.number_input("Product ID", min_value=1)
        pname = st.text_input("Product Name")
        cat = st.text_input("Category")
        brand = st.text_input("Brand")
        price = st.number_input("Unit Price", min_value=0)
        qty = st.number_input("Stock Quantity", min_value=0)
        vid = st.number_input("Vendor ID", min_value=1)
        submit = st.form_submit_button("Add Product")

        if submit:
            conn.execute("INSERT INTO Product VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (pid, pname, cat, brand, price, qty, vid))
            conn.commit()
            st.success("✅ Product Added Successfully!")

conn.close()
