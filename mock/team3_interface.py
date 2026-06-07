"""
Mock Team 3 Integration - LLM Security Report Generator
Provides get_llm_explanation and generate_security_report with local Ollama support.
"""

import streamlit as st
import pandas as pd
import requests
import json

# Try importing the real Team 3 module
try:
    import importlib.util
    spec = importlib.util.find_spec("team3_module")
    if spec is not None:
        from team3_module import generate_security_report as real_generate_security_report
        from team3_module import get_llm_explanation as real_get_llm_explanation
        USE_MOCK = False
    else:
        USE_MOCK = True
except ImportError:
    USE_MOCK = True

def generate_dynamic_mock_report(df_anomalies):
    """Generate a highly realistic dynamic security report based on the actual anomalies."""
    if df_anomalies is None or df_anomalies.empty:
        return "🛡️ **Sentinel AI Security Report**\n\nNo anomalies detected at this time. System health is optimal."

    timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    report = f"# 🛡️ Sentinel AI Security Analysis Report\n"
    report += f"**Generated:** `{timestamp}` | **Scope:** Local Endpoint | **Model:** Gemma 2B (Mocked)\n\n"
    
    # Severity indicators
    critical_anom = df_anomalies[df_anomalies["Risk Score"] > 85]
    high_anom = df_anomalies[(df_anomalies["Risk Score"] > 70) & (df_anomalies["Risk Score"] <= 85)]
    medium_anom = df_anomalies[(df_anomalies["Risk Score"] > 50) & (df_anomalies["Risk Score"] <= 70)]
    
    overall_threat = "CRITICAL" if not critical_anom.empty else "HIGH" if not high_anom.empty else "MEDIUM"
    threat_color = "🔴" if overall_threat == "CRITICAL" else "🟠" if overall_threat == "HIGH" else "🟡"
    
    report += f"## 📊 Threat Summary\n"
    report += f"- **Overall Threat Level:** {threat_color} **{overall_threat}**\n"
    report += f"- **Total Flagged Anomalies:** `{len(df_anomalies)}` process(es)\n"
    report += f"- **Critical Risks:** `{len(critical_anom)}` | **High Risks:** `{len(high_anom)}` | **Medium/Low:** `{len(medium_anom) + len(df_anomalies[df_anomalies['Risk Score'] <= 50])}`\n\n"

    report += "## 🔍 Detailed Analysis of Top Flagged Processes\n\n"
    
    # Analyze up to 5 processes
    for idx, row in df_anomalies.sort_values(by="Risk Score", ascending=False).head(5).iterrows():
        pname = row['Process']
        pid = row['PID']
        cpu = row['CPU (%)']
        mem = row['Memory (%)']
        threads = row['Threads']
        score = row['Risk Score']
        
        status_icon = "🔴" if score > 85 else "🟠" if score > 70 else "🟡" if score > 50 else "🔵"
        
        report += f"### {status_icon} Process: `{pname}` (PID: `{pid}`)\n"
        report += f"- **Telemetry Stats:** CPU Usage: `{cpu}%` | Memory: `{mem}%` | Threads: `{threads}`\n"
        report += f"- **Risk Index:** `{score}/100`\n"
        report += f"- **Heuristic Flags:** "
        
        # Dynamic comments based on process name/stats
        if "malware" in pname.lower() or "suspicious" in pname.lower():
            report += "Known malicious signature pattern, unauthorized network activity detected.\n"
            report += "- **Potential Impact:** Ransomware, active beaconing to C2 servers, or credential harvesting.\n"
            report += "- **AI Verdict:** High confidence threat. Recommended action is immediate isolation.\n"
        elif cpu > 70 and threads > 50:
            report += "Abnormal CPU thread congestion. High probability of background resource hijacking or cryptojacking.\n"
            report += "- **Potential Impact:** Denial of Service (DoS) of local endpoint services, hardware degradation.\n"
            report += "- **AI Verdict:** High-volume computation anomaly. Investigate background mining scripts.\n"
        elif mem > 60:
            report += "Suspicious memory consumption. Possible buffer overflow attempt or memory injection attack.\n"
            report += "- **Potential Impact:** Privilege escalation, execution of arbitrary shellcode in authorized process spaces.\n"
            report += "- **AI Verdict:** Memory allocation anomaly. Inspect process stack memory.\n"
        else:
            report += "General telemetry drift. Unexpected system activity for a standard OS process.\n"
            report += "- **Potential Impact:** Misconfigured daemon, minor resource leak, or persistent hook installation.\n"
            report += "- **AI Verdict:** Low-priority anomaly. Monitor for further escalation.\n"
            
        report += "\n"

    report += "## 🛡️ Recommended Remediation Actions\n"
    if overall_threat == "CRITICAL":
        report += "1. **Network Isolation:** Cut network connectivity to the endpoint immediately using Sentinel Firewall controls.\n"
        report += "2. **Process Termination:** Forcefully terminate the highest-scoring PIDs (`" + ", ".join(critical_anom['PID'].astype(str).tolist()[:3]) + "`).\n"
        report += "3. **Forensic Dump:** Run a physical memory dump of affected process handles for reverse engineering.\n"
    elif overall_threat == "HIGH":
        report += "1. **Service Suspension:** Suspend the parent services of high-risk processes (`" + ", ".join(high_anom['Process'].tolist()[:3]) + "`).\n"
        report += "2. **Configuration Audit:** Scan configuration files and registry startup hooks for persistence vectors.\n"
        report += "3. **User Alert:** Notify the local system administrator to log off active interactive sessions.\n"
    else:
        report += "1. **Continuous Monitoring:** Keep the current processes on the watcher list for 24 hours.\n"
        report += "2. **Telemetry Verification:** Compare current values against weekly baseline telemetry parameters.\n"
        
    report += "\n---\n*Report generated by Project Sentinel AI engine. Privacy-first, local inference active.*"
    return report

def get_llm_explanation(df_anomalies):
    """
    Sends anomaly data to local Ollama (Gemma) if available.
    Otherwise, generates a highly realistic mock explanation.
    """
    if not USE_MOCK:
        try:
            return real_get_llm_explanation(df_anomalies)
        except Exception:
            pass

    if df_anomalies is None or df_anomalies.empty:
        return "No anomalies detected. The system is operating normally."
        
    # Build details
    details_list = []
    for _, row in df_anomalies.iterrows():
        details_list.append(
            f"- Process: {row['Process']} (PID: {row['PID']}), CPU: {row['CPU (%)']}%, "
            f"Memory: {row['Memory (%)']}%, Threads: {row['Threads']}, Risk: {row['Risk Score']}"
        )
    anomalies_str = "\n".join(details_list)
    
    prompt = (
        "You are an AI Security Analyst. Analyze these anomalous processes:\n"
        f"{anomalies_str}\n\n"
        "Provide a concise summary of the threats and specific actionable recommendations. Format the response in clear Markdown."
    )
    
    # Try querying Ollama
    model = st.session_state.get("ollama_model", "gemma")
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=5
        )
        if response.status_code == 200:
            res = response.json().get("response", "")
            if res:
                return res
    except Exception:
        pass
        
    return generate_dynamic_mock_report(df_anomalies)

def generate_security_report(df_anomalies):
    """
    Returns the security report as markdown text.
    Falls back to get_llm_explanation if Team 3 module is unavailable.
    """
    if not USE_MOCK:
        try:
            return real_generate_security_report(df_anomalies)
        except Exception:
            pass
    return get_llm_explanation(df_anomalies)
