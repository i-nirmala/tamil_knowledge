"""Code Bloom UI styling only. Core RAG/model files under src/ are untouched."""
from pathlib import Path
import base64
import streamlit as st


def _image_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('utf-8')}"


CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+Tamil:wght@400;500;600;700;800&display=swap');
:root{--blue:#1557a6;--blue2:#2d74d6;--blue-soft:#eef5ff;--ink:#17324d;--muted:#6f8091;--line:#dce7f3;--bg:#f5f8fc;--card:#fff;--shadow:0 14px 40px rgba(26,63,105,.10)}
html,body,[class*="css"]{font-family:Inter,"Noto Sans Tamil","Nirmala UI",sans-serif}
.stApp{background:linear-gradient(180deg,#f7faff 0%,#f3f7fc 100%);color:var(--ink)}
.block-container{padding:1.25rem 2rem 3.5rem;max-width:1450px}
#MainMenu,footer,header{visibility:hidden}
.stTextInput input,.stTextArea textarea,.stSelectbox div[data-baseweb="select"]{background:#fff!important;color:#4a3328!important;border-color:#cbd9e8!important;border-radius:12px!important}
.stTextInput input:focus,.stTextArea textarea:focus{border-color:#4d8ddd!important;box-shadow:0 0 0 2px rgba(45,116,214,.12)!important}
.stButton>button{border-radius:11px;border:1px solid #cbd9e8;background:#fff;color:#17446f;font-weight:700;transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease}
.stButton>button:hover{transform:translateY(-2px);border-color:#6c9bd1;box-shadow:0 8px 22px rgba(31,91,153,.12);color:#0d4f9c}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#1557a6,#2d74d6);color:#fff;border:0;box-shadow:0 10px 24px rgba(21,87,166,.22)}
[data-testid="stSidebar"]{background:#fff;border-right:1px solid #dce7f3}
[data-testid="stSidebar"] .block-container{padding:1rem .85rem}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:14px;padding:.75rem;box-shadow:0 5px 18px rgba(24,66,112,.05)}

/* welcome reference: full CICT photo + centered glass card */
.cb-welcome{min-height:calc(100vh - 2.5rem);margin:-.2rem -1rem -2rem;position:relative;overflow:hidden;display:flex;align-items:center;justify-content:center;background:#dfe9f5}
.cb-welcome-bg{position:absolute;inset:0;background-size:cover;background-position:center;filter:brightness(.92) saturate(1.04);transform:scale(1.015);animation:cb-bg-zoom 14s ease-in-out infinite alternate}
.cb-welcome-overlay{position:absolute;inset:0;background:linear-gradient(90deg,rgba(10,34,59,.34),rgba(15,47,78,.12),rgba(10,34,59,.25))}
.cb-welcome-content{position:relative;z-index:2;width:min(820px,90%);padding:2.7rem 3.2rem;border:1px solid rgba(255,255,255,.42);border-radius:28px;background:rgba(255,255,255,.20);backdrop-filter:blur(17px);-webkit-backdrop-filter:blur(17px);box-shadow:0 25px 70px rgba(4,27,52,.22);color:#fff;animation:cb-card-in .7s ease both}
.cb-welcome-hit{position:absolute;inset:0;z-index:1;cursor:pointer}
.cb-welcome-content>*{position:relative;z-index:3}
.cb-brand-line{display:flex;gap:.65rem;align-items:center;color:#fff;font-weight:800;letter-spacing:.12em;font-size:.78rem;text-transform:uppercase}
.cb-brand-mark{width:34px;height:34px;display:grid;place-items:center;border:1px solid rgba(255,255,255,.62);border-radius:10px;color:#fff;font-size:1rem;background:rgba(255,255,255,.10)}
.cb-welcome .cb-eyebrow{margin-top:2rem;color:rgba(255,255,255,.82);font-weight:800;letter-spacing:.14em;font-size:.72rem}
.cb-welcome h1{font-family:"Noto Sans Tamil",Inter,sans-serif;font-size:clamp(2.8rem,6vw,5.4rem);line-height:1.02;margin:.55rem 0 .75rem;letter-spacing:-.05em;color:#fff}
.cb-welcome h1 span{color:#fff}
.cb-welcome p{max-width:760px;color:rgba(255,255,255,.91);font-size:1rem;line-height:1.7;margin:0}
.cb-feature-row{display:flex;flex-wrap:wrap;gap:.55rem;margin:1.5rem 0 1.7rem}
.cb-feature{border:1px solid rgba(255,255,255,.28);background:rgba(11,33,54,.24);backdrop-filter:blur(8px);padding:.48rem .7rem;border-radius:999px;color:#fff;font-size:.76rem}
.cb-welcome-actions{display:flex;gap:.7rem;position:relative;z-index:4}
.cb-welcome-actions .stButton>button{background:#173b59;color:#fff;border:0;min-width:125px}
.cb-enter-hint{display:flex;align-items:center;gap:.7rem;color:#fff;margin-top:1.1rem;font-size:.82rem}
.cb-enter-hint small{display:block;color:rgba(255,255,255,.72);margin-top:.15rem}
.cb-enter-orb{width:30px;height:30px;border-radius:50%;display:grid;place-items:center;background:rgba(255,255,255,.17);animation:cb-pulse 1.8s infinite}

/* centered white login */
.cb-auth-center{min-height:calc(100vh - 3rem);display:flex;align-items:center;justify-content:center;padding:1rem 0}
.cb-auth-card{width:min(510px,94vw);background:#fff;border:1px solid #decfe5;border-radius:24px;box-shadow:0 22px 65px rgba(23,57,93,.12);overflow:hidden;animation:cb-card-in .55s ease both}
.cb-auth-card-top{text-align:left;padding:2rem 2.25rem 1rem}
.cb-auth-card-top .cb-brand-line{color:#24435f;letter-spacing:.08em}.cb-auth-card-top .cb-brand-mark{color:#6f4d7f;border-color:#bcd0e7;background:#eef5ff}
.cb-auth-kicker{margin-top:1.35rem;color:#8b6aa8;font-size:.68rem;font-weight:800;letter-spacing:.15em}
.cb-auth-card-top h2{font:800 clamp(1.7rem,4vw,2.35rem) "Noto Sans Tamil",Inter,sans-serif;line-height:1.22;margin:.55rem 0 .45rem;color:#4a3328}
.cb-auth-card-top h2 span{color:#6f4d7f}.cb-auth-card-top p{color:#78675e;line-height:1.65;font-size:.9rem;margin:0}
.cb-auth-form{padding:1rem 2.25rem 2rem}.cb-auth-form [data-testid="stRadio"]{justify-content:center}.cb-auth-form .stTabs [data-baseweb="tab-list"]{justify-content:center}.cb-auth-form .stTabs [data-baseweb="tab"]{padding:0 1rem}.cb-auth-form .stCaption{text-align:center}

/* dashboard */
.cb-topbar{display:flex;justify-content:space-between;align-items:center;gap:1rem;padding:.7rem 1rem;margin-bottom:1rem;border:1px solid var(--line);background:#fff;border-radius:14px;box-shadow:0 6px 22px rgba(26,63,105,.05)}
.cb-topbrand{display:flex;align-items:center;gap:.7rem}.cb-topbrand .mark{width:34px;height:34px;display:grid;place-items:center;border-radius:10px;background:#eef5ff;color:#6f4d7f}.cb-topbrand b{font-size:.95rem}.cb-topbrand small{color:#78675e;display:block}
.cb-header{padding:1.5rem 1.7rem;border:1px solid var(--line);border-radius:18px;background:linear-gradient(135deg,#fffdfb,#f3edf7);box-shadow:var(--shadow);margin-bottom:1.1rem}.cb-header h1{font:800 2rem "Noto Sans Tamil",Inter,sans-serif;margin:0;color:#4a3328}.cb-header p{margin:.3rem 0 0;color:#63768a}.cb-header .cb-motto{margin-top:.55rem;color:#8b6aa8;font-size:.82rem;font-weight:600}
.cb-dashboard-hero{padding:1.8rem 2rem;background:linear-gradient(135deg,#1557a6,#2d74d6);color:#fff;border-radius:20px;box-shadow:0 18px 40px rgba(111,77,127,.18);margin-bottom:1.1rem}.cb-dashboard-kicker{font-size:.7rem;letter-spacing:.15em;font-weight:800;opacity:.82}.cb-dashboard-hero h2{font:800 2.15rem "Noto Sans Tamil",Inter,sans-serif;margin:.35rem 0}.cb-dashboard-hero p{max-width:850px;margin:0;line-height:1.7;color:rgba(255,255,255,.9)}
.cb-dashboard-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.8rem;margin-bottom:1.1rem}.cb-stat-card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:1rem 1.1rem;box-shadow:0 7px 22px rgba(26,63,105,.05)}.cb-stat-icon{display:block;color:#8b6aa8;font-size:1.2rem}.cb-stat-value{display:block;font-size:1.65rem;font-weight:800;color:#4a3328;margin-top:.2rem}.cb-stat-label{display:block;color:#78675e;font-size:.72rem;margin-top:.2rem}
.cb-section-label{display:flex;justify-content:space-between;align-items:center;margin:1.15rem .1rem .65rem;color:#4a3328}.cb-section-label span{color:#8291a1;font-size:.72rem}
.cb-culture-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.85rem}.cb-culture-card{background:#fff;border:1px solid var(--line);border-radius:17px;overflow:hidden;box-shadow:0 8px 25px rgba(92,65,52,.07);transition:.3s;cursor:pointer}.cb-culture-card:hover{transform:translateY(-7px);border-color:#c4a8d1;box-shadow:0 16px 35px rgba(92,65,52,.13)}.cb-culture-image{height:170px;overflow:hidden;background:#f1e9f4}.cb-culture-image img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .5s ease;animation:cb-image-float 5s ease-in-out infinite alternate}.cb-culture-card:hover .cb-culture-image img{transform:scale(1.08)}.cb-culture-card b{display:block;padding:.65rem .8rem .1rem;font-family:"Noto Sans Tamil",Inter,sans-serif;color:#4a3328}.cb-culture-card span{display:block;padding:0 .8rem .85rem;color:#78675e;font-size:.72rem}
.cb-action-card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:1rem;min-height:105px;box-shadow:0 7px 22px rgba(26,63,105,.05)}.cb-action-card b{display:block;color:#4a3328}.cb-action-card span{display:block;color:#78675e;font-size:.78rem;line-height:1.55;margin:.35rem 0 .7rem}
/* answer */
.cb-card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:1rem 1.2rem;margin-bottom:.8rem;box-shadow:0 7px 24px rgba(26,63,105,.05)}.cb-card-title{font-size:.72rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#6f4d7f;margin:.7rem 0 .55rem}.cb-answer{background:#fff;border:1px solid #cfe0f2;border-left:4px solid #2d74d6;border-radius:15px;padding:1.2rem 1.35rem;font-size:1rem;line-height:1.85;box-shadow:0 8px 25px rgba(92,65,52,.07)}.cb-answer-warning{background:#fff8ed;border:1px solid #f0d5a4;border-left:4px solid #d89925;border-radius:15px;padding:1.1rem 1.3rem;line-height:1.7}.cb-pill{display:inline-block;padding:.28rem .65rem;border-radius:999px;font-size:.7rem;font-weight:700;margin:.15rem .2rem .15rem 0;background:#eef5ff;color:#6f4d7f;border:1px solid #d4e4f5}.cb-pill-green{background:#edf9f2;color:#287a4b;border-color:#cfe9da}.cb-pill-amber{background:#fff6e5;color:#9a6810;border-color:#f0d9a9}.cb-pill-grey{background:#f4f7fa;color:#6d7c8b;border-color:#e0e7ee}.cb-evidence-text{font-size:.9rem;line-height:1.75;background:#f7faff;border:1px solid #decfe5;border-radius:11px;padding:.9rem 1rem;margin-top:.55rem}.cb-meta-row{font-size:.78rem;color:#6c7d8e;margin-bottom:.2rem}
/* history right rail */
.cb-history-rail{position:sticky;top:1rem;background:#fff;border:1px solid var(--line);border-radius:16px;padding:.9rem;box-shadow:0 8px 25px rgba(92,65,52,.07);max-height:calc(100vh - 8rem);overflow:auto}.cb-history-rail h3{font:800 1rem "Noto Sans Tamil",Inter,sans-serif;color:#4a3328;margin:.1rem 0 .25rem}.cb-history-rail p{font-size:.72rem;color:#85736a}.cb-history-btn{margin-bottom:.45rem}.cb-history-item{padding:.75rem .85rem;border:1px solid var(--line);border-radius:12px;background:#fcf8fb;margin-bottom:.55rem}.cb-history-q{font-family:"Noto Sans Tamil",Inter,sans-serif;font-weight:700;color:#5a4033;font-size:.82rem}.cb-history-meta{color:#8b796f;font-size:.68rem;margin-top:.3rem}
/* trace */
.cb-trace-step{display:flex;align-items:flex-start;gap:.7rem;padding:.42rem 0}.cb-trace-dot{min-width:24px;height:24px;border-radius:50%;background:#8b6aa8;color:#fff;font-size:.68rem;font-weight:800;display:flex;align-items:center;justify-content:center}.cb-trace-dot-off{background:#b9a8a0}.cb-trace-label{font-weight:700;font-size:.84rem;color:#4a3328}.cb-trace-value{font-size:.78rem;color:#748495}.cb-side-brand{font:800 1.15rem "Noto Sans Tamil",Inter,sans-serif;color:#4a3328}.cb-side-sub{font-size:.7rem;color:#85736a;line-height:1.4;margin-bottom:1rem}.cb-status-line{font-size:.76rem;display:flex;justify-content:space-between;padding:.2rem 0;color:#78675e}.cb-divider{height:1px;background:#e2d7de;margin:1rem 0;border:none}.cb-small{font-size:.7rem;color:#85736a}
/* tamil keyboard */
.cb-keyboard{padding:.65rem;background:#f4edf7;border:1px solid #decfe5;border-radius:14px;margin:.45rem 0 .8rem}.cb-keyboard-title{font-size:.72rem;font-weight:800;color:#6f4d7f;margin-bottom:.45rem}.cb-key{font-size:.85rem!important;min-height:34px!important;padding:.1rem .25rem!important}
.cb-lang-row{display:flex;gap:.45rem;flex-wrap:wrap;margin:.5rem 0 .8rem}.cb-lang-chip{padding:.4rem .75rem;border:1px solid #cbd9e8;border-radius:999px;background:#fff;color:#42637f;font-weight:700;font-size:.75rem}.cb-lang-chip.active{background:#eaf3ff;color:#6f4d7f;border-color:#77a6d8}
@keyframes cb-bg-zoom{from{transform:scale(1.015)}to{transform:scale(1.04)}}@keyframes cb-card-in{from{opacity:0;transform:translateY(14px) scale(.985)}to{opacity:1;transform:none}}@keyframes cb-pulse{0%,100%{box-shadow:0 0 0 0 rgba(255,255,255,.12)}50%{box-shadow:0 0 0 10px rgba(255,255,255,0)}}@keyframes cb-image-float{from{transform:scale(1)}to{transform:scale(1.035)}}
@media(max-width:1000px){.cb-dashboard-grid,.cb-culture-grid{grid-template-columns:1fr 1fr}}
@media(max-width:720px){.block-container{padding:1rem .7rem 3rem}.cb-dashboard-grid,.cb-culture-grid{grid-template-columns:1fr}.cb-welcome-content{padding:2rem 1.4rem}.cb-welcome{min-height:calc(100vh - 1rem);margin:-.2rem -.7rem -2rem}.cb-auth-card-top,.cb-auth-form{padding-left:1.25rem;padding-right:1.25rem}}
/* Final Lavender + Brown theme */
:root{--lavender:#f3edf7;--lavender-deep:#e8dced;--brown:#6b4637;--brown-deep:#513326;--brown-soft:#8b6858;--violet:#8b6aa8;--violet-deep:#6f4d7f}
body,[data-testid="stAppViewContainer"]{background:linear-gradient(135deg,#fbf8fc 0%,#f3edf7 48%,#faf6f2 100%) !important}
.stApp{background:transparent !important}
[data-testid="stHeader"]{background:rgba(251,248,252,.82)!important}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#fbf8fc,#f1e7f5)!important;border-right:1px solid #dfd0e5!important}
.stButton>button{border-radius:12px!important;border:1px solid #d9c7e0!important;background:#fffdfb!important;color:#5b4034!important;box-shadow:0 5px 14px rgba(91,64,52,.07)!important;transition:transform .18s ease,box-shadow .18s ease,background .18s ease!important}
.stButton>button:hover{transform:translateY(-2px)!important;background:#f3eaf7!important;box-shadow:0 10px 22px rgba(111,77,127,.15)!important}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#6b4637,#8b6aa8)!important;color:#fff!important;border:none!important}
.stTextInput input,.stTextArea textarea,.stSelectbox div[data-baseweb="select"]>div{background:#fffdfb!important;border:1px solid #d8c9d2!important;border-radius:12px!important;color:#4a3328!important}
.cb-dashboard-hero{background:linear-gradient(135deg,#6b4637 0%,#7b5a83 55%,#8b6aa8 100%)!important}
.cb-culture-card{background:rgba(255,253,251,.95)!important;border-color:#dfd1d8!important}
.cb-culture-card:hover{border-color:#b999c5!important;box-shadow:0 18px 36px rgba(107,70,55,.14)!important}
.cb-action-card,.cb-card,.cb-history-rail{background:rgba(255,253,251,.94)!important;border-color:#dfd1d8!important}
.cb-keyboard{background:linear-gradient(145deg,#f7eff9,#fffaf6)!important;border-color:#d9c9df!important}
.cb-keyboard-title{color:#6b4637!important}
.cb-keyboard-sub{font-size:.7rem;color:#8a6c5f;margin:-.15rem 0 .55rem}
.cb-keyboard .stButton>button{font-family:"Noto Sans Tamil",sans-serif!important;font-size:1rem!important;background:#fffdfb!important;color:#5c4034!important;border-color:#dbcbd9!important;min-height:38px!important}
.cb-keyboard .stButton>button:hover{background:#efe3f3!important;color:#6f4d7f!important}
.cb-lang-row{color:#6b4637!important}
.cb-auth-card{box-shadow:0 24px 70px rgba(91,64,52,.16)!important;border-color:#e2d5dd!important}
.cb-auth-kicker{color:#8b6aa8!important}
.cb-auth-card-top h2{color:#4a3328!important}
.cb-feature{border-color:rgba(255,255,255,.25)!important}
@keyframes cb-lavender-pulse{0%,100%{box-shadow:0 0 0 0 rgba(139,106,168,.18)}50%{box-shadow:0 0 0 10px rgba(139,106,168,0)}}
.cb-culture-card{animation:cb-lavender-pulse 4.5s ease-in-out infinite}
.cb-culture-card:nth-child(2){animation-delay:.7s}.cb-culture-card:nth-child(3){animation-delay:1.4s}.cb-culture-card:nth-child(4){animation-delay:2.1s}


/* Final welcome + authentication palette */
.cb-welcome-overlay{background:linear-gradient(120deg,rgba(61,39,31,.68),rgba(111,77,127,.48),rgba(243,237,247,.20))!important}
.cb-welcome-content{background:rgba(82,58,47,.42)!important;border-color:rgba(255,244,250,.30)!important;box-shadow:0 28px 80px rgba(64,42,33,.24)!important;backdrop-filter:blur(12px)!important}
.cb-brand-mark{background:rgba(243,237,247,.18)!important;border-color:rgba(255,255,255,.28)!important}
.cb-auth-center{background:radial-gradient(circle at 20% 20%,rgba(139,106,168,.14),transparent 35%),linear-gradient(135deg,#fbf8fc,#f1e7f5 55%,#faf6f2)!important}
.cb-auth-card{background:rgba(255,253,251,.97)!important}
.cb-auth-card-top .cb-brand-line{color:#4a3328!important}
.cb-auth-card-top .cb-brand-mark{background:#f3eaf7!important;border-color:#d8c5df!important;color:#6f4d7f!important}
.cb-auth-form .stTabs [data-baseweb="tab-highlight"]{background:#8b6aa8!important}
.cb-auth-form .stTabs [data-baseweb="tab"]{color:#6b4637!important}
.cb-auth-form [data-testid="stRadio"] label{color:#5b4034!important}
.cb-auth-form .stButton>button[kind="primary"]{background:linear-gradient(135deg,#6b4637,#8b6aa8)!important}
.cb-enter-orb{background:linear-gradient(135deg,#6b4637,#8b6aa8)!important}

/* CODE BLOOM 2.0 — interactive glass/lavender/brown experience */
.cb-header{display:flex;gap:14px;align-items:center;padding:1rem 1.15rem;margin-bottom:1rem;border:1px solid #dfd1d8;border-radius:22px;background:rgba(255,253,251,.72);backdrop-filter:blur(14px);box-shadow:0 12px 30px rgba(91,64,52,.07);position:relative;overflow:hidden}
.cb-header:after{content:"";position:absolute;width:180px;height:180px;right:-60px;top:-100px;background:radial-gradient(circle,rgba(139,106,168,.20),transparent 65%);animation:cb-orbit 7s linear infinite}
.cb-header h1{font-size:1.35rem!important;margin:0!important;color:#4a3328!important}.cb-header p{margin:.18rem 0;color:#8a6c5f;font-size:.8rem}.cb-header-compact{margin-bottom:.65rem}.cb-header-orb{width:46px;height:46px;min-width:46px;border-radius:15px;display:grid;place-items:center;color:#fff;font-size:1.25rem;background:linear-gradient(135deg,#6b4637,#8b6aa8);box-shadow:0 8px 22px rgba(111,77,127,.22);animation:cb-float 3.8s ease-in-out infinite}
.cb-dashboard-hero{position:relative;overflow:hidden!important;border-radius:28px!important;box-shadow:0 20px 45px rgba(91,64,52,.16)!important}.cb-dashboard-hero:before{content:"✦  ·  ✧  ·  ✦";position:absolute;right:7%;top:18%;font-size:2rem;letter-spacing:16px;opacity:.28;animation:cb-sparkle 4s ease-in-out infinite}
.cb-dashboard-grid{gap:14px}.cb-stat-card{position:relative;overflow:hidden;transition:transform .22s ease,box-shadow .22s ease!important}.cb-stat-card:before{content:"";position:absolute;inset:-40%;background:linear-gradient(110deg,transparent 35%,rgba(255,255,255,.38),transparent 65%);transform:translateX(-55%) rotate(10deg);transition:transform .65s ease}.cb-stat-card:hover{transform:translateY(-6px) scale(1.01)!important;box-shadow:0 20px 36px rgba(107,70,55,.14)!important}.cb-stat-card:hover:before{transform:translateX(55%) rotate(10deg)}
.cb-culture-card{position:relative;overflow:hidden!important;transition:transform .25s ease,box-shadow .25s ease!important}.cb-culture-card:after{content:"✦";position:absolute;right:10px;top:8px;color:#8b6aa8;opacity:0;transform:scale(.4) rotate(-20deg);transition:.25s}.cb-culture-card:hover{transform:translateY(-7px) rotate(-.5deg)!important}.cb-culture-card:hover:after{opacity:1;transform:scale(1) rotate(0)}
.cb-action-card{position:relative;overflow:hidden;transition:.22s ease}.cb-action-card:hover{transform:translateY(-4px);box-shadow:0 16px 30px rgba(91,64,52,.12)}.cb-action-card:before{content:"";position:absolute;left:-60px;top:-60px;width:120px;height:120px;border-radius:50%;background:rgba(139,106,168,.08);transition:.3s}.cb-action-card:hover:before{transform:scale(2)}
.stButton>button{position:relative;overflow:hidden!important}.stButton>button:after{content:"";position:absolute;width:8px;height:8px;border-radius:50%;background:rgba(139,106,168,.5);left:50%;top:50%;transform:translate(-50%,-50%) scale(0);transition:.35s;pointer-events:none}.stButton>button:active:after{transform:translate(-50%,-50%) scale(16);opacity:0}
.stButton>button:hover{letter-spacing:.01em}
@keyframes cb-float{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}@keyframes cb-sparkle{0%,100%{opacity:.18;transform:translateY(0)}50%{opacity:.48;transform:translateY(-8px)}}@keyframes cb-orbit{to{transform:rotate(360deg)}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}}
</style>
"""


def inject_styles() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def cict_image_data_uri() -> str:
    root = Path(__file__).resolve().parents[1]
    return _image_data_uri(root / "assets" / "cict.jpg")


