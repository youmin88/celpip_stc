# -*- coding: utf-8 -*-
import json, os

base_dir = os.path.dirname(__file__) or "."
data_file = os.path.join(base_dir, "data.json")
out_file  = os.path.join(base_dir, "trainer3.html")

with open(data_file, "r", encoding="utf-8") as f:
    items = json.load(f)

with open(out_file, "w", encoding="utf-8") as f:
    f.write("""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sentence Trainer — Chunk Inputs for OVERLAP</title>
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
    input.answer { display: inline-block; width: min(320px, 60vw); padding: 4px 6px; margin: 0 2px; border-radius: 6px; border: 1px solid #bbb; }
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
    <h1>영/한 문장 — 겹치는 청크(고정 구간) 입력</h1>
    <div class="controls">
      <button id="toggleBtn">정답 보기/숨기기</button>
      <span class="status" id="globalStatus">전체 정답: 0 / 0</span>
    </div>
    <p class="legend">
      규칙: <code>en</code> 템플릿의 <strong>고정 구간(= ~가 아닌 부분)</strong>을 <code>en_sample</code>에서 찾아
      그 부분을 <strong>입력칸</strong>으로 만듭니다. 즉, <em>겹치는 문장</em>이 빈칸이 됩니다.
      (입력 글자수 제한 없음, Enter로 다음 칸 이동)
    </p>
  </header>

  <main id="root"></main>

  <script id="DATA" type="application/json">""")
    f.write(json.dumps(items, ensure_ascii=False, indent=2))
    f.write("""</script>

  <script>
    // Find FIXED-part spans (overlap) of en template in enSample.
    function findOverlapFixedSpans(enSample, enTemplate) {
      const parts = String(enTemplate || "").split("~");
      const s = String(enSample || "");
      const spans = []; // fixed segments as inputs
      let pos = 0;

      function indexOfFrom(hay, needle, from) {
        if (!needle) return from;
        return hay.indexOf(needle, from);
        }

      // For each fixed part, in order, locate it and create a span for that exact substring.
      for (let i=0; i<parts.length; i++) {
        const p = parts[i];
        if (p === "") {
          // Empty fixed piece (due to leading/trailing "~" or consecutive "~~") -> skip
          continue;
        }
        const idx = indexOfFrom(s, p, pos);
        if (idx === -1) {
          // If any fixed part is not found, we cannot confidently align; return empty inputs
          return [];
        }
        spans.push({start: idx, end: idx + p.length, text: s.slice(idx, idx + p.length)});
        pos = idx + p.length;
      }
      return spans;
    }

    function renderMaskedLine(enSample, fixedSpans) {
      const container = document.createElement("div");
      container.className = "masked";
      let cursor = 0;
      // sort by start index
      fixedSpans.sort((a,b)=>a.start-b.start);

      for (const span of fixedSpans) {
        // append plain segment BEFORE fixed span
        if (span.start > cursor) container.append(enSample.slice(cursor, span.start));

        // input for the fixed (overlap) part
        const inp = document.createElement("input");
        inp.type = "text";
        inp.className = "answer";
        inp.setAttribute("data-ans", span.text); // compare as-is (trim 안함)
        // live check
        function check() {
          const ok = inp.value.trim() === inp.dataset.ans.trim();
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
        container.appendChild(inp);

        // advance cursor after the fixed span
        cursor = span.end;
      }

      // append remaining tail AFTER last fixed span
      if (cursor < enSample.length) container.append(enSample.slice(cursor));
      return container;
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

        const fixedSpans = findOverlapFixedSpans(item.en_sample || "", item.en || "");
        const masked = renderMaskedLine(item.en_sample || "", fixedSpans);
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
      const correct = inputs.filter(inp => inp.value === inp.dataset.ans).length;
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
