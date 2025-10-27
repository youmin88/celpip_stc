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
  <title>Sentence Trainer — Chunk Inputs (robust)</title>
  <style>
    :root { --gap: 10px; }
    * { box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; margin: 0; line-height: 1.5; }
    header, main { max-width: 900px; margin: 0 auto; padding: 16px; }
    header h1 { font-size: 1.4rem; margin: 0 0 8px; }
    header {  position: sticky;  top: 0;  z-index: 1000;  background: #fff;  border-bottom: 1px solid #e5e5e5; }
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
    .note { font-size: .85rem; color: #777; margin-top: 6px; }
    @media (prefers-color-scheme: dark) {
      body { background: #0b0b0b; color: #eaeaea; }
      .item { border-color: #333; }
      .masked, .full { background: #161616; }
      button { background: #222; color: #eee; border-color: #444; }
      .ko { color: #ddd; }
      .status { color: #aaa; }
      input.answer { border-color: #555; background: #0f0f0f; color: #eee; }
      .note { color: #aaa; }
    }
    header { position: sticky; top: 0; z-index: 1000; background: #fff; border-bottom: 1px solid #e5e5e5; }
    @media (prefers-color-scheme: dark) { header { background: #0b0b0b; border-bottom-color: #222; } }
  </style>
</head>
<body>
  <header>
    <h1>영/한 문장 — 겹치는 고정 구간(OVERLAP) 입력</h1>
    <div class="controls">
      <button id="toggleBtn">정답 보기/숨기기</button>
      <span class="status" id="globalStatus">전체 정답: 0 / 0</span>
    </div>
    <p class="note">고정 구간을 대소문자 무시로 찾아 빈칸으로 만듭니다. 못 찾으면 임시로 '~' 사이 청크 빈칸으로 대체합니다.</p>
  </header>

  <main id="root"></main>

  <script id="DATA" type="application/json">""")
    f.write(json.dumps(items, ensure_ascii=False, indent=2))
    f.write("""</script>

  <script>
    function findFixedSpansCI(enSample, enTemplate) {
      const parts = String(enTemplate || "").split("~");
      const s = String(enSample || "");
      const sL = s.toLowerCase();
      const spans = [];
      let posL = 0;
      for (let i=0;i<parts.length;i++) {
        const p = parts[i];
        if (!p) continue;
        const pL = p.toLowerCase();
        const idxL = sL.indexOf(pL, posL);
        if (idxL === -1) return [];
        spans.push({start: idxL, end: idxL + p.length, text: s.slice(idxL, idxL + p.length)});
        posL = idxL + p.length;
      }
      return spans;
    }

    function findGapChunks(enSample, enTemplate) {
      const parts = String(enTemplate || "").split("~");
      const s = String(enSample || "");
      const spans = [];
      let pos = 0;
      function indexOfFrom(hay, needle, from) {
        if (!needle) return from;
        return hay.indexOf(needle, from);
      }
      const matches = [];
      for (let i=0;i<parts.length;i++) {
        const p = parts[i];
        const idx = indexOfFrom(s, p, pos);
        if (idx === -1) return [];
        matches.push({start: idx, end: idx + p.length});
        pos = idx + p.length;
      }
      for (let i=0;i<matches.length-1;i++) {
        const left = matches[i], right = matches[i+1];
        const start = left.end, end = right.start;
        if (end >= start) spans.push({start, end, text: s.slice(start, end)});
      }
      if (parts.length > 0 && parts[0] === "") {
        const firstStart = matches[0].start;
        if (firstStart > 0) spans.unshift({start: 0, end: firstStart, text: s.slice(0, firstStart)});
      }
      if (parts.length > 0 && parts[parts.length-1] === "") {
        const lastEnd = matches[matches.length-1].end;
        if (lastEnd < s.length) spans.push({start: lastEnd, end: s.length, text: s.slice(lastEnd)});
      }
      return spans;
    }

    function renderMaskedLine(enSample, spans, noteFallback) {
      const container = document.createElement("div");
      container.className = "masked";
      let cursor = 0;
      spans.sort((a,b)=>a.start-b.start);
      for (const span of spans) {
        if (span.start > cursor) container.append(enSample.slice(cursor, span.start));
        const inp = document.createElement("input");
        inp.type = "text";
        inp.className = "answer";
        inp.setAttribute("data-ans", span.text);
        function check() {
          const ok = inp.value.trim() === inp.dataset.ans.trim();
          inp.classList.toggle("ok", ok);
          inp.classList.toggle("bad", !ok && inp.value.length > 0);
          updateGlobal();
        }
        inp.addEventListener("input", check);
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
        cursor = span.end;
      }
      if (cursor < enSample.length) container.append(enSample.slice(cursor));
      if (noteFallback) {
        const n = document.createElement("div");
        n.className = "note";
        n.textContent = "고정 구간을 찾지 못해 임시로 청크(~) 구간을 빈칸으로 대체했습니다.";
        container.appendChild(n);
      }
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

        let spans = findFixedSpansCI(item.en || "", item.en_sample || "");
        let usedFallback = false;
        if (!spans.length) {
          spans = findGapChunks(item.en_sample || "", item.en || "");
          usedFallback = true;
        }
        const masked = renderMaskedLine(item.en || "", spans, usedFallback);
        sec.appendChild(masked);

        const full = document.createElement("div");
        full.className = "full";
        full.textContent = item.en || "";
        if (reveal) full.style.display = "block";
        sec.appendChild(full);

        root.appendChild(sec);
      });
      updateGlobal();
    }

    function updateGlobal() {
      const inputs = Array.from(document.querySelectorAll("input.answer"));
      const correct = inputs.filter(inp => inp.value.trim() === inp.dataset.ans.trim()).length;
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
