%%writefile app.py
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="적정주가 계산기", layout="centered")

st.title("📗 적정주가 계산기")
st.caption("책의 두 가지 방법으로 공정한 가격 범위를 계산합니다")

# ══════════════════════════════════════════════
# 계산부 — 순수 계산기 (데이터 출처와 무관)
# ══════════════════════════════════════════════

def 배수법_적정범위(eps, 보수배수, 프리미엄배수):
    return round(eps * 보수배수, 2), round(eps * 프리미엄배수, 2)

def 현금흐름법_주당가치(시작매출, 성장률, 년수, 마진율, 할인율, 주식수):
    """갈래 B: 터미널배수 = 0.9 ÷ 할인율"""
    터미널배수 = 0.9 / 할인율
    합계 = 0
    매출 = 시작매출
    for t in range(1, 년수 + 1):
        매출 = 시작매출 * (1 + 성장률) ** (t - 1)
        합계 += (매출 * 마진율) / (1 + 할인율) ** t
    합계 += (매출 * 마진율 * 터미널배수) / (1 + 할인율) ** 년수
    return round(합계 / 주식수, 2)

업계배수표 = {
    "Semiconductors":                 (25, 35),
    "Software - Application":         (28, 40),
    "Software - Infrastructure":      (28, 40),
    "Consumer Electronics":           (20, 30),
    "Internet Retail":                (25, 40),
    "Internet Content & Information": (20, 30),
    "Banks - Diversified":            (9, 13),
    "Drug Manufacturers - General":   (14, 20),
    "Beverages - Non-Alcoholic":      (18, 25),
    "Auto Manufacturers":             (10, 20),
}
기본배수 = (15, 25)

def 업계배수(업종명, 예상eps사용=False):
    보수, 프리미엄 = 업계배수표.get(업종명, 기본배수)
    if 예상eps사용:
        보수, 프리미엄 = round(보수 * 0.8), round(프리미엄 * 0.8)
    return 보수, 프리미엄

# ══════════════════════════════════════════════
# 게이지
# ══════════════════════════════════════════════

def 게이지그리기(하한, 상한, 현재가):
    좌끝 = min(하한, 현재가) * 0.85
    우끝 = max(상한, 현재가) * 1.15
    def 위치(x):
        return (x - 좌끝) / (우끝 - 좌끝) * 100
    p하, p상, p현 = 위치(하한), 위치(상한), 위치(현재가)
    html = f"""
    <div style="position:relative; height:95px; margin:6px 0 0 0;">
      <div style="position:absolute; top:0; left:{p현}%; transform:translateX(-50%);
                  font-size:14px; font-weight:bold; color:#d32f2f; white-space:nowrap;">
        현재가 ${현재가:,.2f}</div>
      <div style="position:absolute; top:22px; left:{p현}%; transform:translateX(-50%);
                  width:4px; height:34px; background:#d32f2f; border-radius:2px;"></div>
      <div style="position:absolute; top:32px; left:0; right:0; height:16px;
                  background:#e0e0e0; border-radius:8px;"></div>
      <div style="position:absolute; top:32px; left:{p하}%; width:{p상-p하}%; height:16px;
                  background:#66bb6a; border-radius:8px;"></div>
      <div style="position:absolute; top:56px; left:{p하}%; transform:translateX(-50%);
                  font-size:13px; color:#2e7d32;">${하한:,.0f}</div>
      <div style="position:absolute; top:56px; left:{p상}%; transform:translateX(-50%);
                  font-size:13px; color:#2e7d32;">${상한:,.0f}</div>
      <div style="position:absolute; top:74px; left:{(p하)/2}%; transform:translateX(-50%);
                  font-size:12px; color:#888;">싼 편</div>
      <div style="position:absolute; top:74px; left:{(p하+p상)/2}%; transform:translateX(-50%);
                  font-size:12px; color:#2e7d32; font-weight:bold;">적정</div>
      <div style="position:absolute; top:74px; left:{(p상+100)/2}%; transform:translateX(-50%);
                  font-size:12px; color:#888;">비싼 편</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def 위치문장(하한, 상한, 현재가):
    if 현재가 < 하한:
        st.write(f"현재가 ${현재가:,.2f}는 범위보다 **아래** — 싼 편입니다")
    elif 현재가 > 상한:
        st.write(f"현재가 ${현재가:,.2f}는 범위보다 **위** — 비싼 편입니다")
    else:
        st.write(f"현재가 ${현재가:,.2f}는 범위 **안** — 비싸게 사는 것은 아닙니다")

# ══════════════════════════════════════════════
# 용어 서랍 (이번 신설)
# ══════════════════════════════════════════════

def 용어서랍_배수법():
    with st.expander("📖 용어가 어려울 때 여세요"):
        st.markdown("""
**티커** — 주식의 짧은 이름표. 엔비디아는 NVDA, 애플은 AAPL. 미국 시장의 주민번호 같은 것.

**EPS (주당순이익)** — 회사가 1년간 번 순이익을 주식 수로 나눈 것. "주식 1장이 1년에 벌어온 돈."
이게 클수록 주식 1장의 밥벌이가 좋은 회사.

**TTM (최근 4분기)** — Trailing Twelve Months. "가장 최근 1년치"라는 뜻.
실적 EPS 옆에 붙으면 '지난 1년 실제로 번 돈'이라는 표시.

**PER / 배수** — "1년 버는 돈의 몇 배 값을 쳐줄까." 배수 30이면 '30년치 이익만큼의 값'.
이익이 빠르게 크는 회사는 높은 배수를 줘도 정당 — 내년 이익이 커지면 배수가 저절로 내려오니까.
""")

def 용어서랍_현금흐름법():
    with st.expander("📖 용어가 어려울 때 여세요"):
        st.markdown("""
**마진율** — 매출 100원 중 남는 돈. 마진 60%면 100원 팔아 60원이 남는 장사.

**할인율** — "내년의 100만원을 지금 돈으로 치면 얼마인가"의 이자율.
할인율 10%면 내년 100만원은 지금 약 91만원 값. 높게 잡을수록 미래 돈을 짜게 쳐주는 것이라
적정주가가 내려갑니다. 이 계산법의 결과를 가장 크게 흔드는 손잡이입니다.

**매출 성장률** — 매출이 해마다 몇 %씩 커진다고 볼 것인가. 낙관하면 높게, 조심하면 낮게.

**전망 기간** — 몇 년 앞까지 내다보고 계산할 것인가. 책은 5~6년을 씁니다.
""")

# ══════════════════════════════════════════════
# 데이터부 — 야후 (방어 1겹: 하루 캐시)
# ══════════════════════════════════════════════

@st.cache_data(ttl=86400)
def 데이터가져오기(티커):
    info = yf.Ticker(티커).info
    return {
        "회사명":   info.get("longName"),
        "현재가":   info.get("currentPrice"),
        "실적EPS":  info.get("trailingEps"),
        "예상EPS":  info.get("forwardEps"),
        "매출":     info.get("totalRevenue"),
        "영업마진": info.get("operatingMargins"),
        "업종":     info.get("industry"),
        "주식수":   info.get("sharesOutstanding"),
    }

# ══════════════════════════════════════════════
# 화면부
# ══════════════════════════════════════════════

티커 = st.text_input("티커를 입력하세요 (예: NVDA, AAPL)", value="").strip().upper()

if st.button("조회") and 티커:
    try:
        with st.spinner("숫자를 불러오는 중..."):
            d = 데이터가져오기(티커)
        if d["현재가"] is None:
            st.error("이 티커를 찾지 못했습니다. 철자를 확인해 주세요.")
        else:
            st.session_state["데이터"] = d
    except Exception:
        st.error("데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.")

if "데이터" in st.session_state:
    d = st.session_state["데이터"]
    st.subheader(f"🏢 {d['회사명']}")
    왼, 오 = st.columns(2)
    왼.metric("현재가", f"${d['현재가']:,.2f}")
    오.metric("업종", d["업종"] or "정보 없음")
    왼.metric("실적 EPS (최근 4분기)", f"${d['실적EPS']:.2f}" if d['실적EPS'] else "정보 없음")
    오.metric("예상 EPS (애널리스트)", f"${d['예상EPS']:.2f}" if d['예상EPS'] else "정보 없음")
    왼.metric("매출 (TTM)", f"{d['매출']/1e8:,.0f}억 달러" if d['매출'] else "정보 없음")
    오.metric("영업마진", f"{d['영업마진']*100:.1f}%" if d['영업마진'] else "정보 없음")

탭1, 탭2 = st.tabs(["① 배수법 (PER)", "② 현금흐름법 (DCF)"])

# ── 탭① 배수법 ──
with 탭1:
    용어서랍_배수법()
    if "데이터" not in st.session_state:
        st.info("먼저 위에서 티커를 조회하세요")
    else:
        d = st.session_state["데이터"]
        eps선택 = st.radio("어느 이익으로 계산할까요?",
                          ["실적 EPS (최근 4분기에 실제로 번 돈)",
                           "예상 EPS (애널리스트가 전망한 내년 이익)"])
        예상사용 = eps선택.startswith("예상")
        eps = d["예상EPS"] if 예상사용 else d["실적EPS"]

        if eps is None:
            st.warning("이 종목은 해당 EPS 정보가 없습니다. 다른 쪽을 선택해 보세요.")
        else:
            if 예상사용:
                st.caption("💡 예상 이익에는 이미 '내년의 성장'이 들어 있어요. "
                           "그래서 배수는 보수적으로 — 기본값을 자동으로 낮춰 두었습니다.")
            기본보수, 기본프리미엄 = 업계배수(d["업종"], 예상사용)
            보수 = st.slider("보수 배수 (조심스러운 눈)", 5, 60, 기본보수)
            프리미엄 = st.slider("프리미엄 배수 (낙관적인 눈)", 5, 60, 기본프리미엄)

            if 보수 > 프리미엄:
                st.warning("보수 배수가 프리미엄 배수보다 큽니다. 슬라이더를 확인해 주세요.")
            else:
                하한, 상한 = 배수법_적정범위(eps, 보수, 프리미엄)
                st.success(f"**적정 범위: ${하한:,.2f} ~ ${상한:,.2f}**")
                게이지그리기(하한, 상한, d["현재가"])
                위치문장(하한, 상한, d["현재가"])
                st.caption("📌 적정주가는 점이 아니라 범위입니다. 가정 하나에 숫자가 출렁이니, "
                           "범위 안이면 '비싸게 사는 건 아니다' 정도로 쓰세요.")

# ── 탭② 현금흐름법 ──
with 탭2:
    용어서랍_현금흐름법()
    if "데이터" not in st.session_state:
        st.info("먼저 위에서 티커를 조회하세요")
    else:
        d = st.session_state["데이터"]
        if not d["매출"] or not d["주식수"]:
            st.warning("이 종목은 매출 또는 주식 수 정보가 없어 현금흐름법을 쓸 수 없습니다.")
        else:
            st.caption("미래에 벌 현금을 예상해 '지금 값'으로 깎아 더하는 방법입니다. "
                       "슬라이더의 가정에 따라 결과가 크게 움직입니다.")
            기본마진 = round(d["영업마진"] * 100) if d["영업마진"] else 30
            성장률 = st.slider("매출 성장률 (연 %)", 0, 60, 20)
            마진   = st.slider("마진율 (%)", 5, 90, 기본마진)
            할인율 = st.slider("할인율 (%) — 미래 돈을 깎는 이자율", 7, 13, 10)
            년수   = st.slider("전망 기간 (년)", 5, 6, 5)

            보수치 = 현금흐름법_주당가치(d["매출"], max(성장률-5, 0)/100, 년수, 마진/100, 할인율/100, d["주식수"])
            낙관치 = 현금흐름법_주당가치(d["매출"], (성장률+5)/100,       년수, 마진/100, 할인율/100, d["주식수"])

            st.success(f"**적정 범위: ${보수치:,.2f} ~ ${낙관치:,.2f}**")
            st.caption(f"보수 시나리오는 성장률 {max(성장률-5,0)}%, 낙관은 {성장률+5}%로 자동 계산했습니다.")
            게이지그리기(보수치, 낙관치, d["현재가"])
            위치문장(보수치, 낙관치, d["현재가"])
            st.warning("⚠️ 할인율 1%포인트에 결과가 20~30달러씩 움직입니다. "
                       "이 방법은 '정답'이 아니라 '가정을 바꿔보는 실험 도구'입니다.")

st.divider()
st.caption("⚠️ 이 앱은 계산 도구이며 매수 추천이 아닙니다")
