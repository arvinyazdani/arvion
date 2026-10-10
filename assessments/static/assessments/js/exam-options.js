(function () {
  'use strict';
  const form = document.querySelector('.os-exam-form');
  if (!form) return;
  const feedback = form.querySelector('[role=status]'), fa = document.documentElement.lang === 'fa';
  form.addEventListener('change', () => {
    const selected = form.querySelector('input[name=exam]:checked');
    form.querySelectorAll('input[name=exam]').forEach(n => n.removeAttribute('aria-invalid'));
    if (selected) feedback.textContent = selected.closest('label').querySelector('strong').textContent;
  });
  form.addEventListener('submit', event => {
    if (form.querySelector('input[name=exam]:checked')) return;
    event.preventDefault();
    feedback.textContent = fa ? 'برای ادامه، یک آزمون را انتخاب کنید یا راهنمای همان آزمون را باز کنید.' : 'Choose an assessment to continue, or open its individual briefing.';
    const first = form.querySelector('input[name=exam]');
    if (first) {first.setAttribute('aria-invalid', 'true'); first.setAttribute('aria-describedby', 'os-exam-feedback'); first.focus();}
  });
})();
