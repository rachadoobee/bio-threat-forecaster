import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

API_URL = "http://localhost:8000/api"

st.set_page_config(
    page_title="Biosecurity Threat Forecaster",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .threat-critical { background-color: #ff4b4b; padding: 10px; border-radius: 5px; color: white; }
    .threat-high { background-color: #ffa500; padding: 10px; border-radius: 5px; }
    .threat-medium { background-color: #ffd700; padding: 10px; border-radius: 5px; }
    .threat-low { background-color: #90EE90; padding: 10px; border-radius: 5px; }
    .big-metric { font-size: 48px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🧬 Biosecurity Threat Forecaster")
st.markdown("### Tracking AI-Enabled Biological Risks to Humanity")

# Sidebar actions
st.sidebar.header("⚡ Actions")

col1, col2 = st.sidebar.columns(2)
if col1.button("🔄 Ingest"):
    with st.spinner("Fetching..."):
        resp = requests.post(f"{API_URL}/ingest")
        if resp.ok:
            st.sidebar.success(f"Fetched {resp.json().get('fetched', 0)} items")

if col2.button("🤖 Classify"):
    with st.spinner("Classifying..."):
        resp = requests.post(f"{API_URL}/classify", params={"limit": 10})
        if resp.ok:
            st.sidebar.success(f"Classified {len(resp.json())} items")

if st.sidebar.button("📊 Update All Threat Assessments"):
    with st.spinner("Analyzing threats..."):
        resp = requests.post(f"{API_URL}/threats/update-all")
        if resp.ok:
            st.sidebar.success("All threats updated!")
            st.rerun()

st.sidebar.markdown("---")

# Fetch threats
resp = requests.get(f"{API_URL}/threats")
threats = resp.json() if resp.ok else []

# ============ MAIN DASHBOARD ============

if not threats:
    st.warning("⚠️ No threats defined yet. Go to the **Setup** tab to add threat categories.")
else:
    # Summary metrics row
    st.markdown("---")
    
    levels = [t.get("threat_level", "low") for t in threats]
    avg_score = sum(t.get("feasibility_score", 1) for t in threats) / len(threats)
    increasing = sum(1 for t in threats if "increasing" in t.get("trend", ""))
    
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Threats Tracked", len(threats))
    m2.metric("🔴 Critical", levels.count("critical"))
    m3.metric("🟠 High", levels.count("high"))
    m4.metric("📈 Increasing Trends", increasing)
    m5.metric("Avg Feasibility", f"{avg_score:.1f}/5")
    
    st.markdown("---")
    
    # ============ THREAT TIMELINE VISUALIZATION ============
    st.subheader("🕐 Threat Timeline Forecast")
    
    # Parse timeline estimates into approximate months
    def parse_timeline(t):
        tl = t.get("timeline_estimate", "Unknown")
        if not tl or tl == "Unknown":
            return 36  # Default to 3 years if unknown
        # Try to extract numbers
        import re
        nums = re.findall(r'\d+', tl)
        if nums:
            return int(nums[0])
        if "current" in tl.lower():
            return 0
        return 24
    
    timeline_data = []
    for t in threats:
        months = parse_timeline(t)
        timeline_data.append({
            "Threat": t["name"][:40] + "..." if len(t["name"]) > 40 else t["name"],
            "Months Until Feasible": months,
            "Feasibility Score": t.get("feasibility_score", 1),
            "Level": t.get("threat_level", "low"),
            "Category": t.get("category", "Unknown")
        })
    
    df_timeline = pd.DataFrame(timeline_data)
    
    # Color map
    color_map = {"critical": "#ff4b4b", "high": "#ffa500", "medium": "#ffd700", "low": "#90EE90"}
    df_timeline["Color"] = df_timeline["Level"].map(color_map)
    
    fig_timeline = px.bar(
        df_timeline.sort_values("Months Until Feasible"),
        x="Months Until Feasible",
        y="Threat",
        orientation="h",
        color="Level",
        color_discrete_map=color_map,
        title="Estimated Time Until Threat Becomes Feasible",
        hover_data=["Category", "Feasibility Score"]
    )
    fig_timeline.update_layout(height=max(400, len(threats) * 40), showlegend=True)
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    # ============ THREAT MATRIX ============
    st.markdown("---")
    st.subheader("⚠️ Risk Matrix: Feasibility vs Impact")
    
    # Create risk matrix scatter
    matrix_data = []
    for t in threats:
        score = t.get("feasibility_score", 1)
        level_impact = {"critical": 5, "high": 4, "medium": 3, "low": 2}.get(t.get("threat_level", "low"), 1)
        matrix_data.append({
            "Threat": t["name"],
            "Feasibility": score,
            "Impact": level_impact,
            "Level": t.get("threat_level", "low"),
            "Trend": t.get("trend", "stable"),
            "Category": t.get("category", "Unknown")
        })
    
    df_matrix = pd.DataFrame(matrix_data)
    
    fig_matrix = px.scatter(
        df_matrix,
        x="Feasibility",
        y="Impact",
        size=[40] * len(df_matrix),
        color="Level",
        color_discrete_map=color_map,
        hover_name="Threat",
        hover_data=["Category", "Trend"],
        title="Risk Matrix: Higher = More Dangerous"
    )
    
    # Add quadrant backgrounds
    fig_matrix.add_shape(type="rect", x0=3, x1=5, y0=3, y1=5, fillcolor="rgba(255,0,0,0.1)", line_width=0)
    fig_matrix.add_annotation(x=4, y=4.5, text="CRITICAL ZONE", showarrow=False, font=dict(color="red", size=14))
    
    fig_matrix.update_layout(
        xaxis_title="Feasibility Score (1-5)",
        yaxis_title="Impact Level (1-5)",
        height=500
    )
    fig_matrix.update_xaxes(range=[0, 5.5])
    fig_matrix.update_yaxes(range=[0, 5.5])
    
    st.plotly_chart(fig_matrix, use_container_width=True)
    
    # ============ CATEGORY BREAKDOWN ============
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Threats by Category")
        df_cat = pd.DataFrame(threats)
        if "category" in df_cat.columns:
            cat_counts = df_cat["category"].value_counts()
            fig_cat = px.pie(values=cat_counts.values, names=cat_counts.index, hole=0.4)
            st.plotly_chart(fig_cat, use_container_width=True)
    
    with col2:
        st.subheader("📈 Trend Distribution")
        if threats:
            trend_counts = pd.Series([t.get("trend", "stable") for t in threats]).value_counts()
            trend_colors = {
                "rapidly_increasing": "#ff4b4b",
                "increasing": "#ffa500", 
                "stable": "#808080",
                "decreasing": "#90EE90"
            }
            fig_trend = px.bar(
                x=trend_counts.index,
                y=trend_counts.values,
                color=trend_counts.index,
                color_discrete_map=trend_colors
            )
            fig_trend.update_layout(showlegend=False, xaxis_title="Trend", yaxis_title="Count")
            st.plotly_chart(fig_trend, use_container_width=True)
    
    # ============ DETAILED THREAT CARDS ============
    st.markdown("---")
    st.subheader("🔍 Detailed Threat Analysis")
    
    # Sort by risk (feasibility * impact)
    sorted_threats = sorted(threats, key=lambda x: x.get("feasibility_score", 1) * 
                           {"critical": 5, "high": 4, "medium": 3, "low": 2}.get(x.get("threat_level", "low"), 1),
                           reverse=True)
    
    for threat in sorted_threats:
        level = threat.get("threat_level", "low")
        level_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(level, "⚪")
        trend_emoji = {"rapidly_increasing": "⬆️⬆️", "increasing": "⬆️", "stable": "➡️", "decreasing": "⬇️"}.get(threat.get("trend", "stable"), "➡️")
        
        with st.expander(f"{level_emoji} **{threat['name']}** | Score: {threat.get('feasibility_score', 0):.1f}/5 | {trend_emoji} | Timeline: {threat.get('timeline_estimate', 'Unknown')}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Feasibility", f"{threat.get('feasibility_score', 0):.1f}/5")
            c2.metric("Confidence", f"{threat.get('confidence', 0):.0%}")
            c3.metric("Related Papers", threat.get("recent_items_count", 0))
            
            st.markdown(f"**Category:** {threat.get('category', 'N/A')}")
            st.markdown(f"**Description:** {threat.get('description', 'No description')}")
            st.markdown(f"**Last Updated:** {threat.get('last_updated', 'Never')}")
            
            # Fetch detailed info with papers
            if st.button(f"📄 Show Related Papers ({threat.get('recent_items_count', 0)})", key=f"papers_{threat['id']}"):
                with st.spinner("Loading papers..."):
                    detail_resp = requests.get(f"{API_URL}/threats/{threat['id']}")
                    if detail_resp.ok:
                        detail = detail_resp.json()
                        papers = detail.get("related_papers", [])
                        
                        if papers:
                            st.markdown("---")
                            st.markdown("### 📚 Related Papers")
                            
                            for paper in papers:
                                impact_colors = {
                                    "step_change": "🔴",
                                    "significant": "🟠", 
                                    "incremental": "🟡",
                                    "none": "⚪"
                                }
                                impact_icon = impact_colors.get(paper.get("impact_level", "none"), "⚪")
                                
                                with st.container():
                                    st.markdown(f"**{impact_icon} {paper['title']}**")
                                    
                                    col1, col2 = st.columns([3, 1])
                                    with col1:
                                        if paper.get('authors'):
                                            st.text(f"Authors: {paper['authors'][:100]}")
                                        if paper.get('published_date'):
                                            st.text(f"Published: {paper['published_date'][:10]}")
                                        if paper.get('url'):
                                            st.markdown(f"🔗 [View Paper]({paper['url']})")
                                    
                                    with col2:
                                        st.metric("Impact", paper.get('impact_level', 'N/A'))
                                        if paper.get('relevance_score'):
                                            st.metric("Relevance", f"{paper['relevance_score']:.1%}")
                                    
                                    if paper.get('classification_reasoning'):
                                        with st.expander("Why this is relevant"):
                                            st.write(paper['classification_reasoning'])
                                    
                                    if paper.get('capabilities_identified'):
                                        caps = paper['capabilities_identified']
                                        if caps and caps != "[]":
                                            st.text(f"Capabilities: {caps}")
                                    
                                    st.markdown("---")
                        else:
                            st.info("No related papers yet. Run ingestion and classification to find relevant papers.")
            
            if st.button(f"🔄 Update Assessment", key=f"upd_{threat['id']}"):
                with st.spinner("Analyzing..."):
                    resp = requests.post(f"{API_URL}/threats/{threat['id']}/update")
                    if resp.ok:
                        st.success("Updated!")
                        st.rerun()

# ============ TABS FOR OTHER FUNCTIONS ============
st.markdown("---")
tab1, tab2, tab3, tab4 = st.tabs(["📰 Recent Items", "📊 Papers by Threat", "➕ Add Item", "⚙️ Setup"])

with tab1:
    st.subheader("Recently Ingested Items")
    
    col1, col2 = st.columns(2)
    show_relevant = col1.checkbox("Show only relevant", value=True)
    limit = col2.slider("Number of items", 10, 100, 30)
    
    resp = requests.get(f"{API_URL}/items", params={"relevant_only": show_relevant, "limit": limit})
    if resp.ok:
        items = resp.json()
        if items:
            for item in items:
                rel_icon = "✅" if item.get("is_relevant") else "❌" if item.get("is_relevant") is False else "❓"
                impact_icon = {"step_change": "🔴", "significant": "🟠", "incremental": "🟡"}.get(item.get("impact_level"), "⚪")
                
                with st.expander(f"{rel_icon} {impact_icon} {item['title'][:80]}"):
                    if item.get("url"):
                        st.markdown(f"🔗 [View Source]({item['url']})")
                    st.text(f"Impact: {item.get('impact_level', 'N/A')}")
                    st.text(f"Classified: {'Yes' if item.get('classified') else 'No'}")
                    st.text(f"Fetched: {item.get('fetched_at', 'Unknown')[:10]}")
        else:
            st.info("No items yet. Click 'Ingest' in the sidebar.")

with tab2:
    st.subheader("📊 Papers by Threat Category")
    
    if threats:
        # Threat selector
        threat_names = {t["id"]: t["name"] for t in threats}
        selected_threat_id = st.selectbox(
            "Select a threat to see related papers:",
            options=list(threat_names.keys()),
            format_func=lambda x: threat_names[x]
        )
        
        if selected_threat_id:
            with st.spinner("Loading papers..."):
                detail_resp = requests.get(f"{API_URL}/threats/{selected_threat_id}")
                
                if detail_resp.ok:
                    detail = detail_resp.json()
                    papers = detail.get("related_papers", [])
                    
                    # Show threat info
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Feasibility", f"{detail['feasibility_score']:.1f}/5")
                    col2.metric("Threat Level", detail['threat_level'])
                    col3.metric("Timeline", detail['timeline_estimate'])
                    col4.metric("Papers", len(papers))
                    
                    st.markdown("---")
                    st.markdown(f"**Description:** {detail['description']}")
                    
                    # Show papers
                    if papers:
                        st.markdown("---")
                        st.markdown(f"### {len(papers)} Related Papers")
                        
                        # Sort options
                        sort_by = st.radio("Sort by:", ["Relevance", "Impact", "Date"], horizontal=True)
                        
                        if sort_by == "Relevance":
                            papers = sorted(papers, key=lambda x: x.get("relevance_score", 0), reverse=True)
                        elif sort_by == "Impact":
                            impact_order = {"step_change": 3, "significant": 2, "incremental": 1, "none": 0}
                            papers = sorted(papers, key=lambda x: impact_order.get(x.get("impact_level", "none"), 0), reverse=True)
                        elif sort_by == "Date":
                            papers = sorted(papers, key=lambda x: x.get("published_date", ""), reverse=True)
                        
                        for i, paper in enumerate(papers, 1):
                            impact_colors = {"step_change": "🔴", "significant": "🟠", "incremental": "🟡", "none": "⚪"}
                            impact_icon = impact_colors.get(paper.get("impact_level", "none"), "⚪")
                            
                            with st.container():
                                st.markdown(f"#### {i}. {impact_icon} {paper['title']}")
                                
                                c1, c2, c3 = st.columns(3)
                                c1.metric("Impact", paper.get('impact_level', 'N/A'))
                                if paper.get('relevance_score'):
                                    c2.metric("Relevance", f"{paper['relevance_score']:.0%}")
                                if paper.get('published_date'):
                                    c3.metric("Published", paper['published_date'][:10])
                                
                                if paper.get('authors'):
                                    st.text(f"👥 {paper['authors'][:150]}")
                                
                                if paper.get('url'):
                                    st.markdown(f"🔗 [View Paper]({paper['url']})")
                                
                                if paper.get('classification_reasoning'):
                                    with st.expander("📝 Why this paper is relevant"):
                                        st.write(paper['classification_reasoning'])
                                
                                if paper.get('capabilities_identified') and paper['capabilities_identified'] != "[]":
                                    st.info(f"🔬 Capabilities: {paper['capabilities_identified']}")
                                
                                st.markdown("---")
                    else:
                        st.info("No papers linked to this threat yet. Run ingestion and classification to find relevant papers.")
    else:
        st.info("No threats defined yet. Add threats in the Setup tab.")

with tab4:
    st.subheader("Add Item Manually")
    with st.form("manual_item"):
        title = st.text_input("Title")
        content = st.text_area("Content (abstract or description)", height=150)
        url = st.text_input("URL (optional)")
        
        if st.form_submit_button("Add & Classify"):
            if title and content:
                resp = requests.post(f"{API_URL}/ingest/manual", json={"title": title, "content": content, "url": url})
                if resp.ok:
                    item_id = resp.json()["id"]
                    class_resp = requests.post(f"{API_URL}/classify/{item_id}")
                    if class_resp.ok:
                        st.success("Added and classified!")
                        st.json(class_resp.json())

with tab3:
    st.subheader("Add New Threat Category")
    with st.form("new_threat"):
        name = st.text_input("Threat Name")
        category = st.selectbox("Category", [
            "AI-Enabled Knowledge Access",
            "Biological Design Tools", 
            "Dual-Use Research",
            "Biosecurity Evasion",
            "Enabling Technologies",
            "Other"
        ])
        description = st.text_area("Description")
        capabilities = st.text_input("Enabling Capabilities (comma-separated)")
        timeline = st.text_input("Timeline Estimate (e.g., '6-12 months')")
        
        if st.form_submit_button("Add Threat"):
            if name:
                caps = [c.strip() for c in capabilities.split(",")] if capabilities else []
                resp = requests.post(f"{API_URL}/threats", json={
                    "name": name, "category": category, "description": description,
                    "enabling_capabilities": caps, "timeline_estimate": timeline
                })
                if resp.ok:
                    st.success(f"Added: {name}")
                    st.rerun()
    
    st.markdown("---")
    st.subheader("Current Data Sources")
    resp = requests.get(f"{API_URL}/sources")
    if resp.ok and resp.json():
        st.dataframe(pd.DataFrame(resp.json()), use_container_width=True)