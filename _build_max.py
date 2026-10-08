"""Собрать max.html — версию игры для MAX-бота — из index.html (Telegram-версия).

index.html НЕ меняется. В max.html: убран telegram-web-app.js и добавлен блок MAX:
в конце раздела игра показывает код результата «ИГРА <режим> <верно>/<всего> <подпись>»,
сотрудник копирует его и отправляет боту. Подпись = FNV-1a от (секрет|chat_id|…) —
та же функция game_sig() в StardogsBot/code/max_shop.py.

Запуск после любой правки index.html:  python _build_max.py
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
src = (HERE / "index.html").read_text(encoding="utf-8")

src = src.replace('<script src="https://telegram.org/js/telegram-web-app.js"></script>\n', "")

MAX_BLOCK = r"""
// ══ MAX-бот (max.html, 08.10.2026): результат — кодом, его отправляют боту ══
const MAXU = new URLSearchParams(location.search).get('max') || '';
const MAX_BOT_URL = 'https://max.ru/id9728064038_bot';
const GAME_SALT = 'stardogs-max-kolbaski-2026';   // = _GAME_SALT в max_shop.py
function maxSig(mode, c, n, intr){
  const s = GAME_SALT + '|' + MAXU + '|' + mode + '|' + c + '|' + n + '|' + (intr ? 1 : 0);
  let h = 0x811c9dc5;
  for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; }
  return h.toString(36).padStart(6, '0').slice(-6);
}
function maxShowCode(mode, c, n, intr){
  const code = 'ИГРА ' + mode + (intr ? '*' : '') + ' ' + c + '/' + n + ' ' + maxSig(mode, c, n, intr);
  let box = document.getElementById('maxCodeBox');
  if(!box){
    box = document.createElement('div'); box.id = 'maxCodeBox';
    box.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.55);display:flex;align-items:center;' +
      'justify-content:center;z-index:9999;padding:16px';
    document.body.appendChild(box);
  }
  box.innerHTML =
    '<div style="background:#fff;color:#222;border-radius:16px;max-width:420px;width:100%;padding:22px;text-align:center;' +
    'font-family:inherit;box-shadow:0 10px 40px rgba(0,0,0,.3)">' +
    '<div style="font-size:20px;font-weight:700;margin-bottom:8px">📤 Отправь результат боту</div>' +
    '<div style="color:#555;line-height:1.45;margin-bottom:14px">Скопируй код и отправь его сообщением боту ' +
    'Stardogs в MAX — он засчитает результат' + (intr ? ' (попытка была прервана)' : '') + '.</div>' +
    '<div id="maxCode" style="font:700 20px/1.3 monospace;background:#FFF4CC;border:2px dashed #FCC41A;border-radius:12px;' +
    'padding:14px 8px;margin-bottom:14px;user-select:all;word-break:break-word">' + code + '</div>' +
    '<button id="maxCopy" style="width:100%;padding:14px;border:0;border-radius:12px;background:#E41D2E;color:#fff;' +
    'font-size:17px;font-weight:700;cursor:pointer;margin-bottom:10px">📋 Скопировать код</button>' +
    '<a href="' + MAX_BOT_URL + '" style="display:block;padding:12px;border-radius:12px;background:#f2f2f2;color:#222;' +
    'text-decoration:none;font-weight:600">↩️ Вернуться в бота</a></div>';
  document.getElementById('maxCopy').onclick = function(){
    const btn = this;
    const ok = () => { btn.textContent = '✅ Скопировано — вставь в чат с ботом'; };
    try { navigator.clipboard.writeText(code).then(ok, fallback); } catch(e){ fallback(); }
    function fallback(){
      const r = document.createRange(); r.selectNodeContents(document.getElementById('maxCode'));
      const sel = getSelection(); sel.removeAllRanges(); sel.addRange(r);
      try { document.execCommand('copy'); ok(); } catch(e){ btn.textContent = 'Выдели код и скопируй вручную'; }
    }
  };
}
if(MAXU){
  // конец раздела → код вместо отправки в Telegram; переиграть нельзя
  tgOffer = function(correct, total, pct, mode){
    const again = document.getElementById('playAgain'); if(again) again.style.display = 'none';
    attDel(mode);
    maxShowCode(mode, correct, total, false);
  };
  tgSend = function(mode, correct, total, label){
    attDel(mode);
    maxShowCode(mode, correct, total, true);
  };
  // брошенная попытка: отмечаем в localStorage, при новом входе — только отправить набранное
  attLoad(found => {
    Object.keys(found).forEach(m => {
      const v = found[m];
      if(m in LOCKED || !MODE_LABEL[m] || Date.now() - v.t > ATT_TTL){ attDel(m); return; }
      PENDING[m] = v;
      const el = [...document.querySelectorAll('.mode')].find(x => (x.getAttribute('onclick') || '').indexOf("'" + m + "'") >= 0);
      if(el) el.insertAdjacentHTML('beforeend',
        '<p style="margin-top:6px;color:var(--red);font-weight:600">⏸ Попытка прервана: верно ' + (v.c || 0) + ' из ' + v.n +
        '. Нажми — получишь код для бота</p>');
    });
  });
  const _startM = start;
  start = function(mode){
    const fresh = !(mode in PENDING) && !(mode in LOCKED);
    _startM(mode);
    if(fresh) attSet(mode, {t: Date.now(), c: 0, i: 0, n: state.order.length});
  };
  const _answerM = answer;
  answer = function(chosen, btn){
    const was = state.answered;
    _answerM(chosen, btn);
    if(!was) attSet(state.mode, {t: Date.now(), c: state.correct, i: state.i + 1, n: state.order.length});
  };
}
"""

marker = "\n</script>\n</body></html>"
assert marker in src, "не нашёл конец скрипта в index.html"
out = src.replace(marker, MAX_BLOCK + marker, 1)
(HERE / "max.html").write_text(out, encoding="utf-8")
print("max.html собран:", len(out), "байт")
