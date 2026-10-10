(function () {
  'use strict';

  function processScoreBadges() {
    var scoreRe = /⭐️\s*(\d+(?:\.\d+)?)\/10/;
    document.querySelectorAll('.main-content h2, .main-content h3, .main-content li').forEach(function (el) {
      var match = el.innerHTML.match(scoreRe);
      if (!match || el.querySelector('.score-badge')) return;
      var score = parseFloat(match[1]);
      var tier = score >= 9 ? 'high' : score >= 7 ? 'good' : score >= 5 ? 'mid' : 'low';
      el.innerHTML = el.innerHTML.replace(scoreRe, '<span class="score-badge" data-tier="' + tier + '">' + match[1] + '</span>');
    });
  }

  function markSemanticElements() {
    document.querySelectorAll('.main-content p').forEach(function (p) {
      var value = p.textContent.trim();
      if (/^(Tags|标签|Tags \/ 标签)\s*:/.test(value)) p.classList.add('tag-line');
      if (/^(rss|reddit|github|hackernews|hn|telegram|google_news|ossinsight)\s*·/i.test(value)) p.classList.add('source-line');
    });
  }

  function setupLanguageToggle() {
    var toggle = document.createElement('div');
    toggle.className = 'lang-toggle';
    var options = [
      { id: 'bilingual', label: '双语' },
      { id: 'en', label: 'EN' },
      { id: 'zh', label: '中文' }
    ];
    var buttons = {};
    options.forEach(function (option) {
      var button = document.createElement('button');
      button.type = 'button';
      button.textContent = option.label;
      button.dataset.lang = option.id;
      buttons[option.id] = button;
      toggle.appendChild(button);
    });
    document.body.insertBefore(toggle, document.body.firstChild);

    var saved = null;
    try { saved = localStorage.getItem('horizon-lang'); } catch (e) { /* private mode */ }
    var current = saved === 'en' || saved === 'zh' || saved === 'bilingual' ? saved : 'bilingual';
    var hasPairs = document.querySelector('.bilingual-en, .bilingual-zh');
    var zhSection = document.getElementById('lang-zh');
    var enSection = document.getElementById('lang-en');

    function update(lang) {
      current = lang;
      Object.keys(buttons).forEach(function (key) { buttons[key].classList.toggle('active', key === lang); });
      document.body.dataset.language = lang;
      if (hasPairs) {
        document.querySelectorAll('.bilingual-en').forEach(function (node) { node.hidden = lang === 'zh'; });
        document.querySelectorAll('.bilingual-zh').forEach(function (node) { node.hidden = lang === 'en'; });
      }
      if (zhSection && enSection) {
        zhSection.classList.toggle('hidden', lang === 'en');
        enSection.classList.toggle('hidden', lang === 'zh');
      }
      try { localStorage.setItem('horizon-lang', lang); } catch (e) { /* private mode */ }
    }

    Object.keys(buttons).forEach(function (key) { buttons[key].addEventListener('click', function () { update(key); }); });
    update(current);
  }

  document.addEventListener('DOMContentLoaded', function () {
    processScoreBadges();
    markSemanticElements();
    setupLanguageToggle();
  });
})();
