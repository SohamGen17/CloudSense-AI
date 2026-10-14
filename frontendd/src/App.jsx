
import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import {
  Activity,
  AlertTriangle,
  Cpu,
  Thermometer,
  Zap,
  RefreshCw,
  Server,
  ShieldCheck,
  Send,
} from "lucide-react";
import "./App.css";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const normalSample = {
  device_id: "server-001",
  temperature: 30.8,
  humidity: 54.2,
  vibration: 0.021,
  voltage: 12.1,
  current: 1.32,
  power: 15.97,
  cpu_utilization: 48.3,
  cpu_temperature: 45.7,
};

const abnormalSample = {
  device_id: "server-001",
  temperature: 48.7,
  humidity: 51.8,
  vibration: 0.12,
  voltage: 10.8,
  current: 2.4,
  power: 25.92,
  cpu_utilization: 95,
  cpu_temperature: 78.3,
};

function MetricCard({ title, value, unit, icon: Icon, detail }) {
  return (
    <div className="metric-card">
      <div className="metric-heading">
        <span>{title}</span>
        <Icon size={19} />
      </div>
      <div className="metric-value">
        {value ?? "—"} <small>{unit}</small>
      </div>
      <div className="metric-detail">{detail}</div>
    </div>
  );
}

export default function App() {
  const [summary, setSummary] = useState(null);
  const [latest, setLatest] = useState(null);
  const [history, setHistory] = useState([]);
  const [apiStatus, setApiStatus] = useState("Checking");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");

  const loadDashboard = useCallback(async () => {
    try {
      const [healthRes, summaryRes, historyRes] = await Promise.all([
        axios.get(`${API}/health`),
        axios.get(`${API}/api/summary`),
        axios.get(`${API}/api/telemetry?limit=50`),
      ]);

      setApiStatus(healthRes.data.status === "healthy" ? "Online" : "Check");
      setSummary(summaryRes.data);
      setLatest(summaryRes.data.latest_reading);
      setHistory(
        [...historyRes.data.records]
          .reverse()
          .map((r) => ({
            ...r,
            time: new Date(r.timestamp).toLocaleTimeString(),
          }))
      );
      setError("");
    } catch (err) {
      setApiStatus("Offline");
      setError(
        "Cannot reach the API. Start FastAPI on port 8000 and check CORS."
      );
    }
  }, []);

  useEffect(() => {
    loadDashboard();
    const timer = setInterval(loadDashboard, 5000);
    return () => clearInterval(timer);
  }, [loadDashboard]);

  async function sendSample(sample) {
    setBusy(true);
    setError("");
    try {
      const response = await axios.post(`${API}/api/predict`, sample);
      setResult(response.data);
      await loadDashboard();
    } catch (err) {
      setError(
        err.response?.data?.detail
          ? JSON.stringify(err.response.data.detail)
          : "Prediction request failed. Check that FastAPI is running."
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Activity size={23} /></div>
          <div>
            <strong>CloudSense<span>-AI</span></strong>
            <small>INFRASTRUCTURE INTELLIGENCE</small>
          </div>
        </div>

        <div className="nav-label">MONITORING</div>
        
        <button
          className={`nav-item ${activeTab === "overview" ? "active" : ""}`}
          onClick={() => setActiveTab("overview")}
        >
          <Activity size={18} /> Overview
        </button>

        <button
          className={`nav-item ${activeTab === "telemetry" ? "active" : ""}`}
          onClick={() => setActiveTab("telemetry")}
        >
          <Server size={18} /> Server telemetry
        </button>

        <button
          className={`nav-item ${activeTab === "anomalies" ? "active" : ""}`}
          onClick={() => setActiveTab("anomalies")}
        >
          <ShieldCheck size={18} /> Anomaly detection
        </button>


        <div className="sidebar-bottom">
          <div className="source-tag"><span /> SIMULATED DATA</div>
          <small>ML-powered monitoring prototype</small>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <div className="eyebrow">INFRASTRUCTURE / OVERVIEW</div>
            <h1>System Overview</h1>
            <p>Monitor server health and detect unusual operating behavior.</p>
          </div>
          <div className={`api-status ${apiStatus.toLowerCase()}`}>
            <span /> API {apiStatus}
          </div>
        </header>

        {error && <div className="error-banner"><AlertTriangle size={18} /> {error}</div>}

        <section className="section-heading">
          
          <div>
            <h2>Infrastructure metrics</h2>
            <p>Latest recorded telemetry from your test server.</p>
          </div>
          <button className="secondary-button" onClick={loadDashboard}>
            <RefreshCw size={16} /> Refresh
          </button>

          
          {activeTab === "overview" && (
            <>
              {/* Keep your existing metrics, chart, health panel,
                  and telemetry simulator sections here. */}
            </>
          )}

          {activeTab === "telemetry" && (
            <section className="panel">
              <h2>Server Telemetry</h2>
              <p>Latest readings and historical server measurements.</p>

              <div className="metrics-grid">
                <MetricCard
                  title="Ambient temperature"
                  value={latest?.temperature}
                  unit="°C"
                  icon={Thermometer}
                  detail="Latest recorded reading"
                />
                <MetricCard
                  title="Humidity"
                  value={latest?.humidity}
                  unit="%"
                  icon={Activity}
                  detail="Latest recorded reading"
                />
                <MetricCard
                  title="CPU utilization"
                  value={latest?.cpu_utilization}
                  unit="%"
                  icon={Cpu}
                  detail="Server workload"
                />
                <MetricCard
                  title="Power consumption"
                  value={latest?.power}
                  unit="W"
                  icon={Zap}
                  detail="Latest recorded reading"
                />
              </div>

              <h2>Recent readings</h2>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Temperature</th>
                      <th>CPU temp.</th>
                      <th>CPU usage</th>
                      <th>Power</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.slice().reverse().map((item) => (
                      <tr key={item.id}>
                        <td>{item.time}</td>
                        <td>{item.temperature} °C</td>
                        <td>{item.cpu_temperature} °C</td>
                        <td>{item.cpu_utilization}%</td>
                        <td>{item.power} W</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

{activeTab === "anomalies" && (
  <section className="panel">
    <h2>Anomaly Detection</h2>
    <p>Readings classified by the Isolation Forest model.</p>

    <div className="metrics-grid">
      <MetricCard
        title="Total readings"
        value={summary?.total_readings ?? 0}
        unit=""
        icon={Activity}
        detail="Stored telemetry"
      />
      <MetricCard
        title="Detected anomalies"
        value={summary?.anomaly_count ?? 0}
        unit=""
        icon={AlertTriangle}
        detail="Model-flagged readings"
      />
    </div>

    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Device</th>
            <th>CPU temp.</th>
            <th>Anomaly score</th>
            <th>Classification</th>
          </tr>
        </thead>
        <tbody>
          {history
            .filter((item) => item.anomaly)
            .slice()
            .reverse()
            .map((item) => (
              <tr key={item.id}>
                <td>{item.time}</td>
                <td>{item.device_id}</td>
                <td>{item.cpu_temperature} °C</td>
                <td>{item.anomaly_score?.toFixed(4) ?? "—"}</td>
                <td>
                  <span className="risk-pill risk-high">
                    ANOMALY
                  </span>
                </td>
              </tr>
            ))}
        </tbody>
      </table>

      {!history.some((item) => item.anomaly) && (
        <p>No anomalies are present in the loaded readings.</p>
      )}
    </div>
  </section>
)}

        </section>

        <section className="metrics-grid">
          <MetricCard
            title="CPU temperature"
            value={latest?.cpu_temperature}
            unit="°C"
            icon={Thermometer}
            detail="Latest reading"
          />
          <MetricCard
            title="CPU utilization"
            value={latest?.cpu_utilization}
            unit="%"
            icon={Cpu}
            detail="Compute workload"
          />
          <MetricCard
            title="Power consumption"
            value={latest?.power}
            unit="W"
            icon={Zap}
            detail="Estimated from voltage × current"
          />
          <MetricCard
            title="Anomaly events"
            value={summary?.anomaly_count ?? 0}
            unit=""
            icon={AlertTriangle}
            detail={`${summary?.total_readings ?? 0} total readings stored`}
          />
        </section>

        <section className="content-grid">
          <div className="panel chart-panel">
            <div className="panel-heading">
              <div>
                <h2>Telemetry history</h2>
                <p>CPU temperature over recent saved readings</p>
              </div>
              <span className="panel-badge">LIVE REFRESH</span>
            </div>

            <div className="chart-area">
              {history.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={history}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#253142" />
                    <XAxis dataKey="time" stroke="#8a9ab0" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#8a9ab0" tick={{ fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: "#111b2a", border: "1px solid #344155" }} />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="cpu_temperature"
                      name="CPU temperature (°C)"
                      stroke="#55d6be"
                      dot={false}
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="empty-state">
                  <Activity size={30} />
                  <strong>No telemetry history yet</strong>
                  <span>Submit a test reading below to populate this chart.</span>
                </div>
              )}
            </div>
          </div>

          <div className="panel health-panel">
            <div className="panel-heading">
              <div>
                <h2>Device health</h2>
                <p>Most recent ML classification</p>
              </div>
            </div>

            <div className={`health-icon ${latest?.anomaly ? "warning" : "healthy"}`}>
              {latest?.anomaly ? <AlertTriangle size={27} /> : <ShieldCheck size={27} />}
            </div>
            <div className="health-title">
              {latest ? (latest.anomaly ? "Anomaly detected" : "No anomaly detected") : "Awaiting telemetry"}
            </div>
            <div className={`risk-pill ${latest?.anomaly ? "risk-high" : "risk-low"}`}>
              {latest?.risk_level ?? "NO DATA"}
            </div>

            <div className="health-divider" />
            <div className="detail-row">
              <span>Device ID</span><strong>{latest?.device_id ?? "—"}</strong>
            </div>
            <div className="detail-row">
              <span>Ambient temperature</span><strong>{latest ? `${latest.temperature} °C` : "—"}</strong>
            </div>
            <div className="detail-row">
              <span>Vibration</span><strong>{latest?.vibration ?? "—"} g</strong>
            </div>
            <div className="detail-row">
              <span>Humidity</span><strong>{latest ? `${latest.humidity}%` : "—"}</strong>
            </div>
          </div>
        </section>

        <section className="panel test-panel">
          <div className="panel-heading">
            <div>
              <h2>Telemetry simulator</h2>
              <p>Submit sample readings to test the trained anomaly detector.</p>
            </div>
            <Send size={20} />
          </div>

          <div className="sample-buttons">
            <button
              className="primary-button"
              disabled={busy}
              onClick={() => sendSample(normalSample)}
            >
              {busy ? "Sending..." : "Send normal sample"}
            </button>
            <button
              className="danger-button"
              disabled={busy}
              onClick={() => sendSample(abnormalSample)}
            >
              {busy ? "Sending..." : "Send abnormal sample"}
            </button>
          </div>

          {result && (
            <div className="result-box">
              <strong>Latest prediction response</strong>
              <pre>{JSON.stringify(result, null, 2)}</pre>
            </div>
          )}
        </section>

        <footer>
          CloudSense-AI · Machine-learning-based predictive maintenance prototype
          <span>Data source: simulated telemetry</span>
        </footer>
      </main>
    </div>
  );
}
