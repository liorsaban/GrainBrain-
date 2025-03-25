import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import os
import io
import time
import serial
import serial.tools.list_ports
from scipy.signal import find_peaks
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from datetime import datetime
from scipy.stats import mode
from serial_connection import SerialConnection
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Image

matplotlib.use('Agg')  # Use a non-interactive backend for Streamlit


# ✅ Persistent connection (cached across page reloads)
@st.cache_resource
def init_serial_connection(port="COM4"):
    try:
        conn = SerialConnection(port)
        return conn if conn.ser else None
    except serial.SerialException as e:
        st.error(f"❌ SerialException: {e}")
        return None

def close_serial_connection():
    if "scale" in st.session_state and st.session_state.scale:
        st.session_state.scale.close()
        del st.session_state.scale
        st.cache_resource.clear()
        time.sleep(2)  # Allow OS to release COM port

# Allow user to select COM port dynamically
available_ports = [p.device for p in serial.tools.list_ports.comports()]
selected_port = st.selectbox("🔌 Select COM port:", available_ports, index=available_ports.index("COM4") if "COM4" in available_ports else 0)


# Initialize connection if not already connected
if "scale" not in st.session_state or st.session_state.scale is None:
    st.session_state.scale = init_serial_connection(selected_port)

import requests
import socket

# ✅ Automatically get local IP (your PC running the Flask API)
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        return None

# ✅ Request weight data from the local API
def read_weight():
    local_ip = get_local_ip()
    if not local_ip:
        return "Error: Could not determine local IP"
    
    api_url = f"http://{local_ip}:5000/read_weight"
    
    try:
        response = requests.get(api_url)
        data = response.json()
        return data.get("weight", "Error: No Data")
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"





# ✅ Define Sieve Sizes
sieve_sizes = np.array([
    2000, 1700, 1410, 1180, 1000, 850, 710, 600, 500, 420,
    355, 300, 250, 180, 150, 125, 106, 90, 74, 63, 0
])

# ✅ File for storing empty sieve weights
empty_sieve_file = "empty_sieve_weights.csv"

# ✅ Initialize Session State
if "step" not in st.session_state:
    st.session_state["step"] = 1
if "sample_id" not in st.session_state:
    st.session_state["sample_id"] = ""
if "selected_sizes" not in st.session_state:
    st.session_state["selected_sizes"] = []
if "empty_weights" not in st.session_state:
    st.session_state["empty_weights"] = {}
if "sample_weights" not in st.session_state:
    st.session_state["sample_weights"] = {}


# ✅ Main UI Logic
def main():
    step = st.session_state["step"]

    # ---------------------------
    # STEP 1: Enter Sample ID & Load Existing Empty Weights
    # ---------------------------
    if step == 1:
        st.title("Auto Sieve - Step 1: Enter Sample ID")
        sample_id = st.text_input("Sample ID", value=st.session_state["sample_id"])
        if sample_id:
            st.session_state["sample_id"] = sample_id

        if os.path.exists(empty_sieve_file):
            st.write("⚙️ **Existing empty sieve data found.** Choose an option:")
            if st.button("📂 Use Existing Data"):
                existing_data = pd.read_csv(empty_sieve_file)
                st.session_state["empty_weights"] = dict(zip(existing_data["Sieve Size (μm)"], existing_data["Empty Weight (g)"]))
                st.success("✅ Using saved empty sieve weights.")
            if st.button("🔄 Recalibrate"):
                st.session_state["empty_weights"] = {}
                st.warning("⚠️ Proceeding to recalibrate empty sieve weights.")

        if st.button("Next →"):
            if not sample_id:
                st.warning("⚠️ Please enter a Sample ID!")
            else:
                st.session_state["step"] = 2
                st.rerun()

 # --------------------------- 
    # STEP 2: Measure Empty Sieve Weights
    # ---------------------------
    elif step == 2:
        st.title("Auto Sieve - Step 2: Measure Empty Sieve Weights")
        st.write(f"Sample ID: **{st.session_state['sample_id']}**")

        for size in sieve_sizes:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"Sieve {size} μm")
            with col2:
                weight = st.session_state["empty_weights"].get(size)
                button_label = f"✅ {weight} g" if weight is not None else f"Measure {size} μm"

                if st.button(button_label, key=f"empty_{size}"):
                    weight = read_weight()
                    if np.isnan(weight):
                        st.error(f"⚠️ Measurement failed for sieve {size} μm.")
                    else:
                        st.session_state["empty_weights"][size] = weight
                        st.success(f"✅ {size} μm: {weight} g")
                        st.rerun()

        if st.button("Next →", key="next_step_2"):
            if not st.session_state["empty_weights"]:
                st.warning("⚠️ Please measure at least one sieve before proceeding.")
            else:
                df_empty = pd.DataFrame({
                    "Sieve Size (μm)": list(st.session_state["empty_weights"].keys()),
                    "Empty Weight (g)": list(st.session_state["empty_weights"].values())
                })
                df_empty.to_csv(empty_sieve_file, index=False)
                st.session_state["step"] = 3
                st.rerun()

    # ---------------------------
    # STEP 3: Measure Sieve+Sample Weights
    # ---------------------------
    elif step == 3:
        st.title("Auto Sieve - Step 3: Measure Sieve+Sample Weights")
        st.write(f"Sample ID: **{st.session_state['sample_id']}**")

        for size in st.session_state["empty_weights"]:
            size_int = int(size)  # Ensure size is a standard Python int
            col1, col2 = st.columns([2, 1])
            with col1:
                empty_weight = st.session_state['empty_weights'][size]
                st.write(f"Sieve {size_int} μm (Empty: {empty_weight} g)")
            with col2:
                weight = st.session_state["sample_weights"].get(size_int)
                button_label = f"✅ {weight} g" if weight is not None else f"Measure Sample {size_int} μm"

                if st.button(button_label, key=f"sample_{size_int}"):
                    weight = read_weight()
                    if np.isnan(weight):
                        st.error(f"❌ Measurement failed for sieve {size_int} μm.")
                    else:
                        st.session_state["sample_weights"][size_int] = weight
                        st.success(f"✅ Measured: {weight} g")
                        st.rerun()

        if st.button("Next →", key="next_step_3"):
            if len(st.session_state["sample_weights"]) < len(st.session_state["empty_weights"]):
                st.warning("⚠️ Please measure all sieve+sample weights before proceeding.")
            else:
                st.session_state["step"] = 4
                st.rerun()



    # ---------------------------
    # STEP 4: Results & Exports
    # ---------------------------
    if step == 4:
        st.title("Auto Sieve - Step 4: Results")
        sample_id = st.session_state.get('sample_id', 'No Sample ID')
        st.write(f"Sample ID: **{sample_id}**")
        st.write(f"Date: **{datetime.now().strftime('%d/%m/%Y')}**")

        # ✅ Ensure required session state keys exist
        if "empty_weights" not in st.session_state or "sample_weights" not in st.session_state:
            st.error("⚠️ Missing data. Please restart the process.")
            st.stop()

        # ✅ Convert NumPy int64 keys to Python int
        selected_sizes = np.array(sorted([int(size) for size in st.session_state["empty_weights"].keys()]))
        empty_weights = np.array([st.session_state["empty_weights"][size] for size in selected_sizes])
        sample_weights = np.array([st.session_state["sample_weights"].get(size, np.nan) for size in selected_sizes])

        # ✅ Check for missing sample weights
        if np.all(np.isnan(sample_weights)):
            st.warning("⚠️ No valid sample weights recorded. Please return to Step 3 and measure sieve+sample weights.")
            if st.button("← Back to Step 3"):
                st.session_state["step"] = 3
                st.rerun()
            st.stop()

        # ✅ Calculate net sample weights
        net_weights = sample_weights - empty_weights

        # ✅ Check if any valid sample weights exist
        if np.isnan(net_weights).all():
            st.error("⚠️ No valid sample weights recorded. Please return to Step 3 and measure sieve+sample weights.")
            if st.button("← Back to Step 3"):
                st.session_state["step"] = 3
                st.rerun()
            st.stop()

        # ✅ Sort sieve sizes in ascending order
        sorted_indices = np.argsort(selected_sizes)
        sorted_sizes = selected_sizes[sorted_indices]
        sorted_net_weights = net_weights[sorted_indices]

        # ✅ Calculate Mid Sieve Sizes Correctly
        mid_sizes_sorted = []
        for i, size in enumerate(sorted_sizes):
            if i < len(sorted_sizes) - 1:
                mid = (size + sorted_sizes[i + 1]) / 2
            else:  # Largest sieve
                mid = size + 0.5 * size
            mid_sizes_sorted.append(mid)

        # ✅ Restore the original order of mid sieve sizes to match selected_sizes
        mid_sizes_sorted = [mid_sizes_sorted[np.where(sorted_sizes == s)[0][0]] for s in selected_sizes]

        # ✅ Handle special case where all weights are zero
        if sorted_net_weights.sum() == 0:
            mean_size, d10, d50, d90 = np.nan, np.nan, np.nan, np.nan
            percents = np.zeros(len(mid_sizes_sorted))
            st.warning("⚠️ No valid sample mass detected. Statistics will be empty.")
        else:
            # ✅ Compute cumulative % passing
            cumulative = np.cumsum(sorted_net_weights[::-1])[::-1]
            percents1 =  (cumulative / cumulative[0] * 100)
            percents = 100- (cumulative / cumulative[0] * 100)

            # ✅ Compute grain-size statistics
            mean_size = np.average(mid_sizes_sorted, weights=sorted_net_weights)
            d90 = np.interp(10, percents1[::-1], mid_sizes_sorted[::-1])
            d50 = np.interp(50, percents1[::-1], mid_sizes_sorted[::-1])
            d10 = np.interp(90, percents1[::-1], mid_sizes_sorted[::-1])

       # ✅ Calculate Modes (up to 3 prominent peaks) properly using histogram peaks

            mid_sizes_sorted_array = np.array(mid_sizes_sorted)  # Convert to NumPy array first!

        # Create a weighted histogram to find prominent modes
        bins = np.concatenate((mid_sizes_sorted_array, [mid_sizes_sorted_array[-1] + 1]))
        hist, bin_edges = np.histogram(
            np.repeat(mid_sizes_sorted_array, np.round(sorted_net_weights * 100).astype(int)),
            bins=bins
        )

        # Find peaks in the histogram (prominent modes)
        peaks, _ = find_peaks(hist)

        # Get peak mid-size values and their counts
        peak_sizes = mid_sizes_sorted_array[peaks]  # Now indexing works
        peak_counts = hist[peaks]

        # Sort peaks by their prominence (highest counts first)
        sorted_peak_indices = np.argsort(peak_counts)[::-1]
        modes = peak_sizes[sorted_peak_indices][:3]  # Take up to three peaks

        # Fill in NaNs if fewer than 3 modes are found
        modes = np.pad(modes, (0, max(0, 3 - len(modes))), constant_values=np.nan)

        
            # ✅ Display Full Statistics Table
        st.subheader("Grain-Size Statistics")
        stats_data = pd.DataFrame({
                "Statistic": ["Mean size", "D10", "D50", "D90", "Mode 1", "Mode 2", "Mode 3"],
                "Value (μm)": [mean_size, d10, d50, d90, modes[0], modes[1] if len(modes) > 1 else np.nan, modes[2] if len(modes) > 2 else np.nan]
            })
        st.table(stats_data)

            # ✅ Display Full Raw Data Table
        st.subheader("Raw Data")
        raw_data = pd.DataFrame({
                "Sieve Size (μm)": selected_sizes,
                "Mid Sieve Size (μm)": mid_sizes_sorted,
                "Net Weight (g)": net_weights
            })
        st.table(raw_data)

            # ✅ Generate and Show the Plot
        fig, ax1 = plt.subplots(figsize=(8, 5))
        ax1.plot(mid_sizes_sorted, percents, marker='o', linestyle='-', color='blue', label="Cumulative % Passing")
        ax1.set_xscale('log')
        ax1.set_xlabel('Grain size (μm)')
        ax1.set_ylabel('Cumulative % passing', color='blue')
        ax1.grid(True, which='both', ls='--', lw=0.5)

        ax2 = ax1.twinx()
        ax2.bar(mid_sizes_sorted, sorted_net_weights, width=np.array(mid_sizes_sorted)/3, alpha=0.5, color='gray', label="Net Weight")
        ax2.set_ylabel('Net Weight (g)', color='gray')
        ax2.invert_xaxis()
        plt.title('Grain-Size Distribution with Net Weight')
        st.pyplot(fig)

            # ✅ Export to Excel
        excel_filename = f"{sample_id}_sieve_results.xlsx"
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                raw_data.to_excel(writer, sheet_name='Raw Data', index=False)
                stats_data.to_excel(writer, sheet_name='Statistics', index=False)
        excel_bytes = excel_buffer.getvalue()
        st.download_button("Download Results (Excel)", data=excel_bytes, file_name=excel_filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # ✅ Export Raw Data to CSV
        csv_filename = f"{sample_id}_raw_data.csv"
        csv_bytes = raw_data.to_csv(index=False).encode()
        st.download_button("Export Raw Data (CSV)", data=csv_bytes, file_name=csv_filename, mime="text/csv")
         
         
            # ✅ Export pdf report

        def generate_pdf_report():
            sample_id = st.session_state.get('sample_id', 'No Sample ID')
            pdf_filename = f"{sample_id}_report.pdf"
            pdf_buffer = io.BytesIO()

            doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
            elements = []

            # Title & Date Table
            title = [["Auto Sieve Report", sample_id],
                    ["Date", datetime.now().strftime('%d/%m/%Y')]]
            title_table = Table(title, colWidths=[3 * inch, 3 * inch])
            title_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ]))
            elements.extend([title_table, Spacer(1, 12)])

            # Grain-Size Statistics Table (existing)
            stats_data = [
                ["Statistic", "Value (μm)"],
                ["Mean size", f"{mean_size:.2f}"],
                ["D10", f"{d10:.2f}"],
                ["D50", f"{d50:.2f}"],
                ["D90", f"{d90:.2f}"],
                ["Mode 1", f"{modes[0]:.2f}" if not np.isnan(modes[0]) else "-"],
                ["Mode 2", f"{modes[1]:.2f}" if not np.isnan(modes[1]) else "-"],
                ["Mode 3", f"{modes[2]:.2f}" if not np.isnan(modes[2]) else "-"],
            ]
            stats_table = Table(stats_data, colWidths=[3 * inch, 3 * inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ]))
            elements.extend([stats_table, Spacer(1, 12)])

            # Raw Data Table (existing)
            raw_data_table = [["Sieve Size (μm)", "Mid Sieve Size (μm)", "Net Weight (g)"]]
            for i in range(len(selected_sizes)):
                raw_data_table.append([
                    selected_sizes[i],
                    f"{mid_sizes_sorted[i]:.2f}",
                    f"{net_weights[i]:.2f}"
                ])

            raw_table = Table(raw_data_table, colWidths=[2 * inch, 2 * inch, 2 * inch])
            raw_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ]))
            elements.extend([raw_table, Spacer(1, 12)])

            # ✅ Generate the matplotlib plot and insert into PDF
            plot_buffer = io.BytesIO()
            fig.savefig(plot_buffer, format="png", dpi=300, bbox_inches='tight')
            plot_buffer.seek(0)
            
            # Define plot size in PDF (width, height)
            pdf_plot = Image(plot_buffer, 6 * inch, 4 * inch)
            elements.append(pdf_plot)

            # Generate PDF
            doc.build(elements)

            pdf_bytes = pdf_buffer.getvalue()
            st.download_button("Download Report (PDF)", data=pdf_bytes, file_name=pdf_filename, mime="application/pdf")

        # Call this after the existing plot is generated by matplotlib
        generate_pdf_report()


            # Navigation button

        if st.button("← Back"):
                st.session_state["step"] = 3
                st.rerun()

if __name__ == "__main__":
    main()
