# -*- coding: utf-8 -*-
import json, os

base_dir = os.path.dirname(__file__) or "."
data_file = os.path.join(base_dir, "data.json")
out_file  = os.path.join(base_dir, "trainer2.html")

with open(data_file, "r", encoding="utf-8") as f:
    items = json.load(f)

with open(out_file, "w", encoding="utf-8") as f:
    f.write("""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sentence Trainer — First letter inside input</title>
  <style>
    :root { --gap: 10px; }
    * { box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; margin: 0; line-height: 1.5; }
    header, main { max-width: 900px; margin: 0 auto; padding: 16px; }
    header h1 { font-size: 1.4rem; margin: 0 0 8px; }
    .controls { display: flex; flex-wrap: wrap; gap: var(--gap); align-items: center; }
    button { padding: 8px 12px; border: 1px solid #bbb; border-radius: 8px; background: #f7f7f7; }
    button:active { transform: translateY(1px); }
    .status { margin-left: auto; color: #666; }
    .item { border: 1px solid #e3e3e3; border-radius: 12px; padding: 14px; margin-top: 12px; }
    .ko { color: #222; margin-bottom: 6px; }
    .masked, .full { padding: 10px; background: #fafafa; border-radius: 8px; }
    .full { margin-top: 6px; color: #666; font-size: .95rem; display: none; white-space: pre-wrap; }
    .masked { white-space: pre-wrap; }
    .chunk { display: inline; }
    /* <<< You can edit width here >>> */
    input.answer { display: inline-block; width: min(150px, 48vw); padding: 4px 6px; margin: 0 2px; border-radius: 6px; border: 1px solid #bbb; }
    input.answer.ok { border-color: #0a8; background: rgba(10,136,120,.06); }
    input.answer.bad { border-color: #c33; }
    @media (prefers-color-scheme: dark) {
      body { background: #0b0b0b; color: #eaeaea; }
      .item { border-color: #333; }
      .masked, .full { background: #161616; }
      button { background: #222; color: #eee; border-color: #444; }
      .ko { color: #ddd; }
      .status { color: #aaa; }
      input.answer { border-color: #555; background: #0f0f0f; color: #eee; }
    }
    .legend { font-size: .9rem; color: #666; }
    .legend code { background: #eee; padding: 2px 6px; border-radius: 4px; }
    @media (prefers-color-scheme: dark) {
      .legend { color: #aaa; }
      .legend code { background: #222; }
    }
  </style>
</head>
<body>
  <header>
    <h1>영/한 문장 — 첫 글자 입력칸 내부 + Enter 이동</h1>
    <div class="controls">
      <button id="toggleBtn">정답 보기/숨기기</button>
      <span class="status" id="globalStatus">전체 정답: 0 / 0</span>
    </div>
    <p class="legend">대상 단어는 <strong>첫 글자가 입력칸 안에 미리 채워져</strong> 보입니다. 입력을 시작하면 그 글자는 자동으로 덮어쓰기 됩니다. 채점은 <em>첫 글자를 제외한 나머지 철자</em> 기준입니다.</p>
  </header>

  <main id="root"></main>

  <script id="DATA" type="application/json">""")
    f.write(json.dumps(items, ensure_ascii=False, indent=2))
    f.write("""</script>

  <script>
    function tokenize(s) {
      const raw = String(s || "").split(/(\\s+)/);
      function normalize(w) {
        return (w || "").toLowerCase().replace(/^[^A-Za-z']+|[^A-Za-z']+$/g, "");
      }
      const words = [];
      const map = [];
      let wi = 0;
      for (let i=0;i<raw.length;i++) {
        if (raw[i].trim().length === 0) { map.push(-1); continue; }
        map.push(wi);
        words.push({raw: raw[i], norm: normalize(raw[i])});
        wi++;
      }
      return {raw, words, map};
    }

    function splitToken(rawToken) {
      const s = String(rawToken || "");
      let firstIdx = -1, lastIdx = -1;
      for (let i=0;i<s.length;i++) { if (/[A-Za-z]/.test(s[i])) { firstIdx = i; break; } }
      for (let i=s.length-1;i>=0;i--) { if (/[A-Za-z]/.test(s[i])) { lastIdx = i; break; } }
      if (firstIdx === -1 || lastIdx === -1) return {lead: s, first: "", remainder: "", trail: ""};
      const lead = s.slice(0, firstIdx);
      const letters = s.replace(/[^A-Za-z]/g, "");
      const first = letters.slice(0,1);
      // const remainder = letters.slice(1);
      const remainder = letters;
      const trail = s.slice(lastIdx+1);
      return {lead, first, remainder, trail};
    }

    function overlappingWordIndices(enSample, en) {
      const tS = tokenize(enSample);
      const tE = tokenize(String(en || "").replace(/~+/g, "").trim());
      const eSet = new Set(tE.words.map(w => w.norm).filter(Boolean));
      const maskIdx = new Set();
      for (let i=0;i<tS.words.length;i++) {
        const w = tS.words[i].norm;
        if (w && eSet.has(w)) maskIdx.add(i);
      }
      return {tS, maskIdx};
    }

    const root = document.getElementById("root");
    const toggleBtn = document.getElementById("toggleBtn");
    const globalStatus = document.getElementById("globalStatus");
    let reveal = false;

    function renderAll(DATA) {
      root.innerHTML = "";
      DATA.forEach(item => {
        const sec = document.createElement("section");
        sec.className = "item";

        const ko = document.createElement("div");
        ko.className = "ko";
        ko.textContent = item.ko || "";
        sec.appendChild(ko);

        const masked = document.createElement("div");
        masked.className = "masked";
        const {tS, maskIdx} = overlappingWordIndices(item.en_sample || "", item.en || "");

        for (let i=0;i<tS.raw.length;i++) {
          const tok = tS.raw[i];
          if (tS.map[i] === -1) { masked.append(tok); continue; }
          const wi = tS.map[i];
          if (maskIdx.has(wi)) {
            const {lead, first, remainder, trail} = splitToken(tok);
            if (lead) masked.append(lead);

            // Input holds ONLY the remainder as the expected answer, but we prefill FIRST letter
            const inp = document.createElement("input");
            inp.type = "text";
            inp.className = "answer";
            inp.value = first || ""; // show first letter inside input
            inp.setAttribute("data-first", (first || "").toLowerCase());
            inp.setAttribute("data-ans", (remainder || "").toLowerCase());
            // if (remainder && remainder.length > 0) inp.maxLength = remainder.length; // user types remainder only

            // Auto-select on focus/click so typing overwrites the prefilled first letter
            const selectAll = () => { try { inp.select(); } catch(_){} };
            inp.addEventListener("focus", selectAll);
            inp.addEventListener("click", selectAll);

            // Check remainder only
            function check() {
              const ok = inp.value.trim().toLowerCase() === inp.dataset.ans;
              inp.classList.toggle("ok", ok);
              inp.classList.toggle("bad", !ok && inp.value.length > 0);
              updateGlobal();
            }
            inp.addEventListener("input", check);

            // Enter -> next
            inp.addEventListener("keydown", (e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                const inputs = Array.from(document.querySelectorAll("input.answer"));
                const i = inputs.indexOf(inp);
                if (i >= 0 && i < inputs.length - 1) {
                  inputs[i+1].focus();
                  inputs[i+1].select();
                }
              }
            });

            masked.appendChild(inp);
            if (trail) masked.append(trail);
          } else {
            masked.append(tok);
          }
        }
        sec.appendChild(masked);

        const full = document.createElement("div");
        full.className = "full";
        full.textContent = item.en_sample || "";
        if (reveal) full.style.display = "block";
        sec.appendChild(full);

        root.appendChild(sec);
      });

      updateGlobal();
    }

    function updateGlobal() {
      const inputs = Array.from(document.querySelectorAll("input.answer"));
      const correct = inputs.filter(inp => inp.value.trim().toLowerCase() === inp.dataset.ans).length;
      globalStatus.textContent = "전체 정답: " + correct + " / " + inputs.length;
    }

    let DATA = [];
    try {
      DATA = JSON.parse(document.getElementById("DATA").textContent);
    } catch(e) {
      alert("데이터 파싱 오류: " + e.message);
      DATA = [];
    }
    renderAll(DATA);

    toggleBtn.addEventListener("click", () => {
      reveal = !reveal;
      document.querySelectorAll(".full").forEach(el => {
        el.style.display = reveal ? "block" : "none";
      });
    });
  </script>
</body>
</html>""")
print("Wrote:", out_file)
