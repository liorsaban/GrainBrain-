# GrainBrain: Automated Sieve Analysis System

**GrainBrain** is a smart, automated solution for granulometry, integrating real-time weight measurements, grain-size distribution calculations, and professional report generation. It simplifies sieve analysis for laboratories and fieldwork, ensuring efficiency and accuracy.

---

## 🌟 Features
- ✅ **Automated Weight Measurement** – Reads sieve weights directly from a digital scale.  
- ✅ **Grain-Size Distribution Analysis** – Calculates key statistics (D10, D50, D90, mean size, modes).  
- ✅ **Professional Reporting** – Generates **PDF, Excel, and CSV** reports.  
- ✅ **Real-Time Data Processing** – Displays cumulative grain-size distribution curves.  
- ✅ **User-Friendly Interface** – Simple, step-by-step workflow for seamless operation.  

---

## 🛠️ Setup & Installation

### **1️⃣ Install Dependencies**
Ensure you have **Python 3.9+** installed. Then, install required packages:

```bash
pip install -r requirements.txt
```

### **2️⃣ Connect the Digital Scale**
Ensure your scale supports **serial communication** and connect it via a **USB-to-serial adapter**.

#### **Recommended Serial Connection Settings:**
- **Baudrate:** 9600
- **Data Bits:** 8
- **Parity:** None
- **Stop Bits:** 1
- **Flow Control:** None
- **Default port:** COM4 *(modify if needed)*

### **3️⃣ Run the App**
Launch the app

```bash
streamlit run app.py
```

---

## How to Use GrainBrain

### **Step 1: Enter Sample ID**

### **Step 2: Measure Empty Sieves**
- Place each empty sieve on the scale and press **"Measure"**.
- The system records the weight automatically.

### **Step 3: Measure Sample + Sieve**
- Add the sample to the sieves and weigh each again.
- Press **"Measure"** for each sieve.

### **Step 4: Analyze & Export Data**
- View calculated statistics (**mean size, D-values, modes**).
- Download **Excel, CSV, or PDF report**.
-Download data and statistics in **Excel / CSV**.
---

## ❌ Troubleshooting

### ⚠️ **Scale Not Connecting?**
- Ensure no other program (e.g., **serial monitor**) is using the port.
- Try **reconnecting the USB cable** and restarting the app.
- Modify the **COM port** settings if needed.

### ⚠️ **Weight Not Updating?**
- Ensure the **scale is stable** before measuring.
- Press the **"Measure"** button again to retry.
- Make sure Serial Connection Settings are correct

---

## Credits
Developed by Lior Saban to streamline sieve analysis.
