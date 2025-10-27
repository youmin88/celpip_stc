# -*- coding: utf-8 -*-
import json, os

base_dir = os.path.dirname(__file__) or "."
data_file = os.path.join(base_dir, "data.json")
out_file  = os.path.join(base_dir, "trainer.html")

with open(data_file, "r", encoding="utf-8") as f:
    items = json.load(f)

# Write HTML with raw JSON in a <script type="application/json"> tag
with open(out_file, "w", encoding="utf-8") as f:
    f.write("""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sentence Trainer — Single Page</title>
  <style>
    :root { --gap: 10px; }
    * { box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; margin: 0; line-height: 1.5; }
    header, main { max-width: 900px; margin: 0 auto; padding: 16px; }
    header h1 { font-size: 1.4rem; margin: 0 0 8px; }
    header {  position: sticky;  top: 0;  z-index: 1000;  background: #fff;  border-bottom: 1px solid #e5e5e5; }
    .controls { display: flex; flex-wrap: wrap; gap: var(--gap); align-items: center; }
    .controls label { display: flex; align-items: center; gap: 8px; }
    input[type=number] { width: 90px; padding: 6px 8px; }
    button { padding: 8px 12px; border: 1px solid #bbb; border-radius: 8px; background: #f7f7f7; }
    button:active { transform: translateY(1px); }
    .item { border: 1px solid #e3e3e3; border-radius: 12px; padding: 14px; margin-top: 12px; }
    .ko { color: #222; margin-bottom: 6px; }
    .sample, .answer { padding: 10px; background: #fafafa; border-radius: 8px; }
    .answer { margin-top: 6px; color: #666; font-size: .95rem; }
    .inputs input { display: inline-block; width: min(180px, 40vw); padding: 6px 8px; margin: 0 4px; }
    .meta { margin-top: 8px; font-size: .85rem; color: #666; }
    .ok { color: #0a8; font-weight: 600; }
    .bad { color: #c33; font-weight: 600; }
    @media (prefers-color-scheme: dark) {
      body { background: #0b0b0b; color: #eaeaea; }
      .item { border-color: #333; }
      .sample, .answer { background: #161616; }
      button { background: #222; color: #eee; border-color: #444; }
      .ko { color: #ddd; }
      .ok { color: #4cd964; }
      .bad { color: #ff453a; }
    }
  </style>
</head>
<body>
  <header>
    <h1>영/한 문장 트레이너 (한 페이지)</h1>
    <div class="controls">
      <label>Blank 개수:
        <input id="blankCount" type="number" min="0" max="20" step="1" value="3">
      </label>
      <button id="applyBtn">적용</button>
      <button id="revealBtn">정답 보기/숨기기</button>
      <span id="status" class="meta"></span>
    </div>
  </header>
  <main id="root"></main>

  <!-- Embed raw JSON safely: -->
  <script id="DATA" type="application/json">""")
    f.write(json.dumps(items, ensure_ascii=False, indent=2))
    f.write("""</script>

  <script>
    // Read JSON from the <script> tag
    const raw = document.getElementById("DATA").textContent;
    let DATA = [];
    try {
      DATA = JSON.parse(raw);
    } catch (e) {
      alert("데이터를 불러오는 중 오류가 발생했습니다: " + e.message);
      DATA = [];
    }

    const STOP = new Set([
      "i","me","my","myself","we","our","ours","ourselves",
      "you","your","yours","yourself","yourselves",
      "he","him","his","himself","she","her","hers","herself","it","its","itself",
      "they","them","their","theirs","themselves",
      "what","which","who","whom","this","that","these","those",
      "am","is","are","was","were","be","been","being",
      "have","has","had","having","do","does","did","doing",
      "a","an","the","and","but","if","or","because","as","until","while",
      "of","at","by","for","with","about","against","between","into","through",
      "during","before","after","above","below","to","from","up","down","in","out",
      "on","off","over","under","again","further","then","once","here","there",
      "when","where","why","how","all","any","both","each","few","more","most","other",
      "some","such","no","nor","not","only","own","same","so","than","too","very",
      "can","will","just","don","should","now","would","could","must","might","shall"
    ]);

    function tokenize(s) {
      const raw = s.split(/(\s+)/);
      function normalize(w) {
        return (w || "")
          .toLowerCase()
          .replace(/^[^a-z']+|[^a-z']+$/g, "");
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

    function overlapCandidates(enSample, en) {
      const tS = tokenize(enSample || "");
      const tE = tokenize(String(en || "").replace(/~+/g, "").trim());

      const sWords = tS.words.map(w => w.norm);
      const eWords = tE.words.map(w => w.norm);

      const eSet = new Set(eWords.filter(Boolean));
      let candidates = [];
      for (let i=0;i<sWords.length;i++) {
        const w = sWords[i];
        if (!w) continue;
        if (eSet.has(w)) {
          candidates.push(i);
        }
      }
      const content = candidates.filter(i => !STOP.has(sWords[i]));
      const functionals = candidates.filter(i => STOP.has(sWords[i]));
      return {tS, sWords, content, functionals};
    }

    const root = document.getElementById("root");
    const statusEl = document.getElementById("status");
    let reveal = false;

    function build(blankN) {
      root.innerHTML = "";
      DATA.forEach((item) => {
        const block = document.createElement("section");
        block.className = "item";

        const ko = document.createElement("div");
        ko.className = "ko";
        ko.textContent = item.ko || "";
        block.appendChild(ko);

        const {tS, sWords, content, functionals} = overlapCandidates(item.en || "", item.en_sample || "");
        const chosenIdx = content.slice(0, blankN).concat(functionals.slice(0, Math.max(0, blankN - content.length)));

        const sample = document.createElement("div");
        sample.className = "sample inputs";

        const wiToExpected = new Map();
        chosenIdx.forEach(wi => wiToExpected.set(wi, tS.words[wi]?.raw || ""));

        const inputs = [];

        for (let i=0; i<tS.raw.length; i++) {
          const tok = tS.raw[i];
          if (tS.map[i] === -1) {
            sample.append(tok);
            continue;
          }
          const wi = tS.map[i];
          const expectedRaw = wiToExpected.get(wi);
          if (expectedRaw) {
            const inp = document.createElement("input");
            inp.setAttribute("type", "text");
            inp.setAttribute("data-ans", (tS.words[wi]?.norm || ""));
            inp.setAttribute("placeholder", "");
            inp.addEventListener("input", () => {
              const ok = inp.value.trim().toLowerCase() === (tS.words[wi]?.norm || "");
              inp.style.borderColor = ok ? "#0a8" : "#c33";
              inp.style.background = ok ? "rgba(10,136,120,.06)" : "";
              calcStatus();
            });
            inputs.push(inp);
            sample.appendChild(inp);
          } else {
            sample.append(tok);
          }
        }

        block.appendChild(sample);

        const ans = document.createElement("div");
        ans.className = "answer";
        ans.style.display = reveal ? "block" : "none";
        const answers = chosenIdx.map(i => tS.words[i]?.raw || "");
        ans.innerHTML = "<strong>정답:</strong> " + answers.join(", ");
        block.appendChild(ans);

        const meta = document.createElement("div");
        meta.className = "meta";
        block.appendChild(meta);

        function calcStatus() {
          const correct = inputs.filter(inp => inp.value.trim().toLowerCase() === inp.dataset.ans).length;
          meta.innerHTML = "맞은 개수: <strong>" + correct + "</strong> / " + inputs.length;
        }
        calcStatus();

        root.appendChild(block);
      });

      function calcGlobal() {
        const allInputs = Array.from(root.querySelectorAll("input[type=text]"));
        const correct = allInputs.filter(inp => inp.value.trim().toLowerCase() === inp.dataset.ans).length;
        statusEl.textContent = "전체 정답: " + correct + " / " + allInputs.length;
      }
      calcGlobal();
      root.addEventListener("input", calcGlobal);
    }

    const blankCount = document.getElementById("blankCount");
    const applyBtn = document.getElementById("applyBtn");
    const revBtn = document.getElementById("revealBtn");

    applyBtn.addEventListener("click", () => {
      let n = parseInt(blankCount.value || "0", 10);
      if (isNaN(n) || n < 0) n = 0;
      if (n > 20) n = 20;
      build(n);
    });

    revBtn.addEventListener("click", () => {
      reveal = !reveal;
      document.querySelectorAll(".answer").forEach(el => {
        el.style.display = reveal ? "block" : "none";
      });
    });

    // Build initially with default N
    (function() {
      let n = parseInt(blankCount.value || "3", 10);
      if (isNaN(n) || n < 0) n = 0;
      if (n > 20) n = 20;
      build(n);
    })();
  </script>
</body>
</html>""")
print("Wrote:", out_file)
