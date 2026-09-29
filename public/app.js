(function(){
  var CFG = JSON.parse(document.getElementById('cfg').textContent);

  // Copy an article + its link
  document.querySelectorAll('.cod li').forEach(function(li){
    var btn = li.querySelector('.copy');
    btn.addEventListener('click', function(){
      var text = li.querySelector('.art').textContent + ' ' + li.querySelector('.txt').textContent + '\n' + location.origin + location.pathname + '#' + li.id;
      var lbl = btn.querySelector('.lbl'), status = document.querySelector('[data-copy-status]');
      function done(){ lbl.textContent = CFG.copied; btn.setAttribute('data-done','1'); if (status) status.textContent = CFG.copied;
        setTimeout(function(){ lbl.textContent = CFG.copy; btn.removeAttribute('data-done'); if (status) status.textContent = ''; }, 1600); }
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, done);
      else done();
    });
  });

  // Excuse generator: reads the full list rendered in the page
  var excuses = Array.prototype.map.call(document.querySelectorAll('[data-excuses] li'), function(li){ return li.innerHTML; });
  var excuseEl = document.querySelector('[data-excuse]'), idx = 0;
  var excuseBtn = document.querySelector('[data-excuse-btn]');
  if (excuseBtn && excuses.length > 1) excuseBtn.addEventListener('click', function(){
    var next = idx;
    while (next === idx) next = Math.floor(Math.random() * excuses.length);
    idx = next; excuseEl.innerHTML = excuses[idx];
  });

  // Standup bingo (nothing is stored)
  var grid = document.querySelector('.bingo');
  var cells = Array.prototype.slice.call(document.querySelectorAll('.bingo button'));
  var winEl = document.querySelector('[data-bingo-win]');
  var LINES = [];
  for (var r = 0; r < 4; r++) { LINES.push([r*4, r*4+1, r*4+2, r*4+3]); LINES.push([r, r+4, r+8, r+12]); }
  LINES.push([0, 5, 10, 15]); LINES.push([3, 6, 9, 12]);
  function checkBingo(){
    var on = cells.map(function(c){ return c.getAttribute('aria-pressed') === 'true'; });
    winEl.textContent = LINES.some(function(l){ return l.every(function(i){ return on[i]; }); }) ? CFG.win : '';
  }
  cells.forEach(function(c){
    c.addEventListener('click', function(){
      c.setAttribute('aria-pressed', c.getAttribute('aria-pressed') === 'true' ? 'false' : 'true');
      checkBingo();
    });
  });
  var reset = document.querySelector('[data-bingo-reset]');
  if (reset) reset.addEventListener('click', function(){
    for (var i = cells.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var tmp = cells[i]; cells[i] = cells[j]; cells[j] = tmp; }
    cells.forEach(function(c){ c.setAttribute('aria-pressed', 'false'); grid.appendChild(c); });
    checkBingo();
  });
})();
