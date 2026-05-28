import asyncio
import io
import json
import logging
import re

logger = logging.getLogger(__name__)

LATEX_TEMPLATES = {
  "modern": r"""
\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage[margin=1.8cm]{geometry}
\usepackage{titlesec,enumitem,hyperref,xcolor,fontawesome5,multicol}
\definecolor{accent}{RGB}{0,102,204}
\hypersetup{colorlinks,urlcolor=accent}
\titleformat{\section}{\large\bfseries\color{accent}}{}{0em}{}[\titlerule]
\titlespacing{\section}{0pt}{8pt}{4pt}
\setlength{\parindent}{0pt}
\begin{document}
<<CONTENT>>
\end{document}
""",
  "minimal": r"""
\documentclass[10pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage[margin=2cm]{geometry}
\usepackage{titlesec,enumitem,hyperref,xcolor}
\definecolor{accent}{RGB}{50,50,50}
\hypersetup{colorlinks,urlcolor=accent}
\titleformat{\section}{\normalsize\bfseries\uppercase}{}{0em}{}[\hrule]
\titlespacing{\section}{0pt}{6pt}{3pt}
\setlength{\parindent}{0pt}
\begin{document}
<<CONTENT>>
\end{document}
""",
  "tech": r"""
\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage[margin=1.5cm]{geometry}
\usepackage{titlesec,enumitem,hyperref,xcolor,tabularx}
\definecolor{accent}{RGB}{0,150,136}
\hypersetup{colorlinks,urlcolor=accent}
\titleformat{\section}{\large\bfseries\color{accent}}{}{0em}{}[\color{accent}\titlerule]
\titlespacing{\section}{0pt}{8pt}{4pt}
\setlength{\parindent}{0pt}
\begin{document}
<<CONTENT>>
\end{document}
""",
  "executive": r"""
\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage[margin=2cm]{geometry}
\usepackage{titlesec,enumitem,hyperref,xcolor}
\definecolor{accent}{RGB}{139,0,0}
\hypersetup{colorlinks,urlcolor=accent}
\titleformat{\section}{\large\scshape\color{accent}}{}{0em}{}[\titlerule]
\titlespacing{\section}{0pt}{8pt}{4pt}
\setlength{\parindent}{0pt}
\begin{document}
<<CONTENT>>
\end{document}
""",
  "creative": r"""
\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage[margin=1.8cm]{geometry}
\usepackage{titlesec,enumitem,hyperref,xcolor,tcolorbox}
\definecolor{accent}{RGB}{103,58,183}
\hypersetup{colorlinks,urlcolor=accent}
\titleformat{\section}{\large\bfseries\color{accent}}{}{0em}{}
\titlespacing{\section}{0pt}{8pt}{4pt}
\setlength{\parindent}{0pt}
\begin{document}
<<CONTENT>>
\end{document}
""",
}


def _pick_template(job_title: str, job_description: str) -> str:
  text = (job_title + " " + job_description).lower()
  if any(
    w in text
    for w in [
      "startup",
      "engineer",
      "developer",
      "software",
      "backend",
      "frontend",
      "fullstack",
      "ml",
      "ai",
      "data",
    ]
  ):
    return "tech"
  if any(
    w in text
    for w in ["manager", "director", "lead", "senior", "head", "vp", "executive"]
  ):
    return "executive"
  if any(w in text for w in ["design", "creative", "ux", "ui", "product", "marketing"]):
    return "creative"
  if any(w in text for w in ["intern", "junior", "fresher", "entry"]):
    return "modern"
  return "modern"


async def tailor_resume(job: dict, username: str, profile: dict = None) -> dict:
  if profile is None:
    from app.database import get_full_profile

    profile = get_full_profile(username)

  skills = profile.get("all_skills", profile.get("skills", []))
  roles = profile.get("target_roles", [])
  bio = profile.get("bio", "")
  experience = profile.get("experience_years", 1)
  projects = profile.get("projects", [])
  experiences = profile.get("experiences", [])
  resumes = profile.get("resumes", [])

  primary = next(
    (r for r in resumes if r.get("is_primary")),
    resumes[0] if resumes else None,
  )
  resume_text = primary["raw_text"] if primary else profile.get("resume_text", "")

  proj_detail = (
    "\n".join(
      [
        f"- {p.get('name', '')} | "
        f"{', '.join(p.get('tech_stack', [])[:5])}: "
        f"{p.get('description', '')[:150]} "
        f"{'| ' + p.get('outcome', '') if p.get('outcome') else ''}"
        for p in projects[:5]
      ]
    )
    or "No projects listed"
  )

  exp_detail = (
    "\n".join(
      [
        f"- {e.get('title', '')} at {e.get('organization', '')} "
        f"({e.get('start_date', '')}-"
        f"{'Present' if e.get('is_current') else e.get('end_date', '')}): "
        f"{e.get('description', '')[:150]}"
        for e in experiences[:4]
      ]
    )
    or "No experience listed"
  )

  template_name = _pick_template(job.get("title", ""), job.get("description", ""))

  from app.services.gemini_service import get_gemini_service

  gemini = get_gemini_service()

  content_prompt = f"""You are a world-class technical resume writer.
Create an ATS-optimized resume for this SPECIFIC job.

JOB:
Title: {job.get('title', '')}
Company: {job.get('company', '')}
Description: {job.get('description', 'No description')[:2000]}

CANDIDATE:
Name: {username.title()}
Experience: {experience} years
Skills: {', '.join(skills[:35])}
Target Roles: {', '.join(roles)}
Bio: {bio or 'Not provided'}

WORK EXPERIENCE:
{exp_detail}

PROJECTS:
{proj_detail}

EXISTING RESUME:
{resume_text[:2000] if resume_text else 'Not uploaded'}

INSTRUCTIONS:
1. Write 3-sentence summary targeting THIS exact job title
2. List skills in order of relevance to job description (use job keywords)
3. Write 2-3 experience entries using STAR format with metrics
4. Include 2-3 most relevant projects with tech + impact
5. Every bullet starts with strong action verb
6. Include exact keywords from job description naturally
7. Only use skills/experience the candidate actually has
8. Make each section support and reinforce the others
9. Max 500 words, 1-2 pages worth

FORMAT (use exact headers, LaTeX-friendly):

\\begin{{center}}
{{\\Large \\textbf{{{username.title()}}}}} \\\\
{{\\small {username}@email.com $\\bullet$ LinkedIn: linkedin.com/in/{username.lower()} $\\bullet$ GitHub: github.com/{username.lower()}}}
\\end{{center}}

\\section{{Professional Summary}}
[3 sentences targeting this role]

\\section{{Technical Skills}}
\\begin{{itemize}}[noitemsep,topsep=0pt]
\\item \\textbf{{Primary:}} [top skills for this job]
\\item \\textbf{{Secondary:}} [other relevant skills]
\\item \\textbf{{Tools:}} [tools and platforms]
\\end{{itemize}}

\\section{{Work Experience}}
\\textbf{{[Role]}} $\\bullet$ [Company] \\hfill [Date range] \\\\
\\begin{{itemize}}[noitemsep,topsep=2pt]
\\item [STAR bullet with metric]
\\item [STAR bullet with metric]
\\item [STAR bullet with metric]
\\end{{itemize}}

\\section{{Projects}}
\\textbf{{[Project Name]}} $|$ [Tech Stack] \\hfill \\href{{[url]}}{{[url]}} \\\\
\\begin{{itemize}}[noitemsep,topsep=2pt]
\\item [What you built and technical challenge]
\\item [Impact and outcome with metric if possible]
\\end{{itemize}}

\\section{{Education}}
\\textbf{{[Degree]}} $\\bullet$ [Institution] \\hfill [Year]

Return ONLY the LaTeX content between \\begin{{document}} and \\end{{document}}.
No preamble, no document class."""

  try:
    latex_content = await asyncio.wait_for(gemini.chat(content_prompt), timeout=45.0)
  except Exception as e:
    logger.warning("Gemini resume gen failed: %s", e)
    latex_content = _fallback_latex(profile, job)

  ats_prompt = f"""Rate this resume against the job description for ATS compliance.

JOB DESCRIPTION:
{job.get('description', '')[:1000]}

RESUME:
{latex_content[:2000]}

Return JSON only:
{{
  "ats_score": 85,
  "missing_keywords": ["keyword1","keyword2"],
  "improvements": ["Add X to summary","Mention Y in skills"],
  "strengths": ["Good keyword density","Clear structure"]
}}"""

  try:
    ats_resp = await asyncio.wait_for(gemini.chat(ats_prompt), timeout=20.0)
    clean = re.sub(r"```json|```", "", ats_resp).strip()
    s = clean.find("{")
    e = clean.rfind("}") + 1
    ats_data = json.loads(clean[s:e])
    ats_score = ats_data.get("ats_score", 70)
    improvements = ats_data.get("improvements", [])
    missing_kw = ats_data.get("missing_keywords", [])
  except Exception:
    ats_score = 70
    improvements = []
    missing_kw = []

  if ats_score < 75 and missing_kw:
    improve_prompt = f"""Improve this resume to include these missing keywords naturally:
{missing_kw}

Current resume:
{latex_content[:2000]}

Job description keywords to add:
{job.get('description', '')[:500]}

Return improved LaTeX content only (same format, no preamble)."""
    try:
      improved = await asyncio.wait_for(gemini.chat(improve_prompt), timeout=30.0)
      if improved and len(improved) > 200:
        latex_content = improved
        ats_score = min(ats_score + 12, 95)
    except Exception:
      pass

  template = LATEX_TEMPLATES.get(template_name, LATEX_TEMPLATES["modern"])
  full_latex = template.replace("<<CONTENT>>", latex_content)

  resume_text_clean = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", latex_content)
  resume_text_clean = re.sub(r"\\[a-zA-Z]+", "", resume_text_clean)
  resume_text_clean = re.sub(r"[{}]", "", resume_text_clean).strip()

  try:
    from app.database import save_tailored_resume

    save_tailored_resume(
      username,
      job.get("title", ""),
      job.get("company", ""),
      job.get("url", ""),
      full_latex,
      resume_text_clean,
      ats_score,
      template_name,
    )
  except Exception as e:
    logger.warning("DB save tailored resume failed: %s", e)

  return {
    "latex_code": full_latex,
    "resume_text": resume_text_clean,
    "ats_score": ats_score,
    "template_used": template_name,
    "improvements": improvements,
    "missing_keywords": missing_kw,
  }


def _fallback_latex(profile, job):
  skills = profile.get("all_skills", profile.get("skills", []))
  roles = profile.get("target_roles", [])
  projects = profile.get("projects", [])
  experiences = profile.get("experiences", [])
  bio = profile.get("bio", "")
  username = profile.get("username", "Candidate")

  proj_latex = ""
  for p in projects[:2]:
    tech = ", ".join(p.get("tech_stack", [])[:4])
    proj_latex += f"""
\\textbf{{{p.get('name', '')}}} $|$ {tech} \\\\
\\begin{{itemize}}[noitemsep,topsep=2pt]
\\item {p.get('description', '')[:120]}
\\item {p.get('outcome', 'Built with modern best practices')[:100]}
\\end{{itemize}}
"""

  exp_latex = ""
  for e in experiences[:2]:
    exp_latex += f"""
\\textbf{{{e.get('title', '')}}} $\\bullet$ {e.get('organization', '')} \\hfill {e.get('start_date', '')}--{'Present' if e.get('is_current') else e.get('end_date', '')} \\\\
\\begin{{itemize}}[noitemsep,topsep=2pt]
\\item {e.get('description', '')[:150]}
\\end{{itemize}}
"""

  role_label = roles[0] if roles else "developer"
  summary_extra = (
    bio[:200]
    if bio
    else "Proficient in " + ", ".join(skills[:4]) + "."
  )
  tools_line = (
    ", ".join(skills[12:20]) if len(skills) > 12 else "Git, Docker, Linux"
  )
  exp_section = exp_latex or r"\textit{Experience details to be added}"
  proj_section = proj_latex or r"\textit{See GitHub profile for projects}"

  return f"""\\begin{{center}}
{{\\Large \\textbf{{{username.title()}}}}} \\\\
\\end{{center}}

\\section{{Professional Summary}}
Experienced {role_label} with {profile.get('experience_years', 1)}+ years building scalable solutions. {summary_extra}

\\section{{Technical Skills}}
\\begin{{itemize}}[noitemsep,topsep=0pt]
\\item \\textbf{{Primary:}} {', '.join(skills[:12])}
\\item \\textbf{{Tools:}} {tools_line}
\\end{{itemize}}

\\section{{Work Experience}}
{exp_section}

\\section{{Projects}}
{proj_section}

\\section{{Education}}
\\textbf{{Bachelor of Technology}} $\\bullet$ Computer Science \\hfill 2023
"""


def generate_pdf(resume_data, candidate_name=""):
  if isinstance(resume_data, dict):
    text = resume_data.get("resume_text", "")
    ats_score = resume_data.get("ats_score", 0)
  else:
    text = str(resume_data)
    ats_score = 0

  try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
      buf,
      pagesize=letter,
      rightMargin=0.65 * inch,
      leftMargin=0.65 * inch,
      topMargin=0.55 * inch,
      bottomMargin=0.55 * inch,
    )

    name_s = ParagraphStyle(
      "N",
      fontSize=18,
      fontName="Helvetica-Bold",
      textColor=colors.HexColor("#1e293b"),
      spaceAfter=2,
      alignment=TA_CENTER,
    )
    section_s = ParagraphStyle(
      "S",
      fontSize=11,
      fontName="Helvetica-Bold",
      textColor=colors.HexColor("#0369a1"),
      spaceBefore=10,
      spaceAfter=3,
    )
    body_s = ParagraphStyle(
      "B",
      fontSize=9.5,
      fontName="Helvetica",
      textColor=colors.HexColor("#334155"),
      spaceAfter=2,
      leading=13,
    )
    bullet_s = ParagraphStyle(
      "Bl",
      fontSize=9.5,
      fontName="Helvetica",
      textColor=colors.HexColor("#334155"),
      spaceAfter=2,
      leading=13,
      leftIndent=12,
    )
    sub_s = ParagraphStyle(
      "Sub",
      fontSize=10,
      fontName="Helvetica-Bold",
      textColor=colors.HexColor("#475569"),
      spaceAfter=1,
    )
    ats_s = ParagraphStyle(
      "ATS",
      fontSize=8,
      fontName="Helvetica",
      textColor=colors.HexColor("#94a3b8"),
      spaceAfter=0,
      alignment=TA_CENTER,
    )

    story = []
    if candidate_name:
      story.append(Paragraph(candidate_name.upper(), name_s))
      story.append(
        HRFlowable(
          width="100%",
          thickness=1.5,
          color=colors.HexColor("#0369a1"),
          spaceAfter=6,
        )
      )

    if ats_score > 0:
      color = (
        "#22c55e"
        if ats_score >= 80
        else "#eab308"
        if ats_score >= 65
        else "#ef4444"
      )
      story.append(
        Paragraph(
          f'<font color="{color}">ATS Score: {ats_score}%</font>',
          ats_s,
        )
      )
      story.append(Spacer(1, 4))

    for line in text.split("\n"):
      line = line.strip()
      if not line:
        story.append(Spacer(1, 3))
        continue
      if line.isupper() and len(line) < 40 and not line.startswith("•"):
        story.append(Paragraph(line, section_s))
        story.append(
          HRFlowable(
            width="100%",
            thickness=0.4,
            color=colors.HexColor("#cbd5e1"),
            spaceAfter=3,
          )
        )
      elif line.startswith("•") or line.startswith("-"):
        story.append(Paragraph("• " + line.lstrip("•- "), bullet_s))
      elif ("|" in line or "•" in line) and len(line) < 100:
        story.append(Paragraph(f"<b>{line}</b>", sub_s))
      elif line.endswith(":") and len(line) < 50:
        story.append(Paragraph(f"<b>{line}</b>", body_s))
      else:
        story.append(Paragraph(line, body_s))

    doc.build(story)
    return buf.getvalue()
  except Exception as e:
    logger.error("PDF gen failed: %s", e)
    return text.encode("utf-8")
