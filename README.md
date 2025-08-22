# 📊 Network Utilization Dashboard for Infrastructure Planning  

## 📌 Project Overview  
This project analyzes **network utilization data** to help telecom planners (e.g., Jio) identify peak usage times, performance bottlenecks, and plan for **future infrastructure development**.  

The project uses:  
- **SQL** → To pull raw network usage data  
- **Python (pandas, matplotlib, seaborn)** → To clean, analyze, and visualize data  
- **Streamlit** → To build an **interactive dashboard** for planners  

---

## 📂 Dataset  
The dataset used in this project (`network_utilization_full.csv`) contains simulated network utilization data with the following columns:  

| Column Name       | Description |
|-------------------|-------------|
| `timestamp`       | Date & time of record (hourly) |
| `region`          | Geographical region (North, South, East, West) |
| `city`            | City name (Mumbai, Delhi, Bengaluru, etc.) |
| `site_id`         | Unique identifier for each site |
| `cell_id`         | Unique identifier for each cell |
| `tech`            | Technology type (4G/5G) |
| `capacity_mbps`   | Total network capacity (in Mbps) |
| `throughput_mbps` | Actual throughput (in Mbps) |
| `utilization_pct` | Utilization percentage of the network |
| `latency_ms`      | Latency in milliseconds |
| `packet_loss_pct` | Packet loss percentage |
| `users_active`    | Number of active users |

---

## ⚙️ Installation  

1. Clone this repository  
   ```bash
   git clone https://github.com/your-username/network-utilization-dashboard.git
   cd network-utilization-dashboard
   ```

2. Create a virtual environment (optional but recommended)  
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. Install dependencies  
   ```bash
   pip install -r requirements.txt
   ```

---

## ▶️ Running the Dashboard  

1. Make sure the dataset `network_utilization_full.csv` is in the project folder.  
2. Run the Streamlit app:  
   ```bash
   streamlit run app.py
   ```
3. The dashboard will open in your browser at `http://localhost:8501`.  

---

## 📊 Dashboard Features  

✅ **Utilization Trends** → View utilization % and throughput over time  
✅ **Peak Hours Analysis** → Identify when the network is overloaded  
✅ **Geographical Insights** → Compare cities and regions  
✅ **Tech Comparison** → Compare 4G vs 5G performance  
✅ **KPIs** → Monitor latency, packet loss, and active users  

---

## 📈 Example Use Cases  

- Identify **peak usage hours** to optimize load balancing  
- Compare **4G vs 5G** utilization for investment planning  
- Monitor **latency & packet loss** for QoS improvements  
- Support **capacity planning** for future network expansion  

---

## 🛠️ Tech Stack  
- **Python** (pandas, matplotlib, seaborn)  
- **SQL** (for data extraction)  
- **Streamlit** (interactive dashboard)  

---

## 👤 Author  
**Ashish Kumar**  
📧 beashishrj@gmail.com  
🔗 https://www.linkedin.com/in/ashishkumarrajpoot/
