"""
Seed the database with your threat taxonomy.

EDIT THIS FILE to add your own threat categories.
"""

import sys
sys.path.append(".")

import json
from backend.models.database import init_db, SessionLocal, Threat, ThreatLevel, TrendDirection

# ============================================================
# EDIT YOUR THREAT CATEGORIES HERE
# ============================================================

# THREATS = [
#     # Example structure - replace with your own categories
#     {
#         "name": "LLM-assisted pathogen design",
#         "category": "AI-Enabled Knowledge Access",
#         "description": "Large language models providing actionable guidance on pathogen design, synthesis routes, or enhancement strategies.",
#         "enabling_capabilities": [
#             "Advanced reasoning in biology",
#             "Knowledge of virology and microbiology",
#             "Wet lab protocol generation"
#         ],
#         "timeline_estimate": "Current - 12 months"
#     },
#     {
#         "name": "Protein structure prediction misuse",
#         "category": "Biological Design Tools",
#         "description": "AI tools that predict protein structure being used to design novel toxins or enhance pathogen proteins.",
#         "enabling_capabilities": [
#             "Accurate structure prediction (AlphaFold-level)",
#             "Inverse folding capabilities",
#             "Function prediction from structure"
#         ],
#         "timeline_estimate": "Current"
#     },
#     {
#         "name": "",
#         "category": "Biological Design Tools",
#         "description": "AI tools that predict protein structure being used to design novel toxins or enhance pathogen proteins.",
#         "enabling_capabilities": [
#             "Accurate structure prediction (AlphaFold-level)",
#             "Inverse folding capabilities",
#             "Function prediction from structure"
#         ],
#         "timeline_estimate": "Current"
#     }
#     # ADD YOUR OWN THREATS BELOW
#     # {
#     #     "name": "Your threat name",
#     #     "category": "Your category",
#     #     "description": "Description of the threat",
#     #     "enabling_capabilities": ["cap1", "cap2"],
#     #     "timeline_estimate": "X-Y months"
#     # },
# ]

THREATS = [
  {
    "name": "AI-Augmented Dual-Use Biotechnology Misuse",
    "category": "Augmenting Malicious Capabilities and Lowering Technical Barriers",
    "description": "AI-driven biotechnology, originally intended for medical and scientific progress, can be repurposed by malicious actors to develop harmful biological agents, lower technical barriers for dangerous experiments, and enable the automated discovery or synthesis of toxic compounds.",
    "enabling_capabilities": [
      "Large Language Models for protocol generation",
      "AI-powered synthetic biology and molecular design",
      "Automated laboratory workflows"
    ],
    "timeline_estimate": "12-36 months"
  },
  {
    "name": "AI-Enabled Pathogen Creation and Optimization",
    "category": "Pathogen Creation and Optimization Risks",
    "description": "AI models may be used to design, simulate, and optimize biological agents, accelerating evolutionary processes to create organisms or viral variants with enhanced transmissibility, resistance, or traits not anticipated by their creators, exceeding natural constraints and known countermeasures.",
    "enabling_capabilities": [
      "Generative protein and genome design tools",
      "AI-driven evolutionary simulation",
      "High-fidelity molecular modeling"
    ],
    "timeline_estimate": "24-48 months"
  },
  {
    "name": "Democratization of Bioengineering and Biothreats",
    "category": "Democratization and Accessibility Risks",
    "description": "AI and open biological tools democratize access to advanced biotechnological knowledge and experimentation. This accessibility broadens the pool of actors capable of biosafety breaches—including non-state entities and amateurs—lowering the barriers to bioterrorism and the creation of harmful agents.",
    "enabling_capabilities": [
      "Open-source genomics and LLM-powered design platforms",
      "Accessible AI biology models",
      "Automated, remote experimental tools"
    ],
    "timeline_estimate": "6-24 months"
  },
  {
    "name": "Opaque AI Models and Weak Governance",
    "category": "Governance and Transparency Risks",
    "description": "The 'black box' nature of many deep learning models creates traceability and transparency issues. Existing governance structures are ill-equipped for the dual-use challenges posed by AI in biosecurity, necessitating new frameworks for accountability and safety evaluation in critical applications.",
    "enabling_capabilities": [
      "Black-box deep learning systems",
      "Autonomous experimentation",
      "Weak regulatory oversight"
    ],
    "timeline_estimate": "12-36 months"
  },
  {
    "name": "AI-Enabled Evasion of Biosecurity Screening",
    "category": "Dual-Use Risk",
    "description": "AI-powered design platforms can generate DNA sequences or biological agents that evade current biosecurity and DNA synthesis screening methods, targeting regulatory gaps and enabling covert creation of novel threats.",
    "enabling_capabilities": [
      "AI DNA sequence design",
      "Model evasion techniques",
      "Screening-aware synthesis tools"
    ],
    "timeline_estimate": "6-18 months"
  },
  {
    "name": "Autonomous Pathogen Fitness Enhancement",
    "category": "Pathogen Optimization",
    "description": "AI-driven evolutionary algorithms can autonomously optimize and enhance the fitness of pathogens, increasing traits like transmissibility, environmental survivability, or immune evasion.",
    "enabling_capabilities": [
      "Genetic algorithm-optimized phenotype selection",
      "Automated protein simulation",
      "Fitness evaluation models"
    ],
    "timeline_estimate": "12-30 months"
  },
  {
    "name": "Malicious Controlled Expression of Toxins",
    "category": "Targeted Misuse of Biological Switches",
    "description": "AI-aided design of RNA switches or gene control systems may be maliciously adapted to trigger toxin production or virulence factors under specific conditions within benign organisms.",
    "enabling_capabilities": [
      "Modular synthetic biology control elements",
      "Automated pathway engineering",
      "Context-sensitive expression design"
    ],
    "timeline_estimate": "12-24 months"
  },
  {
    "name": "Adversarial Manipulation of AI Biosystems",
    "category": "Reliability and Adversarial Risk",
    "description": "Attackers can manipulate inputs or datasets to biological AI models, causing them to design harmful agents unintentionally or to generate false results that undermine biosafety.",
    "enabling_capabilities": [
      "Adversarial input generation",
      "Poisoned training datasets",
      "Undetected model exploitation"
    ],
    "timeline_estimate": "9-20 months"
  },
  {
    "name": "Automated Laboratory Malware Risks",
    "category": "Cyber-Physical Security",
    "description": "Automated laboratory systems can be compromised via AI-crafted DNA strands encoding malicious software triggers, leading to data theft, sabotage, or manipulation of bio-experiments.",
    "enabling_capabilities": [
      "Adversarial DNA design",
      "Malware-encoded nucleic acids",
      "Robotic workflow compromise"
    ],
    "timeline_estimate": "6-18 months"
  },
  {
    "name": "Premature Environmental Release of Engineered Microbes",
    "category": "Ecological Risk",
    "description": "AI-designed microbes released into the environment unintentionally due to governance failures can transfer engineered genes to wild organisms, threatening ecological systems and biosafety.",
    "enabling_capabilities": [
      "AI-assisted microbial engineering",
      "Poor biocontainment protocols",
      "Gene drive and mobile elements"
    ],
    "timeline_estimate": "18-36 months"
  }
]



def seed_threats():
    init_db()
    db = SessionLocal()
    
    added = 0
    for threat_data in THREATS:
        # Check if exists
        existing = db.query(Threat).filter(Threat.name == threat_data["name"]).first()
        if existing:
            print(f"Skipping (exists): {threat_data['name']}")
            continue
        
        threat = Threat(
            name=threat_data["name"],
            category=threat_data["category"],
            description=threat_data.get("description"),
            enabling_capabilities=json.dumps(threat_data.get("enabling_capabilities", [])),
            timeline_estimate=threat_data.get("timeline_estimate"),
            feasibility_score=1.0,
            threat_level=ThreatLevel.LOW,
            trend=TrendDirection.STABLE,
            confidence=0.5
        )
        db.add(threat)
        added += 1
        print(f"Added: {threat_data['name']}")
    
    db.commit()
    db.close()
    
    print(f"\nSeeded {added} new threats")


if __name__ == "__main__":
    seed_threats()